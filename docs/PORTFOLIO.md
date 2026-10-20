# Portfolio evidence and learning plan

## Current truthful project summary

"Developed a 915 MHz passive LC filter prototype design with a routed two-layer
KiCad PCB, a through reference coupon, a Python S-parameter model, and a
Touchstone analysis workflow. Checked electrical connectivity and PCB design
rules and evaluated sensitivity to component and ground-return variation.
Physical assembly and NanoVNA validation are pending."

This package was generated with AI assistance. Learn and verify the design
before claiming independent engineering ownership. Do not describe the included
simulated traces as measured performance or claim you have fabricated the PCB.

## Four practical milestones

1. **Understand and reproduce:** derive series/shunt ABCD matrices, run the
   tests, explain return loss versus insertion loss, and reproduce the plots.
2. **Build:** inspect fabrication data, order parts/boards, assemble one filter
   and one reference, photograph soldering and document continuity checks.
3. **Measure and diagnose:** calibrate, export raw S11/S21, compare with the
   model, repeat connections and quantify any instrument limitations.
4. **Improve and explain:** tune a documented variable or make Rev B; explain
   what disagreed, what you changed and what evidence supports the conclusion.

## Final case study outline

- Problem: characterize a practical RF filter around 915 MHz using accessible tools.
- Requirements: passband and stopband table, instrument range and PCB constraints.
- Decisions: LC topology, stackup, ground return, part selection and model limits.
- Evidence: schematic, layout, assembly photos, raw Touchstone files and calibration.
- Results: fill measured values, show before/after tuning with identical axes.
- Reflection: uncertainty, failed assumptions and the next design revision.

After measurement, a resume bullet can use this structure:
"Designed and assembled a [verified topology] RF filter; measured [actual IL]
dB insertion loss and [actual RL] dB return loss across [actual frequency band]
using a calibrated [instrument], and automated Touchstone analysis in Python."
Replace every bracket with evidence or omit the uncompleted claim.

Interview topics: why a 1 nH interconnect matters at 915 MHz; why a capacitor's
package changes its RF impedance; what the VNA calibration reference plane is;
why through subtraction is not full de-embedding; and how your data changed
your original design assumptions.
