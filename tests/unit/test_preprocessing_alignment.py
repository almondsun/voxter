from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from voxter.contracts import CaptureRecordError
from voxter.preprocessing import (
    ALIGNED_MANIFEST_SCHEMA_VERSION,
    build_aligned_manifest,
    write_aligned_manifest,
)


def test_build_aligned_manifest_reconstructs_event_derived_labels(
    tmp_path: Path,
) -> None:
    write_capture_fixture(tmp_path)

    rows = build_aligned_manifest(tmp_path)

    assert [int(row.action_held) for row in rows] == [0, 1, 1, 0]
    assert [row.label_source_timestamp for row in rows] == [10.0, 10.1, 10.2, 10.3]
    assert all(row.schema_version == ALIGNED_MANIFEST_SCHEMA_VERSION for row in rows)
    assert rows[0].raw_frame_path.endswith("frames/attempt-1-000000.jpg")
    assert rows[0].source_width == 1920
    assert rows[0].source_height == 1080
    assert rows[0].frame_width == 960
    assert rows[0].frame_height == 540
    assert rows[0].image_format == "jpeg"
    assert rows[0].capture_resized
    assert rows[0].split == "unsplit"


def test_build_aligned_manifest_uses_positive_delta_sys_later_frame(
    tmp_path: Path,
) -> None:
    write_capture_fixture(tmp_path)

    rows = build_aligned_manifest(tmp_path, delta_sys=1, split="train")

    assert [row.frame_index for row in rows] == [0, 1, 2]
    assert [int(row.action_held) for row in rows] == [1, 1, 0]
    assert [row.label_source_timestamp for row in rows] == [10.1, 10.2, 10.3]
    assert all(row.delta_sys == 1 for row in rows)
    assert all(row.split == "train" for row in rows)


def test_build_aligned_manifest_uses_negative_delta_sys_earlier_frame(
    tmp_path: Path,
) -> None:
    write_capture_fixture(tmp_path)

    rows = build_aligned_manifest(tmp_path, delta_sys=-1)

    assert [row.frame_index for row in rows] == [1, 2, 3]
    assert [int(row.action_held) for row in rows] == [0, 1, 1]
    assert [row.label_source_timestamp for row in rows] == [10.0, 10.1, 10.2]


def test_build_aligned_manifest_does_not_cross_attempt_boundaries(
    tmp_path: Path,
) -> None:
    write_capture_fixture(tmp_path, attempts=("attempt-1", "attempt-2"))

    rows = build_aligned_manifest(tmp_path, delta_sys=1)

    assert [(row.attempt_id, row.frame_index) for row in rows] == [
        ("attempt-1", 0),
        ("attempt-2", 0),
    ]


def test_write_aligned_manifest_writes_jsonl(tmp_path: Path) -> None:
    capture_dir = tmp_path / "capture"
    output_dir = tmp_path / "processed"
    write_capture_fixture(capture_dir)

    manifest_path = write_aligned_manifest(
        capture_dir,
        output_dir,
        delta_sys=1,
        split="validation",
    )

    rows = [
        json.loads(line)
        for line in manifest_path.read_text(encoding="utf-8").splitlines()
    ]
    assert manifest_path == output_dir / "aligned_manifest.jsonl"
    assert len(rows) == 3
    assert rows[0]["schema_version"] == ALIGNED_MANIFEST_SCHEMA_VERSION
    assert rows[0]["action_held"] == 1
    assert rows[0]["split"] == "validation"


def test_write_aligned_manifest_rejects_nested_manifest_name(tmp_path: Path) -> None:
    write_capture_fixture(tmp_path)

    with pytest.raises(CaptureRecordError, match="plain file name"):
        write_aligned_manifest(
            tmp_path,
            tmp_path / "processed",
            manifest_name="nested/manifest.jsonl",
        )


def test_build_aligned_manifest_cli_writes_manifest(tmp_path: Path) -> None:
    capture_dir = tmp_path / "capture"
    output_dir = tmp_path / "processed"
    write_capture_fixture(capture_dir)

    result = subprocess.run(
        [
            sys.executable,
            "tools/build_aligned_manifest.py",
            str(capture_dir),
            "--output",
            str(output_dir),
            "--delta-sys",
            "1",
            "--split",
            "test",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    summary = json.loads(result.stdout)
    manifest_path = Path(summary["manifest_path"])
    rows = [
        json.loads(line)
        for line in manifest_path.read_text(encoding="utf-8").splitlines()
    ]
    assert summary["row_count"] == 3
    assert rows[0]["action_held"] == 1
    assert rows[0]["split"] == "test"


def write_capture_fixture(
    root: Path,
    *,
    attempts: tuple[str, ...] = ("attempt-1",),
) -> None:
    root.mkdir(parents=True, exist_ok=True)
    frames_dir = root / "frames"
    frames_dir.mkdir()
    frame_rows = []
    event_rows = []
    for attempt in attempts:
        frame_count = 4 if len(attempts) == 1 else 2
        for index in range(frame_count):
            frame_path = frames_dir / f"{attempt}-{index:06d}.jpg"
            frame_path.write_bytes(b"\xff\xd8data\xff\xd9")
            frame_rows.append(
                {
                    "run_id": "run-1",
                    "attempt_id": attempt,
                    "frame_index": index,
                    "timestamp": 10.005 + index * 0.1,
                    "frame_path": str(frame_path),
                    "action": 0,
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
        event_rows.extend(
            [
                {
                    "run_id": "run-1",
                    "attempt_id": attempt,
                    "timestamp": 10.05,
                    "device": "/dev/input/event5",
                    "key_code": 17,
                    "kind": "press",
                    "action": 1,
                },
                {
                    "run_id": "run-1",
                    "attempt_id": attempt,
                    "timestamp": 10.25,
                    "device": "/dev/input/event5",
                    "key_code": 17,
                    "kind": "release",
                    "action": 0,
                },
            ]
        )
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
