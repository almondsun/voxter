#!/usr/bin/env python
"""Run a tiny optional-PyTorch Stage 1 optimization smoke."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from voxter.contracts import VoxterContractError
from voxter.training.stage1_torch import (
    Stage1TorchSmokeConfig,
    run_stage1_torch_smoke,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset_dirs", nargs="+", type=Path)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--train-steps", type=int, default=3)
    parser.add_argument("--learning-rate", type=float, default=1e-3)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        report = run_stage1_torch_smoke(
            Stage1TorchSmokeConfig(
                dataset_dirs=tuple(args.dataset_dirs),
                batch_size=args.batch_size,
                train_steps=args.train_steps,
                learning_rate=args.learning_rate,
                device=args.device,
                seed=args.seed,
            )
        )
    except (OSError, ValueError, VoxterContractError) as exc:
        print(f"Stage 1 torch smoke failed: {exc}", file=sys.stderr)
        return 2

    output = json.dumps(report.to_json_dict(), indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
    print(output, end="")
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
