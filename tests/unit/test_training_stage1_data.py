from __future__ import annotations

import json
from pathlib import Path

import pytest

from voxter.contracts import CaptureRecordError
from voxter.training import (
    load_stage1_dataset_index,
    smoke_stage1_batches,
)


def test_stage1_data_smoke_loads_batches(tmp_path: Path) -> None:
    dataset_dir = make_stage1_dataset(tmp_path, sample_count=3)

    index = load_stage1_dataset_index([dataset_dir])
    report = smoke_stage1_batches(index, batch_size=2, max_batches=2)

    assert index.sample_count == 3
    assert index.frame_stack_shape == (4, 2, 3)
    assert report.passed
    assert report.checked_batch_count == 2
    assert report.checked_sample_count == 3


def test_stage1_data_smoke_reports_bad_payload_size(tmp_path: Path) -> None:
    dataset_dir = make_stage1_dataset(tmp_path, sample_count=2)
    first_stack = next((dataset_dir / "stacks").iterdir())
    first_stack.write_bytes(b"too-short")

    index = load_stage1_dataset_index([dataset_dir])
    report = smoke_stage1_batches(index, batch_size=2, max_batches=1)

    assert not report.passed
    assert "wrong byte size" in report.failures[0]


def test_stage1_index_rejects_mismatched_contracts(tmp_path: Path) -> None:
    first = make_stage1_dataset(tmp_path / "first", sample_count=2, width=3)
    second = make_stage1_dataset(tmp_path / "second", sample_count=2, width=4)

    with pytest.raises(CaptureRecordError, match="contracts must match"):
        load_stage1_dataset_index([first, second])


def make_stage1_dataset(
    root: Path,
    *,
    sample_count: int,
    width: int = 3,
    height: int = 2,
    stack_length: int = 4,
) -> Path:
    dataset_dir = root / "dataset"
    observation_dir = dataset_dir / "observations"
    stack_dir = dataset_dir / "stacks"
    observation_dir.mkdir(parents=True)
    stack_dir.mkdir(parents=True)
    manifest_path = dataset_dir / "stage1_manifest.jsonl"
    rows = []
    held_count = 0
    released_count = 0
    for index in range(sample_count):
        action = index % 2
        held_count += 1 if action == 1 else 0
        released_count += 1 if action == 0 else 0
        observation_path = observation_dir / f"{index:06d}.gray"
        stack_path = stack_dir / f"{index:06d}.bin"
        observation_path.write_bytes(bytes([index]) * (width * height))
        stack_path.write_bytes(bytes([index]) * (width * height * stack_length))
        rows.append(
            {
                "schema_version": "stage1-manifest-v1",
                "sample_id": f"run:attempt:{index:06d}:delta+0",
                "run_id": "run",
                "attempt_id": "attempt",
                "frame_index": index,
                "timestamp": float(index),
                "raw_frame_path": f"/tmp/raw/{index:06d}.pgm",
                "observation_path": str(observation_path),
                "frame_stack_path": str(stack_path),
                "action_held": action,
                "label_source_timestamp": float(index),
                "delta_sys": 0,
                "split": "train",
                "observation_schema_version": "observation-v1",
                "observation_width": width,
                "observation_height": height,
                "observation_dtype": "uint8",
                "observation_layout": "hw",
                "frame_stack_schema_version": "frame-stack-v1",
                "frame_stack_length": stack_length,
                "frame_stack_layout": "khw",
                "terminal_cleaning_applied": False,
            }
        )
    with manifest_path.open("w", encoding="utf-8") as manifest_file:
        for row in rows:
            manifest_file.write(json.dumps(row, sort_keys=True) + "\n")
    summary = {
        "schema_version": "stage1-dataset-summary-v1",
        "source_capture_dir": "/tmp/raw",
        "output_dir": str(dataset_dir.resolve()),
        "manifest_path": str(manifest_path.resolve()),
        "sample_count": sample_count,
        "released_count": released_count,
        "held_count": held_count,
        "class_weights": {"held": 1.0, "released": 1.0},
        "delta_sys": 0,
        "split": "train",
        "observation_schema_version": "observation-v1",
        "observation_width": width,
        "observation_height": height,
        "observation_dtype": "uint8",
        "observation_layout": "hw",
        "frame_stack_schema_version": "frame-stack-v1",
        "frame_stack_length": stack_length,
        "frame_stack_layout": "khw",
        "terminal_event_count": 0,
        "discarded_terminal_window_count": 0,
        "death_tail_s": 0.35,
        "reset_skip_s": 1.5,
    }
    (dataset_dir / "dataset_summary.json").write_text(
        json.dumps(summary, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return dataset_dir
