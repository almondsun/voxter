from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from voxter.contracts import CaptureRecordError
from voxter.preprocessing import (
    DELTA_SYS_CALIBRATION_SCHEMA_VERSION,
    calibrate_delta_sys,
    write_delta_sys_calibration_report,
)


def test_calibrate_delta_sys_scores_candidate_offsets(tmp_path: Path) -> None:
    write_capture_fixture(tmp_path)

    report = calibrate_delta_sys(tmp_path, min_delta_sys=-1, max_delta_sys=1)

    assert report.schema_version == DELTA_SYS_CALIBRATION_SCHEMA_VERSION
    assert report.best_delta_sys == 0
    assert [candidate.delta_sys for candidate in report.candidates] == [-1, 0, 1]
    assert [candidate.mismatch_count for candidate in report.candidates] == [2, 0, 2]
    assert [candidate.dropped_sample_count for candidate in report.candidates] == [
        1,
        0,
        1,
    ]


def test_calibrate_delta_sys_rejects_invalid_range(tmp_path: Path) -> None:
    write_capture_fixture(tmp_path)

    with pytest.raises(CaptureRecordError, match="min_delta_sys"):
        calibrate_delta_sys(tmp_path, min_delta_sys=2, max_delta_sys=1)


def test_write_delta_sys_calibration_report_writes_json(tmp_path: Path) -> None:
    capture_dir = tmp_path / "capture"
    output_path = tmp_path / "reports" / "delta_sys.json"
    write_capture_fixture(capture_dir)

    report = write_delta_sys_calibration_report(
        capture_dir,
        output_path,
        min_delta_sys=0,
        max_delta_sys=1,
    )

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert report.best_delta_sys == 0
    assert payload["schema_version"] == DELTA_SYS_CALIBRATION_SCHEMA_VERSION
    assert payload["best_delta_sys"] == 0
    assert len(payload["candidates"]) == 2


def test_calibrate_delta_sys_cli_writes_report(tmp_path: Path) -> None:
    capture_dir = tmp_path / "capture"
    output_path = tmp_path / "delta_sys.json"
    write_capture_fixture(capture_dir)

    result = subprocess.run(
        [
            sys.executable,
            "tools/calibrate_delta_sys.py",
            str(capture_dir),
            "--output",
            str(output_path),
            "--min-delta-sys",
            "-1",
            "--max-delta-sys",
            "1",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    stdout_payload = json.loads(result.stdout)
    file_payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert stdout_payload == file_payload
    assert stdout_payload["best_delta_sys"] == 0


def write_capture_fixture(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    frames_dir = root / "frames"
    frames_dir.mkdir()
    frame_rows = []
    for index, action in enumerate([0, 1, 1, 0]):
        frame_path = frames_dir / f"{index:06d}.jpg"
        frame_path.write_bytes(b"\xff\xd8data\xff\xd9")
        frame_rows.append(
            {
                "run_id": "run-1",
                "attempt_id": "attempt-1",
                "frame_index": index,
                "timestamp": 10.005 + index * 0.1,
                "frame_path": str(frame_path),
                "action": action,
                "action_sample_timestamp": 10.0 + index * 0.1,
                "geometry": "1920,0 1920x1080",
                "capture_duration_s": 0.01,
                "capture_backend": "pipewire-gstreamer-jpeg",
                "image_format": "jpeg",
                "source_width": 1920,
                "source_height": 1080,
                "frame_width": 960,
                "frame_height": 540,
                "capture_resized": True,
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
