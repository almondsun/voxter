#!/usr/bin/env python
"""Smoke-test Stage 1 materialized dataset loading without ML dependencies."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from voxter.contracts import VoxterContractError
from voxter.training import load_stage1_dataset_index, smoke_stage1_batches


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset_dirs", nargs="+", type=Path)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--max-batches", type=int, default=2)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        index = load_stage1_dataset_index(args.dataset_dirs)
        report = smoke_stage1_batches(
            index,
            batch_size=args.batch_size,
            max_batches=args.max_batches,
        )
    except (OSError, ValueError, VoxterContractError) as exc:
        print(f"Stage 1 data smoke failed: {exc}", file=sys.stderr)
        return 2

    output = json.dumps(report.to_json_dict(), indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
    print(output, end="")
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
