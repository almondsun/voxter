# Voxter

Voxter is a real-time visuomotor policy agent for Geometry Dash. The project
goal is to learn transferable gameplay behavior from screen observations and
recent action history, not to replay fixed click timestamps for one level.

The current theory source of truth is:

- `research/model-theory/voxter-v1.tex`
- `research/model-theory/voxter-v1.pdf`

Those documents define the observation and action contracts, dataset alignment
rules, model stages, evaluation protocol, runtime constraints, and expected
failure modes. Implementation folders should preserve those contracts as code is
added.

## Repository Structure

```text
assets/
  geometry-dash/
    levels/              Geometry Dash level assets used for training or tests.
configs/                 Versioned configuration files for capture, training,
                         evaluation, and runtime deployment.
data/
  raw/                    Immutable capture outputs and source logs.
  processed/              Derived frames, aligned labels, and preprocessing
                         outputs that can be regenerated from raw data.
  datasets/               Stable dataset manifests and splits consumed by
                         training and evaluation.
research/
  model-theory/           Mathematical and project-contract documentation.
src/
  voxter/
    capture/              Frame capture, input-state logging, timing metadata.
    preprocessing/        Frame transforms, normalization, stacks, alignment.
    policy/               Model definitions and policy inference contracts.
    training/             Behavioral cloning and reinforcement training flows.
    evaluation/           Offline, online, and transfer evaluation metrics.
    runtime/              Real-time control loop orchestration.
    control/              OS/game input execution and action-state application.
tests/
  unit/                   Focused tests for pure logic and module contracts.
  integration/            End-to-end tests across capture, data, model, and
                         runtime boundaries.
tools/                    Developer and operational scripts.
```

## Core Contracts

Voxter acts from visual observations and prior action history. The deployed
policy must not use future frames, fixed timestamp scripts, symbolic level
representations, or privileged game state as model input for the main real-time
claim.

The action representation is binary held state:

- `0`: input released
- `1`: input held

Press and release events are derived transitions, not primary labels.

Dataset construction must maintain causal alignment. A training label for an
observation must represent an action that could be chosen from information
available at or before that observation. Any system-delay offset must be
measured, documented, and applied consistently.

Real-time deployment must satisfy the control-cycle budget:

```text
capture + preprocess + inference + input <= tick interval
```

For 60 Hz this interval is about 16.67 ms. For 120 Hz it is about 8.33 ms.

## Implementation Boundaries

`src/voxter/capture` owns external screen and input logging side effects.

`src/voxter/preprocessing` owns deterministic conversion from raw captured data
to model observations and aligned labels.

`src/voxter/policy` owns model architecture and inference semantics. It should
not know how frames are captured or how input is physically applied.

`src/voxter/training` owns optimization workflows, dataset loading for training,
and stage-specific learning objectives.

`src/voxter/evaluation` owns metrics and benchmark protocols. Offline metrics
are necessary but not sufficient; online gameplay evaluation is the real
behavioral test.

`src/voxter/runtime` owns the real-time loop that sequences capture,
preprocessing, policy inference, thresholding, input application, and logging.

`src/voxter/control` owns the adapter that converts held/released actions into
the actual game or OS input state.

## Data Boundaries

Raw captures belong in `data/raw` and should be treated as immutable once
recorded.

Processed artifacts belong in `data/processed` and should be reproducible from
raw inputs plus configuration.

Training-ready manifests, sequence windows, and train/test splits belong in
`data/datasets`. Splits should be made by trajectories, sections, seeds, or
section families instead of random individual frames.

## Validation Expectations

As implementation is added, changes should use repository-native commands when
available. Until build and test tooling exists, documentation-only changes can
be validated with structural checks such as Markdown linting when available and
basic file inspection.

Generated code and vendored third-party code are not currently part of this
repository structure.
