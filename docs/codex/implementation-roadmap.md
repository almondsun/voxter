# Implementation Roadmap

This roadmap follows the first-version plan in the model-theory document. Build
the project in stages that preserve causal correctness and real-time constraints.

## Stage 0: Project Tooling

Add the minimum package and validation structure:

- Python package metadata
- test runner
- linter and formatter
- type checker, if practical
- configuration format
- logging conventions

Update `docs/codex/build-and-test.md` once commands are canonical.

## Stage 1: Capture And Logging

Implement:

- frame capture into `frames.jsonl`
- high-resolution input event logging into `input_events.jsonl`
- binary held-state reconstruction from input events
- timestamps or game-tick indexes
- run and attempt identifiers
- raw manifest writing
- system-delay calibration script
- an explicit offline/debug capture backend before real-time runtime capture
- a persistent PipeWire/GStreamer backend for real-time raw recording

Validation:

- manifest schema tests
- timestamp monotonicity checks
- held-state transition extraction tests
- repeat-event filtering tests
- frame-sampled transition loss summary
- PipeWire backend smoke test when a desktop session is available
- calibration fixture or mocked timing test

## Stage 2: Preprocessing And Dataset Manifests

Implement:

- system-delay calibration reports over candidate `delta_sys` values
- runtime-shaped latency benchmark with capture/preprocess/policy/control stubs
- crop and resize
- grayscale and normalization
- frame-stack construction
- label alignment by measured `delta_sys`
- death/reset segment removal
- processed manifest generation
- split definitions by trajectory, section, seed, or section family

Validation:

- calibration sign and scoring tests
- runtime deadline accounting tests
- shape and dtype tests
- alignment sign tests
- sequence-window tests
- split-leakage tests

## Stage 3: Stage 1 Policy

Implement:

- CNN encoder
- binary held-state head
- weighted binary cross-entropy
- training config
- checkpoint metadata
- offline evaluation metrics

Validation:

- model construction and inference shape tests
- tiny training-step smoke test
- metric tests for imbalanced action sequences
- checkpoint metadata test

## Stage 4: Runtime Sanity Loop

Implement:

- runtime loop using capture, preprocessing, policy, and control boundaries
- thresholding
- optional hysteresis
- deadline accounting
- runtime logs
- fail-safe behavior

Validation:

- mocked runtime integration test
- threshold and hysteresis tests
- deadline miss behavior tests
- live smoke test only when the game environment is available

## Stage 5: Stage 2 Sequential Policy

Implement:

- recurrent policy, initially GRU
- previous-action input
- contiguous sequence-window loading
- truncated backpropagation through time
- warm-up behavior if used

Validation:

- sequence ordering tests
- hidden-state reset and warm-up tests
- recurrent inference shape tests
- online evaluation against Stage 1

## Stage 6: Evaluation Benchmarks

Implement:

- training-generator evaluation
- held-out-generator evaluation
- standard-level transfer evaluation
- transition timing metrics
- death-location analysis
- latency report summaries
- baseline comparisons

Validation:

- metric edge-case tests
- report fixture tests
- baseline sanity tests

## Stage 7: Reinforcement Fine-Tuning

Implement:

- environment-like wrapper
- reward computation
- terminal and reset handling
- imitation or KL regularization
- rollout logging
- safety limits for live control

Validation:

- reward unit tests
- terminal/reset tests
- mocked rollout tests
- regression tests against reward hacking cases when discovered

## Stage 8: Ablations And Hardening

Study:

- frame-stack length
- input resolution
- grayscale versus color
- icon standardization
- GRU versus LSTM or Transformer
- threshold and hysteresis settings
- Ghost Mode robustness
- class weighting and sampler choices

Each ablation must record dataset version, config, checkpoint metadata, and
evaluation conditions.
