#!/usr/bin/env python
"""Run a runtime-shaped capture/preprocess/policy/control latency benchmark."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

if __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from voxter.capture.frames import FrameCaptureError
from voxter.capture.pipewire import PipeWireFramePayload, PipeWireGStreamerFrameCapture
from voxter.contracts import ActionState, VoxterContractError
from voxter.preprocessing import (
    FrameStackConfig,
    ObservationConfig,
    RollingFrameStack,
    preprocess_grayscale_observation,
    preprocess_rgb_observation,
)
from voxter.runtime import (
    RuntimeBenchmarkConfig,
    run_frame_driven_runtime_benchmark,
    run_runtime_benchmark,
)


def main() -> int:
    parser = _make_parser()
    args = parser.parse_args()

    try:
        report = _run(args)
    except (OSError, ValueError, VoxterContractError, FrameCaptureError) as exc:
        print(f"runtime benchmark failed: {exc}", file=sys.stderr)
        return 1

    payload = report.to_json_dict(include_cycles=args.include_cycles)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def _make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--backend",
        choices=("synthetic", "pipewire"),
        default="synthetic",
    )
    parser.add_argument("--duration", type=float, default=5.0)
    parser.add_argument("--target-hz", type=float, default=60.0)
    parser.add_argument("--max-cycles", type=int)
    parser.add_argument("--warmup-cycles", type=int, default=0)
    parser.add_argument("--threshold", type=float, default=0.5)
    parser.add_argument(
        "--loop-mode",
        choices=("fixed-rate", "frame-driven"),
        default="fixed-rate",
        help="fixed-rate schedules cycles; frame-driven starts on frame receipt",
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--include-cycles",
        action="store_true",
        help="include per-cycle records in stdout and output JSON",
    )
    parser.add_argument("--geometry", default="1920,0 1920x1080")
    parser.add_argument(
        "--image-format",
        choices=("jpeg", "ppm", "gray8"),
        default="jpeg",
    )
    parser.add_argument(
        "--pipewire-mode",
        choices=("runtime", "recording"),
        default="runtime",
        help="runtime pulls in-memory payloads; recording writes temporary frames",
    )
    parser.add_argument("--jpeg-quality", type=int, default=70)
    parser.add_argument("--output-width", type=int)
    parser.add_argument("--output-height", type=int)
    parser.add_argument("--portal-source-types", type=int, default=1)
    parser.add_argument("--portal-cursor-mode", type=int, default=1)
    parser.add_argument("--portal-timeout", type=int, default=20)
    parser.add_argument("--synthetic-capture-ms", type=float, default=1.0)
    parser.add_argument("--synthetic-preprocess-ms", type=float, default=0.2)
    parser.add_argument("--synthetic-inference-ms", type=float, default=0.2)
    parser.add_argument("--synthetic-control-ms", type=float, default=0.1)
    parser.add_argument(
        "--preprocess",
        choices=("none", "grayscale"),
        default="none",
        help="preprocessing stage to benchmark",
    )
    parser.add_argument("--observation-width", type=int)
    parser.add_argument("--observation-height", type=int)
    parser.add_argument("--frame-stack-length", type=int, default=1)
    return parser


def _run(args: argparse.Namespace) -> Any:
    config = RuntimeBenchmarkConfig(
        duration_s=args.duration,
        target_hz=args.target_hz,
        threshold=args.threshold,
        max_cycles=args.max_cycles,
        warmup_cycles=args.warmup_cycles,
    )
    if args.backend == "synthetic":
        return _run_synthetic(args, config)
    return _run_pipewire(args, config)


def _run_synthetic(
    args: argparse.Namespace,
    config: RuntimeBenchmarkConfig,
) -> Any:
    def capture_frame(frame_index: int) -> bytes:
        _sleep_ms(args.synthetic_capture_ms)
        return f"frame-{frame_index}".encode("ascii")

    def preprocess_frame(frame: bytes) -> bytes:
        _sleep_ms(args.synthetic_preprocess_ms)
        return frame

    def run_policy(_observation: bytes) -> float:
        _sleep_ms(args.synthetic_inference_ms)
        return 0.0

    def apply_action(_action: ActionState) -> None:
        _sleep_ms(args.synthetic_control_ms)

    if args.loop_mode == "frame-driven":
        return run_frame_driven_runtime_benchmark(
            config,
            receive_frame=capture_frame,
            preprocess_frame=preprocess_frame,
            run_policy=run_policy,
            apply_action=apply_action,
        )
    return run_runtime_benchmark(
        config,
        capture_frame=capture_frame,
        preprocess_frame=preprocess_frame,
        run_policy=run_policy,
        apply_action=apply_action,
    )


def _run_pipewire(
    args: argparse.Namespace,
    config: RuntimeBenchmarkConfig,
) -> Any:
    if (args.output_width is None) != (args.output_height is None):
        raise ValueError("output-width and output-height must be set together")

    with tempfile.TemporaryDirectory(prefix="voxter-runtime-benchmark-") as temp_dir:
        frames_dir = Path(temp_dir) / "frames"
        capture = PipeWireGStreamerFrameCapture(
            args.geometry,
            source_types=args.portal_source_types,
            cursor_mode=args.portal_cursor_mode,
            portal_request_timeout_s=args.portal_timeout,
            image_format=args.image_format,
            jpeg_quality=args.jpeg_quality,
            async_writes=True,
            output_width=args.output_width,
            output_height=args.output_height,
        )
        try:
            if args.pipewire_mode == "runtime":

                def capture_frame(frame_index: int) -> PipeWireFramePayload:
                    _ = frame_index
                    return capture.pull_frame_payload()

            else:

                def capture_frame(frame_index: int) -> bytes:
                    frame_path = frames_dir / f"{frame_index:06d}{capture.file_suffix}"
                    record = capture.capture(
                        frame_path,
                        run_id="runtime-benchmark",
                        attempt_id=None,
                        frame_index=frame_index,
                        action=ActionState.RELEASED,
                        action_sample_timestamp=time.time(),
                    )
                    return record.frame_path.encode("utf-8")

            preprocess_frame = _make_pipewire_preprocessor(args)

            def run_policy(_observation: bytes) -> float:
                return 0.0

            def apply_action(_action: ActionState) -> None:
                return None

            if args.loop_mode == "frame-driven":
                return run_frame_driven_runtime_benchmark(
                    config,
                    receive_frame=capture_frame,
                    preprocess_frame=preprocess_frame,
                    run_policy=run_policy,
                    apply_action=apply_action,
                )
            return run_runtime_benchmark(
                config,
                capture_frame=capture_frame,
                preprocess_frame=preprocess_frame,
                run_policy=run_policy,
                apply_action=apply_action,
            )
        finally:
            capture.close()


def _sleep_ms(duration_ms: float) -> None:
    if duration_ms < 0:
        raise ValueError("synthetic stage durations must be non-negative")
    time.sleep(duration_ms / 1000)


def _make_pipewire_preprocessor(args: argparse.Namespace) -> Any:
    if args.frame_stack_length <= 0:
        raise ValueError("frame-stack-length must be positive")
    if args.frame_stack_length != 1 and args.preprocess == "none":
        raise ValueError("frame stacking requires --preprocess grayscale")

    if args.preprocess == "none":

        def preprocess_frame(frame: object) -> object:
            if isinstance(frame, PipeWireFramePayload):
                return frame.data
            return frame

        return preprocess_frame

    if args.pipewire_mode != "runtime":
        raise ValueError("grayscale preprocessing requires --pipewire-mode runtime")
    observation_width = args.observation_width or args.output_width
    observation_height = args.observation_height or args.output_height
    if observation_width is None or observation_height is None:
        raise ValueError(
            "grayscale preprocessing requires observation dimensions or "
            "capture output dimensions"
        )
    config = ObservationConfig(width=observation_width, height=observation_height)
    stacker = (
        RollingFrameStack(
            FrameStackConfig(
                length=args.frame_stack_length,
                width=observation_width,
                height=observation_height,
            )
        )
        if args.frame_stack_length > 1
        else None
    )

    def preprocess_frame(frame: object) -> bytes:
        if not isinstance(frame, PipeWireFramePayload):
            raise ValueError(
                "grayscale preprocessing requires a PipeWire frame payload"
            )
        if frame.image_format == "gray8":
            observation = preprocess_grayscale_observation(
                frame.data,
                source_width=frame.frame_width,
                source_height=frame.frame_height,
                config=config,
            )
        else:
            if frame.image_format != "rgb":
                raise ValueError(
                    "grayscale preprocessing requires raw RGB or GRAY8 "
                    "PipeWire payloads"
                )
            observation = preprocess_rgb_observation(
                frame.data,
                source_width=frame.frame_width,
                source_height=frame.frame_height,
                config=config,
            )
        if stacker is None:
            return observation.data
        return stacker.update(observation).data

    return preprocess_frame


if __name__ == "__main__":
    raise SystemExit(main())
