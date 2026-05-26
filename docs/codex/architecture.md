# Architecture

Voxter is a real-time visuomotor policy agent. The architecture must preserve
the project claim: the deployed policy acts from captured visual observations,
previous actions, and its own memory, not from timestamp scripts or privileged
future information.

## Source Of Truth

The theory source is `research/model-theory/voxter-v1.tex`.

Architecture decisions must preserve these principles:

- visual causality
- binary held-state action representation
- domain-randomized training
- real-time deployment
- separation between model input and diagnostic metadata

## Top-Level Boundaries

`assets/` contains environment inputs such as Geometry Dash level files. Assets
may configure data collection or evaluation, but must not become direct policy
scripts for the main real-time claim.

`configs/` contains versioned settings for capture, preprocessing, datasets,
training, evaluation, and runtime. Timing-sensitive values belong in config, not
hidden constants.

`data/` contains capture outputs, derived artifacts, and dataset manifests.
Raw data is immutable. Processed data is reproducible.

`research/` contains theory, experiment design, and non-runtime analysis.

`src/voxter/` contains implementation code.

`tests/` mirrors implementation boundaries with unit and integration tests.

`tools/` contains CLI scripts and operational helpers.

## Package Boundaries

`capture` owns screen capture, input logging, timestamps, calibration, and raw
capture writes. It is an external side-effect boundary.

`preprocessing` owns deterministic conversion from raw frames and logs to model
observations, frame stacks, aligned labels, and cleaned gameplay segments.

`policy` owns model architecture and inference semantics. It must not capture
frames, mutate datasets, or apply OS input.

`training` owns optimization workflows: behavioral cloning, sequential
behavioral cloning, reinforcement fine-tuning, checkpointing, and training
metrics.

`evaluation` owns offline metrics, online metrics, transfer benchmarks, and
runtime log analysis.

`runtime` owns the deployed loop that sequences capture, preprocessing, policy
inference, thresholding, input application, and logging.

`control` owns physical or OS-level input execution for the binary held state.

## Dependency Direction

Prefer this dependency direction:

```text
tools
  -> training, evaluation, runtime
runtime
  -> capture, preprocessing, policy, control
training
  -> preprocessing, policy, evaluation
evaluation
  -> preprocessing, policy
preprocessing
  -> shared data contracts
capture/control
  -> platform adapters
policy
  -> shared model contracts
```

Avoid reverse dependencies from core policy code into capture, control, runtime,
or tools.

## Core Contracts

The primary action is binary held state:

- `0`: released
- `1`: held

Click, press, and release events are derived transitions.

The model input may include:

- captured frames
- preprocessed frames
- previous actions
- recurrent state computed from past observations

The main deployed policy must not receive:

- future frames
- timestamp scripts
- complete symbolic level definitions
- exact future obstacle positions unavailable visually
- privileged metadata such as section ID, seed, progress, or mode labels

Metadata may be used for diagnostics, balancing, rewards, and evaluation when
kept out of the policy input path.

## Side Effects

Side effects belong at explicit boundaries:

- screen and input logging: `capture`
- physical input application: `control`
- file writes for artifacts: `tools`, `training`, `evaluation`, or clearly named
  adapters
- live gameplay orchestration: `runtime`

Preprocessing, metric calculations, action transition extraction, and dataset
split validation should be pure or close to pure.

## Error Model

Use explicit exceptions with actionable messages in Python. Do not silently
discard bad frames, corrupt metadata, failed input application, or missed
deadlines.

When a subsystem can partially recover, return structured status or raise a
specific exception at the boundary. Do not hide fallback behavior unless it is
documented and safe.

## Compatibility Rules

Treat dataset schemas, config keys, checkpoint metadata, CLI output consumed by
other tools, and runtime log formats as contracts. If one changes:

- document the compatibility impact
- add or update migration notes when needed
- update tests or validators
- call out the change in the final report
