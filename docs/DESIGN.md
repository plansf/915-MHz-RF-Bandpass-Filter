# Design rationale and limitations

## Circuit

```text
J1 center -- C1 1.8pF -- L1 15nH --+-- L3 15nH -- C3 1.8pF -- J2 center
                                |
                        +-------+-------+
                        |               |
                      L2 1.8nH       C2 10pF
                        |               |
                        +------ GND ----+
J1 shield ------------------------------------------------ J2 shield
```

The two series LC arms and parallel shunt LC branch form a three-resonator
bandpass topology. A series resonator conducts near resonance; a parallel
resonator presents a high impedance near resonance. Far from the pass region,
the series arms impede transmission and the shunt branch loads the signal.
All components are passive and nonpolarized. The network uses 50-ohm ports.

For an ideal resonator, f0=1/(2*pi*sqrt(L*C)). At 915 MHz, one ideal resonant
pair would be 15 nH with approximately 2.02 pF, and another 1.8 nH with about
16.8 pF. These are resonance calculations, not an impedance-matched complete
filter synthesis. The selected BOM is adjusted for estimated trace, package
and ground-return effects; it does not use those ideal pair values.

**Important model dependence:** the ideal, parasitic-free version of the selected
BOM fails the return-loss target. It is plotted openly alongside the estimated
board model. This discrepancy demonstrates how strongly this design depends on
its parasitics. The nominal result is a first-prototype prediction, not an EM
validated design or measured proof of matching. Allow a board revision or tuning.

## Model and equations

`rf915.py` cascades ABCD matrices of series impedances, shunt admittances and
transmission lines, then converts to 50-ohm S-parameters. For M=[A B; C D],
den=A+B/Z0+C*Z0+D, S21=2/den, S11=(A+B/Z0-C*Z0-D)/den.
Tests compare the ideal cascade with an independent nodal solution, as well
as checking reciprocity, passivity and a matched line's phase delay.

Inductors use Coilcraft's 0603HP typical frequency-dependent model:

`ZL = R2 + ((k*sqrt(f) + j*2*pi*f*L) || (R1 + 1/(j*2*pi*f*Cp)))`.

The parameter table is transcribed from the linked manufacturer model. Frequency
is in Hz and Cp is converted from pF. Capacitors use an **assumed**, non-vendor-
fitted series ESR of 0.08 ohm and ESL of 0.2 nH. SMA launches use an assumed
0.4 nH series inductance and 0.12 pF shunt capacitance per port. The center node
has an assumed 0.15 pF pad capacitance. Each shunt return uses 0.15 nH nominal.
None of these PCB/connector/capacitor values has been extracted by EM or measurement.

Approximate line sections mirror routed pad-center distances:

| Segment, each side unless noted | Length mm | Model impedance |
|---|---:|---:|
| SMA to narrow feed transition | 8.42 | 50 ohm |
| Narrow feed to series capacitor | 1.10 | 93 ohm |
| Series capacitor to series inductor | 1.2325 | 93 ohm |
| Series inductor to center junction | 1.7125 | 93 ohm |
| Center to L2 signal pad | 0.5125 | 93 ohm |
| Center to C2 signal pad | 1.02 | 93 ohm |

Effective permittivity is assumed 3.1 for wide lines and 2.9 for narrow lines.
Line attenuation is an assumed constant 8 dB/m, not a frequency-dependent FR4
material fit. Pad-center line lengths and lumped pad/launch values are an
approximation and may double-count some field effects. Coupling, radiation,
ground current distribution, actual laminate/soldermask properties, connector
pin stubs and solder fillets are not solved. Stopband depth is especially
optimistic if direct electromagnetic input-to-output coupling dominates.

## PCB choices

The board is 40 x 24 mm, two layers, 0.8 mm FR4, 35 um copper. The bottom layer
is ground with the required signal-pin clearances. Top ground stays outside
the signal corridor. Short shunt returns use paired vias; stitching vias tie
the ground layers. 1.5 mm feeds are approximately 50 ohms under an assumed
relative permittivity of 4.3; this is not a controlled-impedance fabrication
guarantee. The thin PCB keeps the shunt return short. A default 1.6 mm board
would materially change the design and must not be substituted unchanged.

0402 capacitors reduce package size, while 0603 inductors provide a documented
RF model and manageable assembly. Adjacent inductors can still couple; the
model omits that coupling. Vertical Amphenol 132134 SMA connectors avoid an
edge-launch connector's board-thickness-specific landing geometry. They still
introduce RF discontinuities and require mechanical support on a thin board.

The separate through coupon shares connector spacing, PCB stack and feed width,
but its signal geometry differs. It diagnoses fixtures; dividing filter S21
by through S21 does **not** rigorously de-embed both two-port launches.

## Sensitivity and acceptance

The shipped sweep uses 300 reproducible independent uniform samples: each
inductor +/-5%, C1/C3 +/-0.1 pF, C2 +/-0.5 pF, and a shared shunt ground-return
inductance spanning 0.05-0.35 nH. This is illustrative sensitivity, **not a
manufacturing yield estimate**. It omits several uncertainties listed above.
Results and their exact values are in `results/simulation/metrics.json`.

Targets are maximum 3 dB insertion loss and minimum 10 dB input return loss
throughout 902-928 MHz, with at least 15 dB attenuation at 433 and 1830 MHz.
No claim is made about regulatory compliance, transmit power, noise figure,
temperature stability or narrow-channel rejection. The hardware remains unbuilt.
