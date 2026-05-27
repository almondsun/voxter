#!/usr/bin/env python
"""Validate and write an acceptance record for a Stage 1 Voxter dataset."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from voxter.contracts import VoxterContractError
from voxter.preprocessing import write_stage1_dataset_acceptance


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture_dir", type=Path)
    parser.add_argument("dataset_dir", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--min-input-events", type=int, default=1)
    parser.add_argument("--require-both-actions", action="store_true", default=True)
    parser.add_argument(
        "--allow-single-action", dest="require_both_actions", action="store_false"
    )
    parser.add_argument("--max-sync-mismatches", type=int, default=0)
    parser.add_argument("--max-dropped-frames", type=int, default=0)
    parser.add_argument("--max-missing-frame-files", type=int, default=0)
    parser.add_argument("--max-missed-periods", type=int)
    parser.add_argument("--max-p95-interval-ms", type=float)
    parser.add_argument("--max-p99-interval-ms", type=float)
    args = parser.parse_args()

    output_path = args.output or args.dataset_dir / "acceptance.json"
    try:
        acceptance = write_stage1_dataset_acceptance(
            args.capture_dir,
            args.dataset_dir,
            output_path,
            min_input_events=args.min_input_events,
            require_both_actions=args.require_both_actions,
            max_sync_mismatches=args.max_sync_mismatches,
            max_dropped_frames=args.max_dropped_frames,
            max_missing_frame_files=args.max_missing_frame_files,
            max_missed_periods=args.max_missed_periods,
            max_p95_interval_ms=args.max_p95_interval_ms,
            max_p99_interval_ms=args.max_p99_interval_ms,
        )
    except (OSError, ValueError, VoxterContractError) as exc:
        print(f"Stage 1 dataset acceptance failed: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(acceptance.to_json_dict(), indent=2, sort_keys=True))
    return 0 if acceptance.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
