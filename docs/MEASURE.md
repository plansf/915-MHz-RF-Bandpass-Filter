# NanoVNA measurement procedure

## Confirm the instrument

Record model, firmware, rated usable frequency range, serial if available and
calibration kit. The exact NanoVNA model is not yet known. Confirm that it can
reliably characterize 902-928 MHz; some versions have limitations near this
range. Measure 1830 MHz only if the model supports it. A display that accepts
a frequency is not by itself proof of useful accuracy there.

NanoVNA-Saver can export Touchstone data; use the version compatible with your
instrument. USB control varies across firmware, so this project accepts
exported `.s2p` rather than issuing unverified serial commands. See the linked
official project documentation in `SOURCES.md` for installation and operation.

## Calibrate and acquire

1. Allow the instrument to stabilize per its manual. Fit the same short cables
   and adapters you will use on the DUT. Set a passband sweep, e.g. 850-1000 MHz
   with at least 301 points if supported. If limited to 101 points, a narrower
   sweep with sufficient samples inside 902-928 MHz is still useful.
2. Follow your firmware's open/short/load and transmission-through calibration
   procedure. Put the reference planes at the cable ends that attach to the
   board connectors. Include any fixed adapters in this calibration. Save the
   calibration; avoid moving or bending cables afterward.
3. Verify the cable-to-cable through has small insertion loss and low reflection.
   Also acquire the PCB through coupon. Strong ripple, unexplained loss or
   unstable traces require investigation before interpreting the filter.
4. Connect CH0/source to filter J1, CH1/receiver to J2. Acquire complex S11 and
   S21; save Touchstone 1.x `.s2p`, screenshots and settings. Export 50-ohm
   reference data. Retain the unmodified raw export.
5. Repeat with a broad sweep spanning 433 MHz and, if supported, 1830 MHz.
   Calibrate for the changed sweep as the instrument requires. If one broad
   sweep has too few passband points, increase its points/segments or analyze
   the narrow and broad files separately. The script requires at least five
   samples inside the passband and both band edges to be covered.
6. Reconnect and repeat at least three times to estimate connector repeatability.
   A second acquisition with ports swapped can characterize the reverse
   direction. Do not pretend S12/S22 placeholders in a forward-only export
   are measured channels. For a swapped forward acquisition, S11 describes
   the other end of the board; name and document it accordingly.

## Analysis and records

Copy `measurements/metadata-template.json` alongside each `.s2p`. Fill in all
required fields, including the calibration plane, actual parts, sweep and
observations. Keep `measured_channels` as `["S11", "S21"]` unless you actually
assembled a complete four-parameter acquisition with consistent reference planes.

```powershell
python rf915.py analyze measurements/filter-revA.s2p --kind measured --metadata measurements/filter-revA.json --output results/measured-revA --reference results/simulation/nominal.s2p
```

The JSON reports worst passband insertion/return loss, passband ripple, 915 MHz
values and attenuation at the specified stopband points. Stopband values are
interpolated within the sweep only. `overall_pass: null` means coverage is
incomplete, provided no tested criterion failed. To establish every target,
combine the evidence from your qualified sweeps manually in the report; do
not splice traces acquired under different calibrations without documenting it.

The script computes group delay from unwrapped S21 phase. Deep stopband/noisy
points can yield meaningless delay; interpret it in the useful passband only.
It warns about violations of passive power bounds; a warning is not a
calibration certificate. NanoVNA noise/dynamic range can limit stopband claims.

The through board is a diagnostic reference. Plotting it or subtracting its
insertion loss is not full two-port de-embedding. Report the original calibrated
measurement as the primary result. Record temperature, cable changes, board
serial and every component change. Never overwrite the initial baseline.

## Acceptance worksheet

| Criterion | Target | Measured result | Evidence file |
|---|---|---|---|
| Worst IL, 902-928 MHz | <=3 dB | Not measured | Pending |
| Worst input RL, 902-928 MHz | >=10 dB | Not measured | Pending |
| Attenuation, 433 MHz | >=15 dB | Not measured | Pending |
| Attenuation, 1830 MHz | >=15 dB | Not measured / instrument dependent | Pending |
| Three reconnection runs | Report variation | Not measured | Pending |

Missing or instrument-limited evidence stays explicitly unverified. A useful
portfolio result can include a failed first board if the diagnosis and revision
are supported by data.
