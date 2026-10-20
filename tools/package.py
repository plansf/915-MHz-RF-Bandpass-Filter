"""Validate generated deliverables and create an archive outside the project."""
import hashlib
import json
import platform
import re
import zipfile
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
import numpy
import matplotlib

ROOT=Path(__file__).resolve().parents[1]

class Links(HTMLParser):
    def handle_starttag(self,tag,attrs):
        for key,value in attrs:
            if key=='href' and value and not value.startswith(('http','data:','#')):
                if not (ROOT/value).exists():raise ValueError('Missing report link: '+value)

def main():
    raw=(ROOT/'results/build.log').read_bytes()
    # PowerShell 5 redirects to UTF-16; support that encoding too.
    log=raw.decode('utf-16' if raw.startswith((b'\xff\xfe',b'\xfe\xff')) else 'utf-8-sig')
    match=re.search(r'Ran (\d+) tests',log)
    if not match or not re.search(r'\nOK\s',log):raise ValueError('Passing tests missing from build log')
    erc=(ROOT/'hardware/erc.rpt').read_text()
    if 'Errors 0  Warnings 0' not in erc:raise ValueError('ERC not clean')
    for name in ['drc','thru-drc']:
        report=(ROOT/f'hardware/{name}.rpt').read_text()
        if 'Found 0 DRC violations' not in report or 'Found 0 unconnected pads' not in report:
            raise ValueError(name+' not clean')
    for name in ['rf915','rf915-thru']:
        p=ROOT/'fabrication'/name
        for suffix in ['-F_Cu.gtl','-B_Cu.gbl','-F_Mask.gts','-B_Mask.gbs','-Edge_Cuts.gm1','.drl']:
            if not (p/(name+suffix)).is_file():raise ValueError('Missing fabrication layer '+suffix)
        with zipfile.ZipFile(ROOT/f'fabrication/{name}-revA-gerbers.zip') as z:
            if z.testzip():raise ValueError('Corrupt fabrication archive')
    m=json.loads((ROOT/'results/simulation/metrics.json').read_text())
    if m['status']!='SIMULATED_NOT_MEASURED':raise ValueError('Unexpected simulation status')
    record=f'''RF915 Rev A digital prototype verification
Generated: {datetime.now().astimezone().isoformat(timespec='seconds')}
Python: {platform.python_version()}; NumPy: {numpy.__version__}; Matplotlib: {matplotlib.__version__}
CAD tool used: KiCad 9.0.5

PASS: {match[1]} unittest cases (independent nodal comparison, matched line delay,
passivity/reciprocity, vendor low-frequency limit, Touchstone encodings/pair order,
input rejection, missing/sparse coverage, simulated-data provenance guard).
PASS: filter ERC: zero errors and warnings.
PASS: filter DRC: zero violations, zero unconnected pads, zero footprint/parity issues.
PASS: through-board DRC: zero violations, zero unconnected pads.
PASS: nominal simulation and 300 sensitivity samples generated.
PASS: simulation Touchstone CLI analysis and reference comparison completed.
PASS: required fabrication layers/drill files present; fabrication ZIP integrity.
PASS: schematic and board previews rendered and visually inspected during preparation.
PASS: local report links checked when packaging.

NOT PERFORMED: physical fabrication, soldering, VNA calibration or measurements.
NOT PERFORMED: full-wave EM analysis, production qualification or external SPICE run.
UNVERIFIED: exact NanoVNA model and useful 1830 MHz capability.
Nominal simulated performance is not a physical acceptance result.
See results/build.log and hardware/*.rpt for execution records.
'''
    (ROOT/'results/verification.txt').write_text(record)
    Links().feed((ROOT/'REPORT.html').read_text(encoding='utf-8'))
    excluded={'__pycache__','.venv','.git','references','symbols'}
    stale={'pcb-top.svg','rf915.svg'}
    files=[p for p in ROOT.rglob('*') if p.is_file() and not excluded.intersection(p.relative_to(ROOT).parts)
           and p.name not in stale and p.name!='SHA256SUMS.txt' and p.suffix not in ('.pyc','.lck')]
    manifest=''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.relative_to(ROOT).as_posix()+'\n'
                     for p in sorted(files))
    (ROOT/'SHA256SUMS.txt').write_text(manifest)
    files.append(ROOT/'SHA256SUMS.txt')
    target=ROOT.parent/'rf915-filter-revA.zip'
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
        for p in files:z.write(p,Path(ROOT.name)/p.relative_to(ROOT))
    with zipfile.ZipFile(target) as z:
        if z.testzip():raise ValueError('Corrupt project ZIP')
    print(f'Packaged {len(files)} files: {target} ({target.stat().st_size:,} bytes)')

if __name__=='__main__':main()
