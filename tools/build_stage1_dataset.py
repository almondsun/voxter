#!/usr/bin/env python
"""Materialize a Stage 1 Voxter behavior-cloning dataset."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from voxter.contracts import VoxterContractError
from voxter.preprocessing import Stage1DatasetConfig, build_stage1_dataset


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture_dir", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--delta-sys", type=int, default=0)
    parser.add_argument("--split", default="unsplit")
    parser.add_argument("--observation-width", type=int, required=True)
    parser.add_argument("--observation-height", type=int, required=True)
    parser.add_argument("--frame-stack-length", type=int, default=4)
    parser.add_argument("--manifest-name", default="stage1_manifest.jsonl")
    parser.add_argument("--summary-name", default="dataset_summary.json")
    args = parser.parse_args()

    try:
        summary = build_stage1_dataset(
            Stage1DatasetConfig(
                capture_dir=args.capture_dir,
                output_dir=args.output,
                observation_width=args.observation_width,
                observation_height=args.observation_height,
                frame_stack_length=args.frame_stack_length,
                delta_sys=args.delta_sys,
                split=args.split,
                manifest_name=args.manifest_name,
                summary_name=args.summary_name,
            )
        )
    except (OSError, ValueError, VoxterContractError) as exc:
        print(f"Stage 1 dataset build failed: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(summary.to_json_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
