from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from voxter.preprocessing import (
    STAGE1_ACCEPTANCE_SCHEMA_VERSION,
    Stage1DatasetConfig,
    accept_stage1_dataset,
    build_stage1_dataset,
)


def test_accept_stage1_dataset_validates_capture_and_payloads(tmp_path: Path) -> None:
    capture_dir = tmp_path / "raw" / "run-1"
    dataset_dir = tmp_path / "datasets" / "run-1-stage1"
    write_capture_fixture(capture_dir)
    build_stage1_dataset(
        Stage1DatasetConfig(
            capture_dir=capture_dir,
            output_dir=dataset_dir,
            observation_width=2,
            observation_height=1,
            frame_stack_length=3,
            split="train",
        )
    )

    acceptance = accept_stage1_dataset(capture_dir, dataset_dir)

    assert acceptance.schema_version == STAGE1_ACCEPTANCE_SCHEMA_VERSION
    assert acceptance.passed
    assert acceptance.sample_count == 4
    assert acceptance.released_count == 2
    assert acceptance.held_count == 2
    assert acceptance.expected_observation_bytes == 2
    assert acceptance.expected_stack_bytes == 6
    assert acceptance.missing_payload_count == 0
    assert acceptance.bad_stack_size_count == 0
    assert acceptance.first_stack_warmup_ok


def test_accept_stage1_dataset_reports_missing_payload(tmp_path: Path) -> None:
    capture_dir = tmp_path / "raw" / "run-1"
    dataset_dir = tmp_path / "datasets" / "run-1-stage1"
    write_capture_fixture(capture_dir)
    build_stage1_dataset(
        Stage1DatasetConfig(
            capture_dir=capture_dir,
            output_dir=dataset_dir,
            observation_width=2,
            observation_height=1,
        )
    )
    first_row = json.loads(
        (dataset_dir / "stage1_manifest.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()[0]
    )
    Path(first_row["frame_stack_path"]).unlink()

    acceptance = accept_stage1_dataset(capture_dir, dataset_dir)

    assert not acceptance.passed
    assert acceptance.missing_payload_count == 1
    assert "missing payload files: 1" in acceptance.failures


def test_accept_stage1_dataset_cli_writes_record(tmp_path: Path) -> None:
    capture_dir = tmp_path / "raw" / "run-1"
    dataset_dir = tmp_path / "datasets" / "run-1-stage1"
    write_capture_fixture(capture_dir)
    build_stage1_dataset(
        Stage1DatasetConfig(
            capture_dir=capture_dir,
            output_dir=dataset_dir,
            observation_width=2,
            observation_height=1,
        )
    )

    result = subprocess.run(
        [
            sys.executable,
            "tools/accept_stage1_dataset.py",
            str(capture_dir),
            str(dataset_dir),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    stdout_record = json.loads(result.stdout)
    file_record = json.loads((dataset_dir / "acceptance.json").read_text())
    assert stdout_record["passed"]
    assert file_record["schema_version"] == STAGE1_ACCEPTANCE_SCHEMA_VERSION


def write_capture_fixture(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    frames_dir = root / "frames"
    frames_dir.mkdir()
    frame_rows = []
    for index in range(4):
        frame_path = frames_dir / f"{index:06d}.pgm"
        frame_path.write_bytes(
            b"P5\n2 1\n255\n" + bytes([10 + index * 10, 11 + index * 10])
        )
        frame_rows.append(
            {
                "run_id": "run-1",
                "attempt_id": "attempt-1",
                "frame_index": index,
                "timestamp": 10.005 + index * 0.1,
                "frame_path": str(frame_path),
                "action": 0 if index in {0, 3} else 1,
                "action_sample_timestamp": 10.0 + index * 0.1,
                "geometry": "1920,0 1920x1080",
                "capture_duration_s": 0.01,
                "capture_backend": "test-pgm",
                "image_format": "pgm",
                "source_width": 2,
                "source_height": 1,
                "frame_width": 2,
                "frame_height": 1,
                "capture_resized": False,
            }
        )
    event_rows = [
        {
            "run_id": "run-1",
            "attempt_id": "attempt-1",
            "timestamp": 10.05,
            "device": "/dev/input/event5",
            "key_code": 17,
            "kind": "press",
            "action": 1,
        },
        {
            "run_id": "run-1",
            "attempt_id": "attempt-1",
            "timestamp": 10.25,
            "device": "/dev/input/event5",
            "key_code": 17,
            "kind": "release",
            "action": 0,
        },
    ]
    (root / "frames.jsonl").write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in frame_rows),
        encoding="utf-8",
    )
    (root / "input_events.jsonl").write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in event_rows),
        encoding="utf-8",
    )
    (root / "capture_summary.json").write_text(
        json.dumps(
            {
                "target_hz": 60.0,
                "effective_hz": 60.0,
                "dropped_frame_count": 0,
                "missed_deadline_estimate": 0,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
