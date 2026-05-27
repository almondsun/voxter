# Data And Datasets

The dataset contract is central to Voxter. The model should learn actions that
could be chosen from available visual information, not labels leaked from future
frames or misaligned logs.

## Directory Contract

`data/raw/` stores accepted capture outputs and source logs. Treat these as
immutable.

`data/processed/` stores reproducible artifacts derived from raw captures.

`data/datasets/` stores manifests, split definitions, sequence-window indexes,
and stable dataset metadata consumed by training and evaluation.

## Raw Capture Streams

Raw capture uses two synchronized streams:

- `frames.jsonl` records captured frame paths, frame timestamps, frame indexes,
  monitor geometry, capture timing, the sampled held state, and the timestamp at
  which that held state was sampled. It also records encoded frame dimensions,
  source dimensions, image format, and whether the capture backend resized the
  frame before writing it.
- `input_events.jsonl` records high-resolution input events such as press,
  release, and repeat events from the OS input device.

Input events are the source of truth for press/release transitions. Frame rows
may include sampled held state for convenience, debugging, and quick validation,
but preprocessing should be able to reconstruct aligned labels from the input
event stream so short taps between frame samples are not lost.

Frame and input-event timestamps must be in the same clock domain. Durations and
deadline measurements may use monotonic clocks, but persisted synchronization
timestamps must be comparable across streams.

## Raw Frame Records

At minimum, a raw frame record must preserve:

- raw frame payload or raw frame path
- binary held-state input sampled at the frame timestamp
- frame timestamp or game-tick index
- encoded frame dimensions
- source capture dimensions
- image format
- whether capture-side resizing was applied
- run identifier
- attempt identifier when available
- frame index inside the run or attempt

At minimum, a raw input event record must preserve:

- event timestamp
- event device identity
- key code
- event kind: press, release, or repeat
- binary held-state after the event
- run identifier
- attempt identifier when available

Useful optional metadata:

- alive state
- done or terminal state
- progress
- section ID
- gameplay mode
- speed
- Ghost Mode condition
- random seed
- notes

Optional metadata is not automatically valid model input. Keep policy input and
diagnostic metadata separate.

## Primary Action Label

The dataset label is binary held state:

- `0`: released
- `1`: held

Press and release labels are derived:

```text
press_t = action_{t-1} == 0 and action_t == 1
release_t = action_{t-1} == 1 and action_t == 0
```

Do not train the primary policy on click timestamps when the contract calls for
held-state control.

Raw press and release events are still recorded because they preserve timing
information that frame sampling can miss. They are used to reconstruct the
held-state label timeline; they are not the primary model target by themselves.

## Causal Alignment

A training label assigned to an observation must correspond to an action chosen
from information available at or before that observation.

The theory document defines `delta_sys` so that a positive value means the
action log lags behind the visual frame. Under that convention:

```text
label_t = action_log_{t + delta_sys}
```

If implementation code uses the opposite sign convention internally, it must
translate before reporting or persisting `delta_sys`.

Samples outside the valid aligned range must be discarded or explicitly padded
according to the dataset contract.

## Preprocessing Outputs

Preprocessing may produce:

- cropped frames, if stable UI removal is needed
- resized frames
- grayscale frames
- normalized arrays
- icon-standardized frames, if implemented reliably
- frame stacks
- aligned labels
- valid gameplay prefixes

Preprocessing must not add future information, hand-coded level scripts, or
privileged labels to the policy input.

## Death And Reset Handling

Keep useful gameplay prefixes from failed attempts. Remove:

- death aftermath
- reset screens
- menus
- idle periods
- clearly invalid control segments

If a prefix truncation window is used before death, make the value configurable
and record it in the processed artifact metadata.

## Splits

Do not split by random individual frames. That leaks trajectory and section
context.

Prefer splits by:

- trajectory
- attempt
- section
- section family
- random seed

The strongest generator test is section-level separation where training and test
section identities do not overlap.

## Balancing

Action classes may be imbalanced. Do not force unrealistic equal class counts by
default. Prefer:

- weighted binary cross-entropy
- sequence-level sampling
- mode-aware or section-aware sampling when metadata is available
- per-mode metric reporting

Any sampler that changes the training distribution should be documented in the
dataset or training config.

## Manifest Expectations

A dataset manifest should include enough information to reproduce samples:

- sample ID
- run ID
- attempt ID
- frame index
- timestamp
- raw frame path
- processed frame path, when applicable
- action held
- alive
- done
- optional section ID
- optional mode
- optional speed
- optional Ghost Mode
- optional progress
- preprocessing config identity
- alignment offset
- split name

Use explicit schema versioning once manifests are consumed by multiple tools.

## Current Stage 1 Dataset Slice

`stage1-manifest-v1` is the first materialized behavior-cloning dataset
manifest. Each row points to:

- one raw PGM/gray8 frame path
- one `observation-v1` grayscale payload
- one `frame-stack-v1` payload in oldest-to-newest `khw` order
- one binary held-state label reconstructed from `input_events.jsonl`
- the persisted `delta_sys` value and split name

Frame stacks reset at run/attempt boundaries. Warm-up repeats the first
observation in an attempt, so no sample uses future frames or frames from a
previous attempt.

`dataset_summary.json` uses `stage1-dataset-summary-v1` and records sample
counts, class counts, weighted-BCE class weights, observation metadata, stack
metadata, split name, and alignment offset. Missing classes receive a `null`
weight rather than an artificial infinite or silently guessed value.

When `terminal_events.jsonl` is present, Stage 1 materialization treats those
events as manual death/reset markers for dataset cleaning. It discards a
configurable window before and after each marker, records the configured
`death_tail_s` and `reset_skip_s` values in `dataset_summary.json`, and resets
frame-stack state after discarded windows. Terminal metadata is diagnostic and
must not be passed to the policy input.
