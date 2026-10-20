"""Build a self-contained HTML report from current generated artifacts."""
import base64
import html
import json
from pathlib import Path
import pymupdf

ROOT=Path(__file__).resolve().parents[1]
CAD=ROOT/'results/cad'

def uri(path,mime):
    return f'data:{mime};base64,'+base64.b64encode(path.read_bytes()).decode()

def main():
    # Render actual KiCad exports; these are not illustrative replacements.
    for name in ['rf915-top','rf915-bottom','rf915-thru-top','rf915-thru-bottom']:
        doc=pymupdf.open(CAD/(name+'.svg'))
        page=doc[0]
        page.get_pixmap(matrix=pymupdf.Matrix(10,10),alpha=False).save(CAD/(name+'.png'))
    doc=pymupdf.open(CAD/'schematic.pdf')
    doc[0].get_pixmap(matrix=pymupdf.Matrix(2,2),alpha=False).save(CAD/'schematic.png')
    crop=pymupdf.Rect(20,60,228,153)* (72/25.4)
    doc[0].get_pixmap(matrix=pymupdf.Matrix(2.5,2.5),clip=crop,alpha=False).save(CAD/'schematic-detail.png')
    m=json.loads((ROOT/'results/simulation/metrics.json').read_text())
    n=m['estimated_board']; tol=m['sensitivity']
    rows=[('Worst insertion loss, 902-928 MHz',f"{n['worst_passband_insertion_loss_db']:.2f} dB",'<=3 dB'),
          ('Worst input return loss, 902-928 MHz',f"{n['worst_passband_return_loss_db']:.2f} dB",'>=10 dB'),
          ('Attenuation at 433 MHz',f"{n['stopband']['433']['attenuation_db']:.2f} dB",'>=15 dB'),
          ('Attenuation at 1830 MHz',f"{n['stopband']['1830']['attenuation_db']:.2f} dB",'>=15 dB')]
    table=''.join('<tr>'+''.join('<td>'+html.escape(c)+'</td>' for c in row)+'</tr>' for row in rows)
    def img(path,alt,mime='image/png'):
        return f'<img src="{uri(ROOT/path,mime)}" alt="{html.escape(alt)}">'
    report=f'''<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>RF915 Rev A engineering report</title>
<style>
body{{font:17px/1.6 system-ui,sans-serif;color:#182837;background:#f1f5f8;margin:0}}
main{{max-width:1000px;margin:36px auto;padding:36px;background:white;border-radius:12px}}
h1{{font-size:40px;line-height:1.15}}h2{{margin-top:38px;color:#174a63}}
.tag{{font-weight:700;color:#804400;background:#fff0cb;padding:12px 18px;border-radius:6px}}
.sub{{color:#516674}}img{{max-width:100%;height:auto;display:block;margin:18px auto}}
table{{border-collapse:collapse;width:100%;font-size:16px}}td,th{{text-align:left;padding:11px;border-bottom:1px solid #cdd9df}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:20px}}a{{color:#005d84}}
code{{background:#edf3f6;padding:2px 5px}}@media(max-width:700px){{main{{margin:0;padding:20px}}.grid{{display:block}}h1{{font-size:30px}}}}
@media print{{body{{background:white}}main{{margin:0;padding:0}}h2{{break-after:avoid}}img,table{{break-inside:avoid}}}}
</style><main>
<p class="sub">FRANCISCO PLANS / RF HARDWARE PROJECT / REVISION A</p>
<h1>915 MHz filter<br>Design, build and measurement package</h1>
<p class="tag">UNBUILT PROTOTYPE. All performance below is simulated, not measured.</p>
<p>A passive three-resonator LC network on a 40 x 24 mm, two-layer, 0.8 mm PCB.
The package includes editable KiCad files, manufacturing exports, a parts list,
Python analysis, a through reference board and a NanoVNA test procedure.</p>
<h2>Predicted performance</h2>
<p>The estimated board model passes the proposed targets. Package and PCB parasitics
are only approximations; fabrication, assembly, tuning and physical validation remain.</p>
<table><tr><th>Metric</th><th>Estimated board model</th><th>Target</th></tr>{table}</table>
{img('results/simulation/response.png','Simulated ideal and estimated board S21 and input return loss')}
<p>The ideal lumped circuit with the same BOM fails return-loss matching. The
selected values compensate estimated parasitics. This dependence is a major
first-prototype risk, not evidence of a measured match.</p>
<h2>Component and ground-return sensitivity</h2>
{img('results/simulation/sensitivity.png','Illustrative simulated sensitivity samples')}
<p>{tol['passing_samples']} of {tol['samples']} illustrative samples satisfy all
modeled targets. This is not measured yield. Independent component tolerances
and a limited ground-return range omit coupling, connector uncertainty and
other real effects. See <a href="docs/DESIGN.md">design assumptions</a>.</p>
<h2>Actual routed PCB exports</h2><div class="grid"><div><h3>Filter, top</h3>
{img('results/cad/rf915-top.png','Filter front copper and silkscreen')}
</div><div><h3>Filter, bottom viewed from top</h3>
{img('results/cad/rf915-bottom.png','Filter bottom copper viewed from above, not mirrored')}
</div></div>
<p>Short component interconnects, paired shunt ground vias and a bottom ground
plane keep the RF path compact. Vertical SMA connectors provide the two ports.</p>
<h3>Through reference, top</h3>
{img('results/cad/rf915-thru-top.png','Separate straight through reference board')}
<p>The reference board diagnoses cable and launch problems; it is not an exact
two-port de-embedding fixture for the filter.</p>
<h2>Schematic</h2>
{img('results/cad/schematic-detail.png','Native KiCad schematic export, detail')}
<p><a href="results/cad/schematic.pdf">Open the full-resolution schematic PDF</a>.
C1/C3: 1.8 pF. L1/L3: 15 nH. L2: 1.8 nH. C2: 10 pF.</p>
<h2>Build and validate</h2>
<ol><li>Read <a href="docs/BUILD.md">ordering and assembly instructions</a> and
use <a href="hardware/BOM.csv">the BOM</a>. Keep the specified 0.8 mm stackup.</li>
<li>Order the filter and through-board Gerber ZIPs in <code>fabrication/</code>.</li>
<li>Assemble, photograph and complete the DC continuity checks.</li>
<li>Follow <a href="docs/MEASURE.md">the NanoVNA procedure</a>, recording instrument
range and calibration reference planes.</li>
<li>Analyze raw Touchstone exports, compare with simulation and document tuning.</li></ol>
<p>No physical measurements are included. Unsupported frequency coverage stays
unverified. The exact NanoVNA model is not known, so no firmware-specific USB
control or 1830 MHz capability is assumed.</p>
<h2>Verification and next evidence</h2>
<p>Read <a href="results/verification.txt">the verification record</a> for actual
software and CAD checks. ERC/DRC establish connectivity and layout-rule compliance;
they do not establish RF performance. The ideal SPICE netlist is an optional
cross-check and has not been run in an external SPICE executable.</p>
<p><a href="README.md">Project guide</a> &middot;
<a href="docs/PORTFOLIO.md">Portfolio evidence plan</a> &middot;
<a href="docs/SOURCES.md">Primary references and attribution</a></p>
</main></html>'''
    (ROOT/'REPORT.html').write_text(report,encoding='utf-8')
    print('Created REPORT.html and rendered CAD previews')

if __name__=='__main__':main()
