# Geometry Dash Assets

This folder contains Geometry Dash-specific assets used by Voxter.

`levels/` stores level files used as training generators, held-out generator
cases, or evaluation fixtures. Level assets should be treated as environment
inputs, not as privileged model inputs. The main Voxter claim requires the policy
to act from captured screen observations and previous action history.
