# RF915: 915 MHz LC Filter

I’m developing this as a student RF hardware project: design a compact filter for
the 902–928 MHz band, model it, lay out a PCB, then compare the model with a
NanoVNA measurement. Revision A is the digital prototype, the boards have been simulated, but yet to be fabricated and tested to see comparison of real Vs. theoretical measurements.

I’m keeping the assumptions and current limits visible so the simulation is not mistaken for measured hardware results.

## The design

The filter is a passive, three-resonator LC bandpass network with 50-ohm SMA
ports. It uses 1.8 pF series capacitors, 15 nH series inductors, and a 1.8 nH /
10 pF shunt resonator. The KiCad package includes the filter PCB and a separate
through-reference board. Both are routed as two-layer, 40 x 24 mm boards for a
specified 0.8 mm FR4 stackup.

The Python model calculates S-parameters and can analyze Touchstone 1.x `.s2p`
files. It includes a typical vendor model for the inductors and estimates for
capacitor, trace, connector, and ground-return parasitics. Those PCB and launch
values are assumptions; the design has not had full-wave EM analysis.

## Current results

The simulated board model meets the initial targets in `design.json`:

| Measure | Target | Estimated board model |
|---|---:|---:|
| Insertion loss across 902–928 MHz | ≤ 3 dB | 1.01 dB worst case |
| Return loss across 902–928 MHz | ≥ 10 dB | 25.14 dB worst case |
| Attenuation at 433 MHz | ≥ 15 dB | 30.44 dB |
| Attenuation at 1830 MHz | ≥ 15 dB | 47.65 dB |

These are simulation outputs, not acceptance results. The ideal lumped model
misses the return-loss target, which shows how much the prediction depends on
the estimated PCB parasitics. In an illustrative 300-case sensitivity sweep,
275 cases met the modeled targets; this is not a manufacturing-yield estimate.
See `results/simulation/metrics.json` and `results/simulation/response.png`.

## What has been checked

The original validation run recorded 10 Python tests passing, clean KiCad ERC
and DRC checks for both boards, and valid fabrication exports. These checks cover
the digital design package. The included KiCad reports are the raw ERC/DRC
outputs. No board has been ordered, assembled, or tested with a VNA. The design
also has not had production qualification or full-wave EM analysis.

## Run the model

Python 3.11+ with NumPy and Matplotlib is needed for the analysis scripts. From
this folder in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe rf915.py simulate
```

To analyze a real acquisition, keep the original Touchstone file and complete
`measurements/metadata-template.json` with the instrument and calibration
details. Then run:

```powershell
.\.venv\Scripts\python.exe rf915.py analyze measurements\filter-revA.s2p --kind measured --metadata measurements\filter-revA.json --output results\measured-revA --reference results\simulation\nominal.s2p
```

The analyzer requires complete coverage of the passband and will not label the
included simulated files as measured data. It reports S-parameter metrics, a
comparison plot, CSV data, and group delay.

## Next step: build and measure

The Gerber archives are in `fabrication/`; the parts list is `hardware/BOM.csv`.
Before ordering, confirm the fabricator can provide the specified two-layer,
0.8 mm FR4 stackup. Assemble the filter and through-reference boards, check them
with a multimeter, calibrate the NanoVNA at the cable ends, and save the raw
Touchstone exports and measurement metadata. Compare those measurements with
the model before deciding whether to tune or make Revision B. Do not substitute
1.6 mm board thickness without revising the design.

## Repository map

- `hardware/` — editable KiCad design, BOM, and ERC/DRC records
- `fabrication/` — Gerber, drill, and board ZIP files
- `rf915.py`, `design.json` — model, Touchstone analysis, and design inputs
- `results/simulation/` — simulated Touchstone files, metrics, and plots
- `measurements/` — metadata template and place for future raw measurements
- `tests/` — model and Touchstone parser tests

## References

- [Coilcraft 0603HP SPICE model](https://www.coilcraft.com/getmedia/353e55d2-1d20-470a-9567-550d989b0e5d/spice_0603hp.pdf) — inductor model basis.
- [Amphenol 132134 mechanical drawing](https://www.amphenolrf.com/library/download/link/link_id/593003/parent/132134/) — vertical SMA footprint dimensions.
- [KiCad 9 CLI documentation](https://docs.kicad.org/9.0/en/cli/cli.html) — ERC, DRC, and fabrication export tools.
- [NanoVNA calibration](https://nanovna.com/?page_id=2) and [NanoVNA-Saver](https://github.com/NanoVNA-Saver/nanovna-saver) — instrument setup and Touchstone export references.

The vendor datasheet and KiCad-derived footprints retain their original sources;
they are included as references and are not claimed as original work.
