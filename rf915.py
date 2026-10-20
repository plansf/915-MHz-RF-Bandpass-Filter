"""RF915 design and measurement tools. All generated design data is SIMULATED."""
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
Z0 = 50.0
# Coilcraft Document 158: R2 + ((k*sqrt(f)+jwL) || (R1+1/jwCp)).
# Parameters are typical de-embedded vendor fits, not measured board models.
COILS = {
    1.8: (25, .033, .014, 6.50e-6),
    2.2: (25, .180, .014, 1.14e-5),
    15.: (13, .078, .066, 2.50e-5),
    16.: (3, .085, .068, 3.10e-5),
    18.: (10, .066, .064, 3.66e-5),
    22.: (2, .140, .058, 4.90e-5),
}

def db(x):
    return 20*np.log10(np.maximum(np.abs(x), 1e-15))

def series(z):
    out = np.zeros((len(z), 2, 2), complex)
    out[:, 0, 0] = out[:, 1, 1] = 1
    out[:, 0, 1] = z
    return out

def shunt(y):
    out = series(np.zeros(len(y)))
    out[:, 1, 0] = y
    return out

def line(f, length_mm, impedance=50., er_eff=3.1, loss_db_per_m=8.):
    gamma_l = (loss_db_per_m*np.log(10)/20 +
               1j*2*np.pi*f*np.sqrt(er_eff)/299792458)*length_mm/1000
    out = np.empty((len(f),2,2), complex)
    out[:,0,0] = out[:,1,1] = np.cosh(gamma_l)
    out[:,0,1] = impedance*np.sinh(gamma_l)
    out[:,1,0] = np.sinh(gamma_l)/impedance
    return out

def abcd_to_s(t, z0=Z0):
    a,b,c,d = t[:,0,0],t[:,0,1],t[:,1,0],t[:,1,1]
    den = a+b/z0+c*z0+d
    s = np.empty_like(t)
    s[:,0,0] = (a+b/z0-c*z0-d)/den
    s[:,1,0] = 2/den
    s[:,0,1] = 2*(a*d-b*c)/den
    s[:,1,1] = (-a+b/z0-c*z0+d)/den
    return s

def inductor(f, nominal_nh, scale=1., ideal=False):
    w = 2*np.pi*f
    if ideal:
        return 1j*w*nominal_nh*1e-9*scale
    r1,r2,cp,k = COILS[nominal_nh]
    za = k*np.sqrt(f)+1j*w*nominal_nh*1e-9*scale
    zb = r1+1/(1j*w*cp*1e-12)
    return r2+za*zb/(za+zb)

def capacitor(f, pf, ideal=False, esr=.08, esl_nh=.2):
    return 1/(1j*2*np.pi*f*pf*1e-12) + (0 if ideal else esr+1j*2*np.pi*f*esl_nh*1e-9)

def simulate(f, cfg, ideal=False, variation=None):
    """Series C1/L1, parallel L2/C2, series L3/C3, SMA-to-SMA estimates.

    The branch parasitics include branch trace + via return. They are assumptions,
    not extracted values. See design.json and the README.
    """
    f = np.asarray(f, float)
    if f.ndim != 1 or np.any(f <= 0):
        raise ValueError('Frequency must be a positive 1D array')
    v = variation or {}
    p = cfg['parasitics']
    def lc(ref):
        return inductor(f, cfg['components'][ref], v.get(ref,1), ideal)
    def cc(ref):
        return capacitor(f, cfg['components'][ref]+v.get(ref,0), ideal,
                         p['capacitor_esr_ohm'],p['capacitor_esl_nh'])
    w = 2*np.pi*f
    bl = 0 if ideal else 1j*w*v.get('return_nh',p['ground_return_nh'])*1e-9
    def branch(z, length):
        if ideal: return z
        t=line(f,length,p['narrow_trace_ohms'],p['narrow_trace_er_eff'])
        return (t[:,0,0]*z+t[:,0,1])/(t[:,1,0]*z+t[:,1,1])
    zp = 1/(1/branch(lc('L2')+bl,p['inductor_branch_mm'])+1/branch(cc('C2')+bl,p['capacitor_branch_mm']))
    y = 1/zp + (0 if ideal else 1j*w*p['center_pad_pf']*1e-12)
    if ideal:
        t = series(cc('C1')+lc('L1')) @ shunt(y) @ series(lc('L3')+cc('C3'))
    else:
        trace1=line(f,p['between_series_parts_mm'],p['narrow_trace_ohms'],p['narrow_trace_er_eff'])
        trace2=line(f,p['inductor_to_center_mm'],p['narrow_trace_ohms'],p['narrow_trace_er_eff'])
        left=series(cc('C1')) @ trace1 @ series(lc('L1')) @ trace2
        right=trace2 @ series(lc('L3')) @ trace1 @ series(cc('C3'))
        t=left @ shunt(y) @ right
    if not ideal:
        launch = shunt(1j*w*p['launch_pad_pf']*1e-12) @ series(1j*w*p['launch_series_nh']*1e-9)
        port = line(f,p['port_line_length_mm'],cfg['pcb']['nominal_line_ohms'])
        # Mirror the launch at port 2, maintaining reciprocal symmetry.
        taper=line(f,p['feed_neck_mm'],p['narrow_trace_ohms'],p['narrow_trace_er_eff'])
        t = launch @ port @ taper @ t @ taper @ port @ series(1j*w*p['launch_series_nh']*1e-9) @ shunt(1j*w*p['launch_pad_pf']*1e-12)
    return abcd_to_s(t)

def write_s2p(path, f, s, description):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w',encoding='ascii') as fp:
        fp.write('! '+description+'\n# Hz S RI R 50\n')
        for fi,si in zip(f,s):
            vals=[fi]
            for row,col in ((0,0),(1,0),(0,1),(1,1)):
                vals.extend([si[row,col].real,si[row,col].imag])
            fp.write(' '.join(f'{x:.12g}' for x in vals)+'\n')

def read_s2p(path):
    """Touchstone 1.x two-port, RI/MA/DB, wrapped rows, ! comments, 50 ohms.

    Deliberately rejects Touchstone 2, noise blocks, nonmonotonic axes, and
    unsupported impedances instead of silently misinterpreting measurements.
    """
    options=['ghz','s','ma','r','50']  # Touchstone defaults
    data=[]
    for raw in Path(path).read_text(encoding='utf-8-sig').splitlines():
        line_=raw.split('!',1)[0].strip()
        if not line_: continue
        if line_.startswith('['):
            raise ValueError('Touchstone 2.x is unsupported; export Touchstone 1.x S2P')
        if line_.startswith('#'):
            options=line_[1:].lower().split()
            continue
        data.extend(float(x.replace('D','E').replace('d','e')) for x in line_.split())
    if len(options)!=5 or options[1]!='s' or options[3]!='r':
        raise ValueError('Expected # <unit> S <RI|MA|DB> R 50')
    if float(options[4])!=50:
        raise ValueError('Only 50-ohm reference impedance is supported')
    scales={'hz':1,'khz':1e3,'mhz':1e6,'ghz':1e9}
    if options[0] not in scales or options[2] not in ('ri','ma','db'):
        raise ValueError('Unsupported Touchstone unit or encoding')
    if not data or len(data)%9:
        raise ValueError('Expected nine numbers per two-port point; no noise block')
    a=np.array(data).reshape(-1,9)
    f=a[:,0]*scales[options[0]]
    if not np.isfinite(a).all() or len(f)<2 or np.any(f<=0) or np.any(np.diff(f)<=0):
        raise ValueError('Need finite data and at least two strictly increasing positive frequencies')
    pairs=a[:,1:].reshape(-1,4,2)
    if options[2]=='ri': z=pairs[:,:,0]+1j*pairs[:,:,1]
    else:
        mag=pairs[:,:,0] if options[2]=='ma' else 10**(pairs[:,:,0]/20)
        z=mag*np.exp(1j*np.deg2rad(pairs[:,:,1]))
    s=np.empty((len(f),2,2),complex)
    s[:,0,0],s[:,1,0],s[:,0,1],s[:,1,1]=z.T
    return f,s

def interp_complex(f, y, x):
    if min(x)<f[0] or max(x)>f[-1]:
        raise ValueError('Sweep does not cover required frequencies; extrapolation refused')
    return np.interp(x,f,y.real)+1j*np.interp(x,f,y.imag)

def metrics(f,s,cfg):
    targets=cfg['targets']
    lo,hi=np.array(targets['passband_mhz'])*1e6
    if f[0]>lo or f[-1]<hi:
        raise ValueError('Sweep must cover the complete 902-928 MHz passband')
    ix=(f>=lo)&(f<=hi)
    if ix.sum()<5: raise ValueError('Need at least five measured/simulated points in the passband')
    band=np.unique(np.r_[lo,f[ix],hi])
    il=-db(interp_complex(f,s[:,1,0],band))
    rl=-db(interp_complex(f,s[:,0,0],band))
    result={'worst_passband_insertion_loss_db':float(il.max()),
            'worst_passband_return_loss_db':float(rl.min()),
            'passband_ripple_db':float(np.ptp(il)),
            'insertion_loss_915_db':float(-db(interp_complex(f,s[:,1,0],[915e6]))[0]),
            'return_loss_915_db':float(-db(interp_complex(f,s[:,0,0],[915e6]))[0]),
            'passband_pass':bool(il.max()<=targets['max_insertion_loss_db'] and rl.min()>=targets['min_return_loss_db']),
            'stopband':{}}
    for mhz,atten in targets['stopband_min_attenuation_db'].items():
        hz=float(mhz)*1e6
        if f[0]<=hz<=f[-1]:
            value=float(-db(interp_complex(f,s[:,1,0],[hz]))[0])
            result['stopband'][mhz]={'attenuation_db':value,'pass':value>=atten}
        else: result['stopband'][mhz]={'attenuation_db':None,'pass':None,'reason':'outside sweep'}
    flags=[x['pass'] for x in result['stopband'].values()]
    result['overall_pass']=False if not result['passband_pass'] or False in flags else (None if None in flags else True)
    return result

def plot_traces(traces, out, title):
    fig,axes=plt.subplots(2,1,figsize=(10,7),sharex=True,layout='constrained')
    for f,s,label in traces:
        axes[0].plot(f/1e6,db(s[:,1,0]),label=label)
        axes[1].plot(f/1e6,-db(s[:,0,0]),label=label)
    for ax in axes:
        ax.axvspan(902,928,color='green',alpha=.1)
        ax.grid(alpha=.25); ax.legend(fontsize=8)
    axes[0].set(ylabel='S21 (dB)',ylim=(-60,1),title=title)
    axes[1].set(ylabel='Input return loss (dB)',xlabel='Frequency (MHz)',ylim=(0,45))
    axes[0].axhline(-3,color='gray',linestyle=':')
    axes[1].axhline(10,color='gray',linestyle=':')
    fig.savefig(out,dpi=180); plt.close(fig)

def run_simulation(cfg, out):
    out.mkdir(parents=True,exist_ok=True)
    f=np.unique(np.r_[np.linspace(200e6,2200e6,4001),902e6,915e6,928e6,433e6,1830e6])
    ideal=simulate(f,cfg,True); nominal=simulate(f,cfg)
    write_s2p(out/'ideal.s2p',f,ideal,'SIMULATED ideal lumped circuit; not measured')
    write_s2p(out/'nominal.s2p',f,nominal,'SIMULATED vendor inductor fit + estimated PCB/capacitor parasitics; not measured')
    plot_traces([(f,ideal,'Ideal lumped simulation'),(f,nominal,'Estimated board simulation')],out/'response.png','RF915 Rev A - SIMULATED, NOT MEASURED')
    result={'status':'SIMULATED_NOT_MEASURED','ideal':metrics(f,ideal,cfg),'estimated_board':metrics(f,nominal,cfg)}
    rng=np.random.default_rng(915)
    samples=[]
    # Independent uniform component tolerance sensitivity, NOT process corners or yield.
    for _ in range(300):
        v={ref:rng.uniform(.95,1.05) for ref in ('L1','L2','L3')}
        v.update({ref:rng.uniform(-.1,.1) for ref in ('C1','C3')})
        v['C2']=rng.uniform(-.5,.5)
        # Assembly/PCB uncertainty deliberately wider than component tolerances.
        v['return_nh']=rng.uniform(.05,.35)
        m=metrics(f,simulate(f,cfg,variation=v),cfg)
        samples.append([m['worst_passband_insertion_loss_db'],m['worst_passband_return_loss_db'],m['overall_pass']])
    with (out/'tolerance_samples.csv').open('w',newline='') as fp:
        w=csv.writer(fp);w.writerow(['max_IL_db','min_RL_db','all_targets_pass']);w.writerows(samples)
    result['sensitivity']={'seed':915,'samples':300,'passing_samples':sum(bool(x[2]) for x in samples),
                           'meaning':'Illustrative independent uniform tolerances and branch parasitics, not measured yield'}
    (out/'metrics.json').write_text(json.dumps(result,indent=2)+'\n')
    fig,ax=plt.subplots(figsize=(7,4),layout='constrained')
    a=np.asarray(samples,float)
    ax.scatter(a[:,0],a[:,1],s=10,alpha=.5)
    ax.axvline(3,c='red',ls='--');ax.axhline(10,c='red',ls='--')
    ax.set(xlabel='Worst passband insertion loss (dB)',ylabel='Worst passband return loss (dB)',title='SIMULATED tolerance/PCB sensitivity - not manufacturing yield')
    ax.grid(alpha=.2);fig.savefig(out/'sensitivity.png',dpi=180);plt.close(fig)
    print(json.dumps(result,indent=2))

def analyze(args,cfg):
    f,s=read_s2p(args.input)
    out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    if args.kind=='measured':
        if not args.metadata: raise ValueError('Measured data requires --metadata with instrument and calibration details')
        meta=json.loads(Path(args.metadata).read_text())
        for key in ('instrument','date','calibration','reference_plane','board_revision','operator'):
            if not meta.get(key): raise ValueError('Missing measurement metadata: '+key)
        if 'SIMULATED' in Path(args.input).read_text().upper():
            raise ValueError('Input is marked SIMULATED; cannot label it measured')
    else: meta={'note':'User supplied data; not claimed to be a physical measurement'}
    result={'kind':args.kind,'input':str(Path(args.input).resolve()),'metadata':meta,'metrics':metrics(f,s,cfg)}
    result['warnings']=[]
    channels=meta.get('measured_channels',['S11','S21']) if args.kind=='measured' else ['S11','S21','S12','S22']
    full=all(x in channels for x in ['S11','S21','S12','S22'])
    passive_test=np.linalg.svd(s,compute_uv=False)[:,0] if full else np.sqrt(abs(s[:,0,0])**2+abs(s[:,1,0])**2)
    if np.any(passive_test>1.02):
        result['warnings'].append('Data exceeds a passive power bound; check calibration, noise, or normalization')
    if not full:
        result['warnings'].append('Forward-only acquisition: S12/S22 are not treated as measured, regardless of exporter placeholders')
    traces=[(f,s,args.kind.upper()+': '+Path(args.input).name)]
    if args.reference:
        fr,sr=read_s2p(args.reference)
        traces.append((fr,sr,'Reference: '+Path(args.reference).name))
    plot_traces(traces,out/'comparison.png',f'RF915 - {args.kind.upper()} input analysis')
    gd=-np.gradient(np.unwrap(np.angle(s[:,1,0])),2*np.pi*f)*1e9
    with (out/'data.csv').open('w',newline='') as fp:
        w=csv.writer(fp);w.writerow(['frequency_hz','s11_db','s21_db','s12_db','s22_db','group_delay_ns'])
        reverse1=db(s[:,0,1]) if full else ['']*len(f)
        reverse2=db(s[:,1,1]) if full else ['']*len(f)
        w.writerows(zip(f,db(s[:,0,0]),db(s[:,1,0]),reverse1,reverse2,gd))
    (out/'metrics.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest='command',required=True)
    sim=sub.add_parser('simulate');sim.add_argument('--output',default=str(ROOT/'results/simulation'))
    a=sub.add_parser('analyze');a.add_argument('input');a.add_argument('--output',required=True)
    a.add_argument('--kind',choices=['measured','simulation','unverified'],default='unverified')
    a.add_argument('--metadata');a.add_argument('--reference')
    args=p.parse_args();cfg=json.loads((ROOT/'design.json').read_text())
    try:
        if args.command=='simulate': run_simulation(cfg,Path(args.output))
        else: analyze(args,cfg)
    except (ValueError,OSError,json.JSONDecodeError) as e:
        p.exit(2,f'Error: {e}\n')

if __name__=='__main__': main()
