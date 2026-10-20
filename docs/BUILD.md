# Order, assemble and inspect

## Order files and settings

Upload `fabrication/rf915-revA-gerbers.zip` for the filter and
`fabrication/rf915-thru-revA-gerbers.zip` for the reference. They are separate
boards, each 40 x 24 mm. Select **2 layers, 0.8 mm finished thickness, FR4,
1 oz / 35 um copper**, plated through holes, soldermask both sides and top
silkscreen. ENIG is a reasonable flat finish for these small pads. Ask for
the actual stackup and laminate data and retain them with your measurements.
No impedance-control coupon or production RF qualification is included.

Review the fabricator's preview: one closed rectangle, matching top/bottom
copper and drill alignment, two five-pin SMA locations, continuous bottom
ground except signal clearances. Keep this first order a small prototype batch.
Do not permit an automatic change to 1.6 mm thickness. No board order has been
placed and current prices/stock have not been verified.

## Parts and equipment

`hardware/BOM.csv` gives exact nominal parts. One filter plus one reference
needs four Amphenol 132134 standard female SMA connectors. Do not substitute
RP-SMA, edge-launch SMA or an arbitrary connector footprint. The vendor drawing
is linked in `SOURCES.md`; the named KiCad footprint places four ground leads
on a 5.08 mm square around the signal pin. Inspect actual parts against that
pattern before soldering.

For rework, obtain extra nominal parts (for example, ten of each capacitor,
five of each inductor) and optional high-Q C0G 0402 tuning capacitors near
1.8 pF and 10 pF. Suggested exploratory values: 1.5, 1.6, 1.7, 1.9, 2.0,
2.2 pF for C1/C3; 8.2, 9.1, 11 and 12 pF for C2. These are tuning options,
not validated substitutions. Retain the same component family where possible.
Changing inductor family invalidates the specific vendor model.

You already have a NanoVNA and soldering equipment. Also prepare magnification,
fine tweezers, suitable flux, a DMM, two short SMA cables, and a compatible
open/short/50-ohm load/through calibration kit. Confirm cable and adapter genders.
0402 parts are small; practice on a spare board if needed.

## Assembly sequence

1. Photograph the bare board; label board serial and revision in the log.
2. Compare footprint positions with `results/cad/rf915-top.svg` and the BOM.
   C1/C3 are the outer series capacitors, L1/L3 the inner series inductors;
   C2 and L2 are the two shunt branches. All are nonpolarized.
3. Solder C2 and L2 first, then L1/L3 and C1/C3. Use minimal solder and
   follow each manufacturer's soldering limits. Inspect for tombstones,
   pad bridges and unintended solder on the nearby ground vias.
4. Install the vertical SMA connectors from the top; solder all ground pins
   and the center pin. Support the body during soldering. Trim protruding
   leads without stressing joints, then inspect the underside for shorts.
5. Populate the through board with its two SMA connectors only.
6. Clean residue using a method compatible with the components, dry and inspect.
   Photograph both sides. Support the board while attaching cables; do not
   use it as a lever or wrench against a tightened connector.

## DMM checks before RF testing

Both connector shields and all ground vias should have near-zero resistance
between them. On the **filter**, each port center to ground should be DC open
(allow capacitor charging); port-center to port-center should also be open.
The MID node is intentionally DC-connected to ground through L2, so continuity
there is expected. On the **through board**, the two center pins should have
continuity to one another, and neither should be shorted to ground.

This is an unpowered passive network. Connect directly to the low-level VNA
test ports; no external RF source, amplifier or DC supply is needed.

## If it needs tuning

First check calibration with the through board, connector type, component
values and soldering. Save the initial result before making changes. Change
one variable at a time and log the actual installed values. Increasing a
resonator's capacitance generally lowers its resonance, but this full network's
match is coupled; use a fresh simulation and measurement to decide each step.
Keep C1/C3 paired for initial experiments. Do not stack arbitrary capacitors
or leave long jumper wires at RF. If no small adjustment achieves the target,
use the measured evidence to revise the layout/model and produce Rev B.
