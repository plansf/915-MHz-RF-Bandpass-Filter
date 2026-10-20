# Maintenance and validation

Use Python 3.11+ for analysis and KiCad's bundled Python for CAD. Avoid coupling
analysis imports to pcbnew. Preserve 50-ohm reference and Touchstone pair ordering
(S11, S21, S12, S22). Reject unsupported formats instead of guessing. Preserve
raw data, label simulation explicitly, and retain unknown results for missing
frequency coverage. No metric should imply physical evidence from simulation.

Run `python -m unittest discover -s tests -v` after changes to the circuit model,
parser or metrics. Run `build.ps1` after hardware/config changes. DRC/ERC errors
must be resolved, not excluded to force a clean report. Inspect new CAD previews.
Report metadata must distinguish forward-only acquisition from full two-port
measurement. Update README and design/measurement docs with changed behavior.
