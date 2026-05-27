#!/usr/bin/env python
"""Build a system-delay calibration report from one raw capture directory."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from voxter.contracts import VoxterContractError
from voxter.preprocessing import write_delta_sys_calibration_report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture_dir", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--min-delta-sys", type=int, default=-5)
    parser.add_argument("--max-delta-sys", type=int, default=5)
    args = parser.parse_args()

    try:
        report = write_delta_sys_calibration_report(
            args.capture_dir,
            args.output,
            min_delta_sys=args.min_delta_sys,
            max_delta_sys=args.max_delta_sys,
        )
    except (OSError, ValueError, VoxterContractError) as exc:
        print(f"calibration failed: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(report.to_json_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
