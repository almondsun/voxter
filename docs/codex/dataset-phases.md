# Dataset Collection Phases

This document defines Voxter dataset collection phases. These phases describe
what gameplay data means and how it should be used. They are separate from the
model training stages in `training-and-evaluation.md`.

The current policy action space is binary held state:

- `0`: released
- `1`: held

Raw press and release events are recorded for timing reconstruction, but the
primary training label remains held state.

## Shared Acceptance Rules

Every recorded gameplay run must keep enough evidence to audit alignment:

- `frames.jsonl`
- `input_events.jsonl`
- `terminal_events.jsonl`
- `capture_summary.json`
- `preview.mp4`

For Stage 1 materialization, each accepted raw run should also have:

- `stage1_manifest.jsonl`
- `dataset_summary.json`
- `acceptance.json`

For the current capture pipeline, a clean accepted run must satisfy:

- both binary action states are present
- frame timestamps are monotonic
- input-event timestamps are monotonic
- action-sample timestamps are monotonic
- frame timestamps are greater than or equal to action-sample timestamps
- zero frame/action synchronization mismatches at action-sample timestamps
- zero dropped frames
- zero missing frame files
- valid `preview.mp4`

Manual numpad `+` terminal markers represent death or reset. Stage 1
materialization removes a configurable window around each marker. The current
defaults are:

- `death_tail_s = 0.35`
- `reset_skip_s = 1.5`

The preview must show action state and terminal events. Frames removed by the
terminal-window cleaner should be tinted red in the preview so the rejected
region can be checked visually.

## Phase 0: Tooling And Contract Smoke

Phase 0 exists only to prove that capture, event logging, preview generation,
preprocessing, and acceptance tooling work end to end.

Phase 0 data is not training data. It may include very short captures, bad
gameplay, portal experiments, and intentionally small smoke-test outputs. Once
Phase A begins, Phase 0 runs should not be mixed into training splits.

## Phase A: Stable Baseline Demonstrations

Phase A is the first real behavior-cloning dataset. It records human gameplay on
the training level under stable, non-randomized conditions:

- Ghost Mode: off
- Speed: normal
- action key: W
- terminal/death marker: numpad `+`
- capture: 60 Hz target
- observation: grayscale `640x360`
- frame stack: 4 frames, oldest to newest

Phase A is meant to answer a narrow question:

> Can a Stage 1 frame-stack policy learn the basic visual-to-held-action mapping
> on stable training-level gameplay?

Phase A should be used for:

- data-loader and trainer smoke tests
- first reactive CNN plus frame-stack baseline
- class-imbalance checks
- transition metric implementation
- preview-based audit of terminal cleaning
- first online sanity deployment only after offline behavior is plausible

Phase A should not be treated as evidence of generator robustness or standard
level transfer. It intentionally avoids Ghost Mode variation, speed variation,
and randomization so the first training failure modes are easier to isolate.

### Current Phase A Batch

The first serious Phase A batch is:

- raw prefix: `data/raw/phase-a-baseline-20260527-*`
- dataset prefix: `data/datasets/phase-a-baseline-20260527-*-stage1`
- accepted runs: 30
- clean Stage 1 samples: 97,275
- held samples: 26,930
- released samples: 70,345
- terminal markers: 107
- terminal discard windows: 107
- split label: `train`
- `delta_sys`: 0

This batch is sufficient for the first serious Stage 1 baseline training run.
It is not sufficient by itself for claims about generalization.

Some runs should be visually reviewed before training reports are treated as
stable, especially runs with many terminal markers or softer effective frame
rate. Current preview-review candidates include:

- `phase-a-baseline-20260527-0014`
- `phase-a-baseline-20260527-0019`
- `phase-a-baseline-20260527-0020`
- `phase-a-baseline-20260527-0031`
- `phase-a-baseline-20260527-0032`

## Phase B: Controlled Speed Variation

Phase B introduces one controlled domain variable at a time: speed.

Recommended order:

1. `1.1x`
2. `1.25x`
3. `1.33x`
4. `1.5x`
5. `1.68x`
6. `2x`
7. random speed

Each speed condition should be recorded as separate trajectories with explicit
metadata. Do not merge Phase B into Phase A silently. Phase B is for testing
whether a policy trained on stable normal-speed gameplay can adapt to timing
changes and whether speed metadata should remain diagnostic or become an
ablation input.

For first use, Phase B should be held out from Phase A training and used as an
evaluation set. It can later be added to training as a domain-randomization
dataset once Phase A learning is confirmed.

## Phase C: Controlled Ghost Mode Variation

Phase C introduces Ghost Mode while keeping speed controlled.

Recommended conditions:

- off
- in
- out
- in and out
- random

Ghost Mode changes visual ambiguity. Phase C is not just more data; it tests
whether the visual policy can handle less reliable obstacle visibility. Keep
Ghost Mode metadata diagnostic unless a deliberate privileged-input ablation is
being run.

For first use, Phase C should be evaluated separately from Phase A. It should
not be mixed into Phase A training until the baseline model has clear transition
metrics and online sanity results.

## Phase D: Combined Randomization

Phase D combines speed and Ghost Mode variation. It is the first broad
generator-style dataset phase.

Phase D should only start after:

- Phase A has trained a working Stage 1 baseline
- transition metrics exist
- preview audit has found no systematic terminal-marker issue
- training code records dataset IDs and preprocessing metadata

Phase D data should be split by trajectory or generated section identity, not by
random individual frames. The main purpose is robustness, not just sample count.

## Phase E: Held-Out Generator Evaluation

Phase E contains runs from generator settings, sections, seeds, or section
families that are not used for training.

Phase E is evaluation data. Do not train on it when reporting generalization.
It should support:

- per-section metrics
- per-mode metrics
- per-speed metrics
- per-Ghost-Mode metrics
- death-location analysis
- transition timing analysis

The strongest generator evidence comes from section-level separation where
training and evaluation section identities do not overlap.

## Phase F: Online Agent Rollouts

Phase F records the agent, not the human demonstrator.

This phase is for online evaluation, behavioral-cloning failure analysis,
DAgger-like data collection, or later reinforcement learning. Phase F must be
kept separate from human demonstration data because it comes from the agent's
own state distribution.

Useful Phase F metadata includes:

- model checkpoint ID
- training dataset IDs
- action threshold
- runtime latency summary
- inference deadline misses
- survival time
- progress
- death location
- whether human intervention occurred

Phase F data may become training data only under a deliberate algorithmic
choice, such as imitation correction, DAgger, or reinforcement learning. It
should not be silently mixed into Phase A behavior cloning.

## Practical Progression

The intended progression is:

1. complete Phase 0 tooling smoke
2. collect Phase A stable baseline demonstrations
3. train and evaluate the first Stage 1 baseline
4. collect Phase B and Phase C as controlled holdouts
5. train with selected controlled variation if Phase A works
6. collect Phase D combined-randomization data
7. reserve Phase E for held-out generator evaluation
8. use Phase F for online rollout analysis and later self-improvement methods

Each phase should preserve its own dataset identity. Mixing phases is allowed
only when the training configuration records exactly which phases and run IDs
were used.
