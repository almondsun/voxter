#!/usr/bin/env python
"""Record a manual Voxter raw capture session.

This tool is for offline/debug data collection. The current `grim` backend is
not a real-time runtime backend.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

if __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from voxter.capture import CaptureSessionConfig, run_capture_session
from voxter.capture.frames import FrameCaptureError
from voxter.capture.preview import PreviewGenerationError
from voxter.contracts import VoxterContractError


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output directory. Defaults to data/raw/<run-id>.",
    )
    parser.add_argument("--duration", type=float, required=True)
    parser.add_argument("--target-hz", type=float, default=20.0)
    parser.add_argument("--geometry", default="1920,0 1920x1080")
    parser.add_argument("--event-device", default="/dev/input/event5")
    parser.add_argument("--attempt-id", default="manual-w")
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--backend", choices=["grim", "pipewire"], default="grim")
    parser.add_argument(
        "--format",
        choices=["jpeg", "png", "ppm", "gray8"],
        default=None,
    )
    parser.add_argument("--jpeg-quality", type=int, default=70)
    parser.add_argument("--png-level", type=int, default=0)
    parser.add_argument("--key-code", type=int, default=17)
    parser.add_argument(
        "--terminal-key-code",
        type=int,
        default=78,
        help="manual terminal/death marker key code; default is numpad plus",
    )
    parser.add_argument("--terminal-type", default="death")
    parser.add_argument("--portal-source-types", type=int, default=1)
    parser.add_argument("--portal-cursor-mode", type=int, default=1)
    parser.add_argument("--portal-request-timeout", type=int, default=20)
    parser.add_argument("--write-queue-size", type=int, default=8)
    parser.add_argument("--sync-writes", action="store_true")
    parser.add_argument("--output-width", type=int, default=None)
    parser.add_argument("--output-height", type=int, default=None)
    parser.add_argument("--no-preview", action="store_true")
    parser.add_argument("--preview-name", default="preview.mp4")
    args = parser.parse_args()

    run_id = args.run_id or f"manual-{int(time.time())}"
    output_dir = args.output or Path("data/raw") / run_id
    image_format = args.format or "jpeg"
    config = CaptureSessionConfig(
        output_dir=output_dir,
        run_id=run_id,
        attempt_id=args.attempt_id,
        geometry=args.geometry,
        event_device=args.event_device,
        duration_s=args.duration,
        target_hz=args.target_hz,
        backend=args.backend,
        image_format=image_format,
        jpeg_quality=args.jpeg_quality,
        png_level=args.png_level,
        key_code=args.key_code,
        terminal_key_code=args.terminal_key_code,
        terminal_type=args.terminal_type,
        portal_source_types=args.portal_source_types,
        portal_cursor_mode=args.portal_cursor_mode,
        portal_request_timeout_s=args.portal_request_timeout,
        async_writes=not args.sync_writes,
        write_queue_size=args.write_queue_size,
        output_width=args.output_width,
        output_height=args.output_height,
        generate_preview=not args.no_preview,
        preview_name=args.preview_name,
    )
    try:
        summary = run_capture_session(config)
    except (
        FrameCaptureError,
        PreviewGenerationError,
        OSError,
        ValueError,
        VoxterContractError,
    ) as exc:
        print(f"capture failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(summary.to_json_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
