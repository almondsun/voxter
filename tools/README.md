# Tools

Developer and operational scripts belong here.

Appropriate tools include:

- capture launchers
- latency calibration helpers
- dataset preparation commands
- manifest validators
- evaluation runners
- report generation scripts
- one-off migration utilities

Scripts should have clear CLI contracts, actionable errors, and stable output
when other tools consume them.

## Manual Capture

`capture_manual_run.py` records an offline/debug raw capture session with two
streams:

- `frames.jsonl`
- `input_events.jsonl`

For the current Geometry Dash setup on monitor 2 with W as the action key:

```bash
python tools/capture_manual_run.py \
  --duration 10 \
  --target-hz 20 \
  --geometry "1920,0 1920x1080" \
  --event-device /dev/input/event5 \
  --output-width 960 \
  --output-height 540
```

The default backend uses `grim`, so it is appropriate for raw data experiments
and diagnostics, not for claiming real-time runtime viability.

For the PipeWire/GStreamer backend, use system Python or a virtual environment
with system site packages so PyGObject is visible:

```bash
python tools/capture_manual_run.py \
  --backend pipewire \
  --duration 5 \
  --target-hz 60 \
  --geometry "1920,0 1920x1080" \
  --event-device /dev/input/event5
```

The portal will ask which screen or window to share. The first implementation
writes JPEG frames by default for practical live captures. Use `--format ppm`
only for short raw diagnostic runs because full-resolution PPM output is large.
PipeWire captures use bounded asynchronous frame writes by default; use
`--sync-writes` only when debugging persistence behavior.

Analyze a completed capture run:

```bash
python tools/analyze_capture_run.py /tmp/voxter-live-5s-jpeg2 \
  --min-input-events 1 \
  --require-both-actions \
  --max-sync-mismatches 0 \
  --max-dropped-frames 0 \
  --max-missing-frame-files 0
```

The analyzer checks binary actions, timestamp monotonicity, frame/action
synchronization at the sampled action timestamp, missing frame files, dropped
frames, missed periods, and frame-interval statistics.

Every completed capture writes `preview.mp4` next to `capture_summary.json` by
default. The preview burns in the current W action state and press/release event
pulses so synchronization can be checked visually after acquisition. Use
`--no-preview` only for diagnostics where MP4 generation is intentionally
skipped.

For clean baseline collection, numpad `+` is the default manual terminal marker:

```bash
python tools/capture_manual_run.py \
  --backend pipewire \
  --format gray8 \
  --duration 60 \
  --target-hz 60 \
  --geometry "1920,0 1920x1080" \
  --event-device /dev/input/event5 \
  --key-code 17 \
  --terminal-key-code 78 \
  --output-width 640 \
  --output-height 360
```

Press numpad `+` once when death or reset occurs. The capture writes
`terminal_events.jsonl`, and the preview shows `TERMINAL: DEATH` on the
corresponding frame.

## Aligned Manifest

`build_aligned_manifest.py` converts one raw capture directory into an
`aligned-manifest-v1` JSONL manifest. Labels are reconstructed from
`input_events.jsonl`; the sampled frame action is kept as raw diagnostic data and
is not treated as the authoritative label source.

```bash
python tools/build_aligned_manifest.py /tmp/voxter-live-10s-async-960x540 \
  --output /tmp/voxter-processed-10s \
  --delta-sys 0 \
  --split unsplit
```

Use the measured system delay for `--delta-sys`. Positive values follow the
project convention `label_t = action_log_{t + delta_sys}`.

Estimate candidate offsets from one raw capture:

```bash
python tools/calibrate_delta_sys.py /tmp/voxter-live-10s-async-960x540 \
  --output /tmp/voxter-processed-10s/delta_sys_calibration.json \
  --min-delta-sys -5 \
  --max-delta-sys 5
```

This report compares sampled frame actions with event-reconstructed held-state
labels. Treat it as log-level evidence; it does not inspect pixels.

## Stage 1 Dataset

`build_stage1_dataset.py` materializes the narrow Stage 1 behavior-cloning
dataset contract from one raw capture directory:

```bash
python tools/build_stage1_dataset.py /tmp/voxter-live-10s-gray8 \
  --output /tmp/voxter-stage1-10s \
  --delta-sys 0 \
  --split train \
  --observation-width 640 \
  --observation-height 360 \
  --frame-stack-length 4
```

The tool writes grayscale observation payloads, binary frame-stack payloads,
`stage1_manifest.jsonl`, and `dataset_summary.json`. It currently requires
PGM/gray8 frame files; encoded JPEG/PNG capture runs must be decoded by a future
adapter before they can be used for Stage 1 training.

If `terminal_events.jsonl` exists, Stage 1 materialization removes terminal
windows using `--death-tail-ms` before each marker and `--reset-skip-ms` after
each marker. The defaults are conservative for early collection: 350 ms before
death and 1500 ms after death/reset.

Validate and record acceptance for a durable Stage 1 dataset:

```bash
python tools/accept_stage1_dataset.py data/raw/<dataset-id> \
  data/datasets/<dataset-id>-stage1
```

The acceptance record is written to `acceptance.json` in the dataset directory.
It checks the raw capture analysis thresholds, manifest/sample counts, binary
action presence, payload existence, payload byte sizes, and first-stack warm-up
semantics.

Smoke-test Stage 1 dataset loading before starting model training:

```bash
python tools/smoke_stage1_data.py data/datasets/phase-a-baseline-20260527-*-stage1 \
  --batch-size 16 \
  --max-batches 4
```

This dependency-free smoke verifies that materialized manifests share one
contract, frame-stack payloads can be batched as `N,K,H,W` byte tensors, labels
are binary, and the batch contract is ready for a later ML-framework adapter.

Run the first tiny Stage 1 optimization smoke after installing the training
extra:

```bash
python -m pip install -e ".[train]"
python tools/smoke_stage1_torch.py data/datasets/phase-a-baseline-20260527-*-stage1 \
  --batch-size 8 \
  --train-steps 3 \
  --device auto
```

This builds a minimal CNN over the `K,H,W` frame-stack contract, runs a few
weighted-BCE optimization steps, and reports finite losses plus whether model
parameters changed. It is a training-path smoke, not a useful trained policy.

## Runtime Benchmark

`runtime_benchmark.py` measures the runtime-shaped loop:

```text
capture -> preprocess stub -> policy stub -> control stub
```

Synthetic smoke:

```bash
python tools/runtime_benchmark.py \
  --backend synthetic \
  --target-hz 60 \
  --max-cycles 120
```

Live PipeWire capture benchmark:

```bash
python tools/runtime_benchmark.py \
  --backend pipewire \
  --loop-mode frame-driven \
  --pipewire-mode runtime \
  --duration 5 \
  --target-hz 60 \
  --geometry "1920,0 1920x1080" \
  --image-format jpeg \
  --output-width 960 \
  --output-height 540 \
  --output /tmp/voxter-runtime-benchmark.json
```

Use `--pipewire-mode recording` to include temporary frame persistence in the
measurement. The default `runtime` mode pulls in-memory payloads and does not
write frames. Neither mode injects keyboard input. Passing the benchmark means
the measured skeleton stayed inside the tick budget; it does not prove the
trained policy or control boundary is ready.

Use `--loop-mode fixed-rate` to test a scheduled control loop and
`--loop-mode frame-driven` to report frame wait separately from
arrival-to-decision latency.

Benchmark the first real preprocessing path:

```bash
python tools/runtime_benchmark.py \
  --backend pipewire \
  --loop-mode frame-driven \
  --pipewire-mode runtime \
  --preprocess grayscale \
  --frame-stack-length 4 \
  --duration 5 \
  --target-hz 60 \
  --geometry "1920,0 1920x1080" \
  --image-format gray8 \
  --output-width 640 \
  --output-height 360
```

`--image-format gray8` asks GStreamer to produce grayscale frames directly,
avoiding a Python per-pixel RGB conversion loop in the live runtime path. Raw
RGB through `--image-format ppm` remains useful for validating the dependency-
free RGB preprocessing implementation on small fixtures or diagnostic runs.
Use `--frame-stack-length 1` for single-frame observations and values such as
`4` to benchmark the Stage 1 stacked input contract.
