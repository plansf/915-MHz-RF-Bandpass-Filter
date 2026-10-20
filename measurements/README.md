# Physical measurement folder

No measurements have been acquired. Do not copy simulated results here as evidence.

Save NanoVNA Touchstone 1.x S2P files here, with one completed metadata JSON per
measurement. Preserve originals. Name revisions clearly, e.g. `A01-before.s2p`,
`A01-after-C2-9p1.s2p`. Use the unmodified metadata template as a starting point.
The CLI requires populated instrument, date, calibration, reference plane, board
revision and operator fields when using `--kind measured`.

Most NanoVNAs measure forward S11/S21 only in one connection. The exporter can
fill S12/S22 with placeholders or estimates. Do not claim they were measured.
To measure the opposite direction, reverse the DUT and save a separate sweep;
record which physical connector was connected to CH0.
