# RF915: 915 MHz filter and NanoVNA characterization

**Revision A: complete digital prototype package; not physically built or measured.**

Project by Francisco Plans, developed with AI assistance as an engineering
learning project. The CAD, circuit model and analysis workflow have digital
verification records; fabrication and NanoVNA measurements are still pending.
See [the portfolio notes](docs/PORTFOLIO.md) for the current evidence and
learning plan.

A hands-on RF project for Francisco Plans: assemble a passive LC bandpass filter,
measure S11/S21 with a NanoVNA, and compare the result with a reproducible circuit
model. A separate straight-through reference board helps identify connector and
fixture problems. This project builds RF hardware and measurement experience;
it does not demonstrate DRAM design experience.

Start with [the illustrated engineering report](REPORT.html), then follow
[fabrication and assembly](docs/BUILD.md) and [the NanoVNA procedure](docs/MEASURE.md).

## Files

| Deliverable | Location |
|---|---|
| Editable schematic and routed PCB | `hardware/rf915.kicad_pro` |
| Through reference board | `hardware/rf915-thru.kicad_pro` |
| Schematic PDF | `results/cad/schematic.pdf` |
| Parts to order | `hardware/BOM.csv` |
| PCB manufacturing ZIPs | `fabrication/*-revA-gerbers.zip` |
| Circuit assumptions and equations | `docs/DESIGN.md`, `design.json` |
| Python simulation and Touchstone analysis | `rf915.py` |
| Simulated response and sensitivity | `results/simulation/` |
| Measurement metadata and raw-data folder | `measurements/` |
| Portfolio write-up to complete after testing | `docs/PORTFOLIO.md` |
| Verification records | `hardware/*rpt`, `results/verification.txt` |

## Run the software

In PowerShell, from this folder (Python 3.11+):

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe rf915.py simulate
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

No instrument is needed for simulation. For your own measurement, first copy
`measurements/metadata-template.json` to a new JSON file and complete its fields:

```powershell
.\.venv\Scripts\python.exe rf915.py analyze measurements\filter-revA.s2p --kind measured --metadata measurements\filter-revA.json --output results\measured-revA --reference results\simulation\nominal.s2p
```

Outputs are a comparison plot, metrics JSON, and CSV including group delay.
Only mark real acquisitions `measured`. An included simulation file cannot be
relabeled as a measurement. A missing stopband frequency produces an unknown
result, not a pass. Touchstone 1.x, 50-ohm, two-port RI/MA/DB files are supported.

## Rebuild the CAD and package

KiCad 9 is required; the generator uses its bundled Python, pcbnew and wx.
`build.ps1` uses the `python` on PATH for scientific analysis. Activate your venv
first, or install requirements in that Python. To regenerate the report, also
install `requirements-report.txt`.

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-report.txt
.\build.ps1
```

The script regenerates native CAD, refills copper zones, checks ERC/DRC and
schematic parity, exports Gerbers/drills, runs tests, simulates and creates the
report. It stops on native-command failures. **It overwrites generated CAD.**
For a hand-edited layout, preserve a copy and update the generator before rebuilding.
UUIDs and export timestamps may change on regeneration.

## What counts as success

Design targets: insertion loss <=3 dB and input return loss >=10 dB across
902-928 MHz; attenuation >=15 dB at 433 MHz and 1830 MHz. This is a **broad
educational bandpass filter**, not a sharp 26 MHz channel-selection filter.
The shipped nominal circuit model passes; that is not evidence that an assembled
board will pass. The model is particularly sensitive to shunt layout parasitics.
Read the limitations in `docs/DESIGN.md` before ordering.

Your next steps are to order the two boards and parts, assemble, calibrate your
NanoVNA, capture data and tune. The exact NanoVNA model is unknown; only test at
915 MHz and 1830 MHz if your unit has a documented usable range there. File export
is used instead of firmware-specific serial commands.

Vendor references and footprint attribution: [sources](docs/SOURCES.md).
