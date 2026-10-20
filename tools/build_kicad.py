"""Generate native KiCad 9 schematic/boards; run with KiCad's bundled Python.

Footprints are vendored into the project for portability. No CAD GUI automation.
"""
import json
import math
import os
import shutil
import uuid
from pathlib import Path
import pcbnew as k
import wx

ROOT=Path(__file__).resolve().parents[1]
HW=ROOT/'hardware'
LIB=Path(os.environ.get('KICAD9_FOOTPRINT_DIR',r'C:/Program Files/KiCad/9.0/share/kicad/footprints'))
CFG=json.loads((ROOT/'design.json').read_text())
U=lambda: str(uuid.uuid4())
mm=k.FromMM
pt=lambda x,y:k.VECTOR2I(mm(x),mm(y))
FP={
 'J':'Connector_Coaxial:SMA_Amphenol_132134_Vertical',
 'C':'Capacitor_SMD:C_0402_1005Metric',
 'L':'Inductor_SMD:L_0603_1608Metric',
}
NETS={'J1':('RF_IN','GND'),'C1':('RF_IN','N1'),'L1':('N1','MID'),
      'L2':('MID','GND'),'C2':('MID','GND'),
      'L3':('MID','N2'),'C3':('N2','RF_OUT'),'J2':('RF_OUT','GND')}

def value(ref):
    if ref.startswith('J'):return 'SMA 50 ohm'
    return f"{CFG['components'][ref]:g}"+('nH' if ref[0]=='L' else 'pF')

def fpname(ref):return FP[ref[0]].split(':')[1]

def line(board,start,end,width=.45,net=None,layer=None):
    if net:
        t=k.PCB_TRACK(board);t.SetStart(pt(*start));t.SetEnd(pt(*end));t.SetWidth(mm(width));t.SetLayer(k.F_Cu);t.SetNet(net)
    else:
        t=k.PCB_SHAPE(board);t.SetShape(k.SHAPE_T_SEGMENT);t.SetStart(pt(*start));t.SetEnd(pt(*end));t.SetWidth(mm(width));t.SetLayer(layer or k.Edge_Cuts)
    board.Add(t)

def build_board(name,thru=False):
    b=k.BOARD();b.GetDesignSettings().SetCopperLayerCount(2);b.GetDesignSettings().SetBoardThickness(mm(.8))
    b.GetTitleBlock().SetTitle('RF915 '+('THRU reference' if thru else 'LC bandpass filter'))
    b.GetTitleBlock().SetRevision('A - UNMEASURED PROTOTYPE')
    nets={}
    for name_ in ['GND','RF_IN','N1','MID','N2','RF_OUT']:
        n=k.NETINFO_ITEM(b,'/'+name_);b.Add(n);nets[name_]=n
    comps={}
    positions={'J1':(55,62,0),'C1':(65,62,0),'L1':(67.5,62,0),
               'L2':(70,63.3,90),'C2':(70,60.5,270),
               'L3':(72.5,62,0),'C3':(75,62,0),'J2':(85,62,0)}
    for ref,(x,y,angle) in positions.items():
        if thru and ref[0]!='J':continue
        lib,nm=FP[ref[0]].split(':')
        fp=k.FootprintLoad(str(HW/'RF915.pretty'),nm)
        fp.SetReference(ref);fp.SetValue(value(ref));fp.SetPosition(pt(x,y));fp.SetOrientationDegrees(angle)
        fp.SetFPID(k.LIB_ID('RF915',nm))
        fp.SetPath(k.KIID_PATH('/'+SCHEM_ROOT+'/'+IDS[ref])) if not thru else None
        fp.Value().SetVisible(False)
        fp.Reference().SetTextSize(pt(.8,.8));fp.Reference().SetTextThickness(mm(.12))
        fp.Reference().SetPosition(pt(x+(2.5 if ref in ('C2','L2') else 0), y+(-2.3 if ref not in ('C2','L2') else 0)))
        fp.Reference().SetTextAngle(k.EDA_ANGLE(0,k.DEGREES_T))
        if ref=='C2':fp.Reference().SetPosition(pt(70,57.5))
        for pad in fp.Pads():
            pnum=int(pad.GetNumber())
            netname=NETS[ref][pnum-1]
            if thru and netname=='RF_OUT':netname='RF_IN'
            # Rotate branch inductor so pin 1 is nearest center line.
            if ref in ('L2','C2'):netname='GND' if pnum==1 else 'MID'
            pad.SetNet(nets[netname])
        # L2 reversed passive pins electrically equivalent; align schematic pins below.
        b.Add(fp);comps[ref]=fp
    def padpos(ref,pin):
        p=next(p for p in comps[ref].Pads() if p.GetNumber()==str(pin)).GetPosition()
        return (k.ToMM(p.x),k.ToMM(p.y))
    if thru:
        line(b,padpos('J1',1),padpos('J2',1),1.5,nets['RF_IN'])
    else:
        for a,pa,z,pz,net_,width in [('J1',1,'C1',1,'RF_IN',1.5),('C1',2,'L1',1,'N1',.45),
                                    ('L3',2,'C3',1,'N2',.45),('C3',2,'J2',1,'RF_OUT',1.5)]:
            # Wide feed tapers to component pad through a short narrow segment.
            axy,zxy=padpos(a,pa),padpos(z,pz)
            if width==1.5:
                if a=='J1':
                    mid=(zxy[0]-1.1,zxy[1]);line(b,axy,mid,1.5,nets[net_]);line(b,mid,zxy,.45,nets[net_])
                else:
                    mid=(axy[0]+1.1,axy[1]);line(b,axy,mid,.45,nets[net_]);line(b,mid,zxy,1.5,nets[net_])
            else:line(b,axy,zxy,width,nets[net_])
        for ref,pin in [('L1',2),('L3',1),('C2',2),('L2',2)]:
            line(b,padpos(ref,pin),(70,62),.45,nets['MID'])
        # Ground-return vias immediately adjacent to each shunt pad.
        for ref,pin in [('L2',1),('C2',1)]:
            x,y=padpos(ref,pin)
            for dx in [-.65,.65]:
                line(b,(x,y),(x+dx,y),.4,nets['GND'])
                via=k.PCB_VIA(b);via.SetPosition(pt(x+dx,y));via.SetWidth(mm(.6));via.SetDrill(mm(.3));via.SetLayerPair(k.F_Cu,k.B_Cu);via.SetNet(nets['GND']);b.Add(via)
    # Closed 40 x 24 mm outline, bottom continuous ground. Top fill kept away
    # from the signal corridor; branch pads connect directly via bottom ground.
    for a,z in [((50,50),(90,50)),((90,50),(90,74)),((90,74),(50,74)),((50,74),(50,50))]:line(b,a,z,.05)
    def zone(layer,coords):
        z=k.ZONE(b);z.SetLayer(layer);z.SetNet(nets['GND']);z.SetLocalClearance(mm(.25));z.SetPadConnection(k.ZONE_CONNECTION_FULL)
        z.SetMinThickness(mm(.2));o=z.Outline();o.NewOutline()
        for x,y in coords:o.Append(mm(x),mm(y))
        b.Add(z)
    zone(k.B_Cu,[(50.25,50.25),(89.75,50.25),(89.75,73.75),(50.25,73.75)])
    zone(k.F_Cu,[(50.25,50.25),(89.75,50.25),(89.75,58),(50.25,58)])
    zone(k.F_Cu,[(50.25,66),(89.75,66),(89.75,73.75),(50.25,73.75)])
    # Stitching at 2 mm spacing, avoiding through-hole SMA grounds.
    for y in [53,56,68,71]:
        for x in range(52,90,2):
            if any(abs(x-cx)<3.5 and abs(y-62)<4 for cx in [55,85]):continue
            v=k.PCB_VIA(b);v.SetPosition(pt(x,y));v.SetWidth(mm(.6));v.SetDrill(mm(.3));v.SetLayerPair(k.F_Cu,k.B_Cu);v.SetNet(nets['GND']);b.Add(v)
    for txt,x,y,size in [('RF915 '+('THRU' if thru else 'BPF')+' REV A',70,51.5,1),('0.8mm / 50R / PROTOTYPE',70,72.5,.8)]:
        t=k.PCB_TEXT(b);t.SetText(txt);t.SetPosition(pt(x,y));t.SetTextSize(pt(size,size));t.SetTextThickness(mm(.12));t.SetLayer(k.F_SilkS);b.Add(t)
    k.SaveBoard(str(HW/(name+'.kicad_pcb')),b)

def effects(size=1.27):return f'(effects (font (size {size} {size})))'

def make_symbol(kind,vertical=False):
    name=kind+('_V' if vertical else '')
    ref='J' if kind=='SMA' else kind
    # Dedicated passive 2-pin symbols, pins on 2.54mm grid.
    def xy(x,y):return (-y,x) if vertical else (x,y)
    if kind=='C':segments=[((-0.5,-1.5),(-.5,1.5)),((.5,-1.5),(.5,1.5)),((-1.016,0),(-.5,0)),((.5,0),(1.016,0))]
    elif kind=='L':
        points=[(-1.016,0)]+[(-1+i*.02,.55*abs(math.sin(math.pi*i/25))) for i in range(101)]+[(1.016,0)]
        segments=list(zip(points[:-1],points[1:]))
    else:segments=[((-1.016,0),(1.016,0)),((-1,-1),(-1,1)),((-1,1),(1,1)),((1,1),(1,-1)),((1,-1),(-1,-1))]
    graphics=''
    for a,b in segments:
        a,b=xy(*a),xy(*b)
        graphics+=f'(polyline (pts (xy {a[0]} {a[1]}) (xy {b[0]} {b[1]})) (stroke (width 0) (type default)) (fill (type none)))'
    pins=''
    for n,x,angle in [(1,-2.54,0),(2,2.54,180)]:
        x,y=xy(x,0);angle=(angle+90)%360 if vertical else angle
        pins+=f'(pin passive line (at {x} {y} {angle}) (length 1.524) (name "{n}" {effects()}) (number "{n}" {effects()}))'
    return f'''(symbol "RF915:{name}" (pin_numbers hide) (pin_names hide) (in_bom yes) (on_board yes)
    (property "Reference" "{ref}" (at 0 3.81 0) {effects()})
    (property "Value" "{name}" (at 0 -3.81 0) {effects()})
    (symbol "{name}_0_1" {graphics}) (symbol "{name}_1_1" {pins}))'''

SCHEM_ROOT='a08bfe37-f949-488a-b999-020a3c8be915'
IDS={ref:str(uuid.uuid5(uuid.NAMESPACE_DNS,'rf915.'+ref)) for ref in NETS}

def build_schematic():
    out=[f'(kicad_sch (version 20250114) (generator "eeschema") (uuid "{SCHEM_ROOT}") (paper "A4")',
         '(title_block (title "RF915 - 915 MHz LC Bandpass Filter") (rev "A") (comment 1 "UNBUILT PROTOTYPE - nominal values compensate estimated parasitics"))',
         '(lib_symbols '+''.join(make_symbol(t,v) for t,v in [('C',False),('L',False),('L',True),('C',True),('SMA',False)])+')']
    positions={'J1':(40.64,76.2),'C1':(66.04,76.2),'L1':(91.44,76.2),'L2':(111.76,96.52),
               'C2':(132.08,96.52),'L3':(152.4,76.2),'C3':(177.8,76.2),'J2':(203.2,76.2)}
    for ref,(x,y) in positions.items():
        vertical=ref in ('L2','C2');kind='SMA' if ref[0]=='J' else ref[0];sym=kind+('_V' if vertical else '')
        out.append(f'''(symbol (lib_id "RF915:{sym}") (at {x} {y} 0) (unit 1)
        (in_bom yes) (on_board yes) (dnp no) (uuid "{IDS[ref]}")
        (property "Reference" "{ref}" (at {x+5 if vertical else x} {y-3.81} 0) {effects()})
        (property "Value" "{value(ref)}" (at {x+8 if vertical else x} {y+3.81} 0) {effects()})
        (property "Footprint" "RF915:{fpname(ref)}" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))
        (pin "1" (uuid "{U()}")) (pin "2" (uuid "{U()}"))
        (instances (project "rf915" (path "/{SCHEM_ROOT}" (reference "{ref}") (unit 1)))))''')
        # Vertical pin1 is BELOW symbol, pin2 above (rotation of local left).
        coords=[(x,y+2.54),(x,y-2.54)] if vertical else [(x-2.54,y),(x+2.54,y)]
        refnets=NETS[ref]
        if vertical:
            refnets=('GND','MID')  # matches layout L2; C2 swapped in layout below
        for pin,((px,py),net) in enumerate(zip(coords,refnets),1):
            # Extend isolated terminals before labeling; avoid labels over symbols.
            endpoint=None
            if ref.startswith('J'):endpoint=(px+(-10.16 if pin==1 else 5.08),py)
            elif vertical and pin==1:endpoint=(px,py+7.62)
            elif ref=='C1' and pin==1:endpoint=(px-10.16,py)
            elif ref=='C3' and pin==2:endpoint=(px+10.16,py)
            if endpoint:
                ex,ey=endpoint
                out.append(f'(wire (pts (xy {px} {py}) (xy {ex} {ey})) (stroke (width 0) (type default)) (uuid "{U()}"))')
                if not (ref=='J2' and pin==1):
                    out.append(f'(label "{net}" (at {ex} {ey} 0) (effects (font (size 1.27 1.27)) (justify left bottom)) (uuid "{U()}"))')
    # Readable signal chain; J symbols use net labels because their second pin is ground.
    for x1,x2 in [(68.58,88.9),(93.98,111.76),(111.76,132.08),(132.08,149.86),(154.94,175.26)]:
        out.append(f'(wire (pts (xy {x1} 76.2) (xy {x2} 76.2)) (stroke (width 0) (type default)) (uuid "{U()}"))')
    for net,x in [('N1',68.58),('MID',111.76),('N2',154.94)]:
        out.append(f'(label "{net}" (at {x} 76.2 0) (effects (font (size 1.27 1.27)) (justify left bottom)) (uuid "{U()}"))')
    for x in [111.76,132.08]:
        out.append(f'(wire (pts (xy {x} 76.2) (xy {x} 93.98)) (stroke (width 0) (type default)) (uuid "{U()}"))')
        out.append(f'(junction (at {x} 76.2) (diameter 0) (color 0 0 0 0) (uuid "{U()}"))')
    for msg,x,y in [('50-ohm ports. C1/L1 and L3/C3 form series resonators; L2 || C2 is the shunt resonator.',30,125),
                    ('Bottom copper is continuous GND. C/L values must match design.json and BOM.',30,132),
                    ('SIMULATION ONLY: capacitors, PCB and launches use estimated parasitics. Tune after measurement.',30,139),
                    ('CH0 -> J1; J2 -> CH1. SMA shields connect to GND. No DC power required.',30,146)]:
        out.append(f'(text "{msg}" (at {x} {y} 0) (effects (font (size 1.27 1.27)) (justify left bottom)) (uuid "{U()}"))')
    out.append('(embedded_fonts no))')
    (HW/'rf915.kicad_sch').write_text('\n'.join(out))

if __name__=='__main__':
    app=wx.App(False)
    HW.mkdir(exist_ok=True);(HW/'RF915.pretty').mkdir(exist_ok=True)
    for libid in FP.values():
        lib,nm=libid.split(':');shutil.copyfile(LIB/(lib+'.pretty')/(nm+'.kicad_mod'),HW/'RF915.pretty'/(nm+'.kicad_mod'))
    (HW/'fp-lib-table').write_text('(fp_lib_table (version 7) (lib (name "RF915")(type "KiCad")(uri "${KIPRJMOD}/RF915.pretty")(options "")(descr "Vendored KiCad standard footprints")))')
    for project in ['rf915','rf915-thru']:
        (HW/(project+'.kicad_pro')).write_text(json.dumps({'meta':{'filename':project+'.kicad_pro','version':1},'board':{'design_settings':{'rules':{'min_clearance':0.2,'min_track_width':0.2,'min_via_diameter':0.6,'min_through_hole_diameter':0.3}}}},indent=2))
    build_schematic()
    build_board('rf915');build_board('rf915-thru',True)
    # Matching custom library prevents cache mismatch and enables symbol editing.
    syms='\n'.join(make_symbol(t,v).replace('RF915:','') for t,v in [('C',False),('C',True),('L',False),('L',True),('SMA',False)])
    (HW/'RF915.kicad_sym').write_text('(kicad_symbol_lib (version 20241209) (generator "kicad_symbol_editor") '+syms+')')
    (HW/'sym-lib-table').write_text('(sym_lib_table (version 7) (lib (name "RF915")(type "KiCad")(uri "${KIPRJMOD}/RF915.kicad_sym")(options "")(descr "Project passive symbols")))')
    for name in ['rf915','rf915-thru']:
        path=HW/(name+'.kicad_pcb')
        board=k.LoadBoard(str(path));board.BuildConnectivity()
        filler=k.ZONE_FILLER(board);filler.Fill(board.Zones());k.SaveBoard(str(path),board)
    print('Generated',HW)
