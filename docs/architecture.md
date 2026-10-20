# Project architecture

`design.json` defines BOM values, acceptance targets and estimated parasitics.
`rf915.py` implements ABCD simulation, Touchstone I/O, metrics and plotting.
`tools/build_kicad.py` generates the circuit and two boards using KiCad 9 Python.
`build.ps1` performs sequential CAD generation, checks, exports, tests, simulation
and report generation. `tools/make_report.py` consumes current metrics and CAD
previews; it does not synthesize measured data.

Hardware geometry is currently coded in the CAD generator, with corresponding
electrical lengths in `design.json`. Changes must update both and rerun checks.
The through board intentionally has no separate schematic; its simple direct
connection is checked with board DRC. The filter has schematic parity checking.

`measurements/` contains user-acquired raw data and metadata; generated results
live under `results/`. Fabrication artifacts are generated, not hand-edited.
Physical measurement is a separate project stage and remains pending.
