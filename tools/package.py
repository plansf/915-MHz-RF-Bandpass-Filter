"""Validate generated hardware files and create a source archive."""
import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    erc = (ROOT / 'hardware/erc.rpt').read_text()
    if 'Errors 0  Warnings 0' not in erc:
        raise ValueError('ERC is not clean')

    for name in ('drc', 'thru-drc'):
        report = (ROOT / f'hardware/{name}.rpt').read_text()
        if 'Found 0 DRC violations' not in report or 'Found 0 unconnected pads' not in report:
            raise ValueError(name + ' is not clean')

    for name in ('rf915', 'rf915-thru'):
        board = ROOT / 'fabrication' / name
        for suffix in ('-F_Cu.gtl', '-B_Cu.gbl', '-F_Mask.gts', '-B_Mask.gbs', '-Edge_Cuts.gm1', '.drl'):
            if not (board / (name + suffix)).is_file():
                raise ValueError('Missing fabrication layer ' + suffix)
        with zipfile.ZipFile(ROOT / f'fabrication/{name}-revA-gerbers.zip') as archive:
            if archive.testzip():
                raise ValueError('Corrupt fabrication archive: ' + name)

    metrics = json.loads((ROOT / 'results/simulation/metrics.json').read_text())
    if metrics.get('status') != 'SIMULATED_NOT_MEASURED':
        raise ValueError('Unexpected simulation status')

    excluded = {'.git', '.venv', '__pycache__', 'references', 'symbols'}
    stale = {'pcb-top.svg', 'rf915.svg'}
    files = []
    for path in ROOT.rglob('*'):
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT)
        if (excluded.intersection(relative.parts)
                or any(part.endswith('-backups') for part in relative.parts)
                or path.name in stale | {'fp-info-cache', 'SHA256SUMS.txt'}
                or path.suffix in ('.pyc', '.lck', '.kicad_prl')):
            continue
        files.append(path)
    manifest = ''.join(
        hashlib.sha256(p.read_bytes()).hexdigest() + '  '
        + p.relative_to(ROOT).as_posix() + '\n'
        for p in sorted(files)
    )
    (ROOT / 'SHA256SUMS.txt').write_text(manifest)
    files.append(ROOT / 'SHA256SUMS.txt')

    target = ROOT.parent / 'rf915-filter-revA.zip'
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, Path(ROOT.name) / path.relative_to(ROOT))
    with zipfile.ZipFile(target) as archive:
        if archive.testzip():
            raise ValueError('Corrupt project archive')
    print(f'Packaged {len(files)} files: {target} ({target.stat().st_size:,} bytes)')


if __name__ == '__main__':
    main()
