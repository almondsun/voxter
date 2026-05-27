#!/usr/bin/env python
"""Build a causally aligned Voxter manifest from one raw capture directory."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from voxter.contracts import VoxterContractError
from voxter.preprocessing import write_aligned_manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture_dir", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--delta-sys", type=int, default=0)
    parser.add_argument("--split", default="unsplit")
    parser.add_argument("--manifest-name", default="aligned_manifest.jsonl")
    args = parser.parse_args()

    try:
        manifest_path = write_aligned_manifest(
            args.capture_dir,
            args.output,
            delta_sys=args.delta_sys,
            split=args.split,
            manifest_name=args.manifest_name,
        )
    except (OSError, ValueError, VoxterContractError) as exc:
        print(f"manifest build failed: {exc}", file=sys.stderr)
        return 1

    line_count = sum(1 for _ in manifest_path.open("r", encoding="utf-8"))
    print(
        json.dumps(
            {
                "capture_dir": str(args.capture_dir),
                "delta_sys": args.delta_sys,
                "manifest_path": str(manifest_path),
                "row_count": line_count,
                "split": args.split,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
