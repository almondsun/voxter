# Capture

Capture code owns screen acquisition, input-state logging, timestamps, and
system-delay calibration.

This module is allowed to perform external side effects such as reading the
screen, observing input state, writing capture logs, and measuring latency.
Keep those side effects out of preprocessing, policy, and evaluation code.

Capture outputs should support causal dataset construction:

- raw frame or raw frame path
- binary held-state input
- timestamp or game-tick index
- run and attempt identity
- optional metadata for analysis and evaluation

System-level delay must be measured and represented explicitly. A positive
model-theory `delta_sys` means the action log lags behind the visual frame, so
labels are taken from a later log index after correction.
