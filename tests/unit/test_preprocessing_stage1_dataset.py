from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from voxter.contracts import CaptureRecordError
from voxter.preprocessing import (
    STAGE1_DATASET_SUMMARY_SCHEMA_VERSION,
    STAGE1_MANIFEST_SCHEMA_VERSION,
    Stage1DatasetConfig,
    build_stage1_dataset,
    load_pgm_image,
)


def test_load_pgm_image_parses_binary_p5_with_comment(tmp_path: Path) -> None:
    path = tmp_path / "frame.pgm"
    path.write_bytes(b"P5\n# source: test\n2 1\n255\n\x0a\xff")

    image = load_pgm_image(path)

    assert image.width == 2
    assert image.height == 1
    assert image.data == bytes([10, 255])


def test_load_pgm_image_rejects_non_p5(tmp_path: Path) -> None:
    path = tmp_path / "frame.pgm"
    path.write_bytes(b"P2\n2 1\n255\n0 1\n")

    with pytest.raises(CaptureRecordError, match="binary P5"):
        load_pgm_image(path)


def test_build_stage1_dataset_materializes_manifest_and_stacks(
    tmp_path: Path,
) -> None:
    capture_dir = tmp_path / "capture"
    output_dir = tmp_path / "dataset"
    write_pgm_capture_fixture(capture_dir)

    summary = build_stage1_dataset(
        Stage1DatasetConfig(
            capture_dir=capture_dir,
            output_dir=output_dir,
            observation_width=2,
            observation_height=1,
            frame_stack_length=3,
            split="train",
        )
    )

    manifest_path = output_dir / "stage1_manifest.jsonl"
    manifest_rows = [
        json.loads(line)
        for line in manifest_path.read_text(encoding="utf-8").splitlines()
    ]
    assert summary.schema_version == STAGE1_DATASET_SUMMARY_SCHEMA_VERSION
    assert summary.sample_count == 4
    assert summary.released_count == 2
    assert summary.held_count == 2
    assert summary.class_weights == {"released": 1.0, "held": 1.0}
    assert summary.frame_stack_length == 3
    assert manifest_rows[0]["schema_version"] == STAGE1_MANIFEST_SCHEMA_VERSION
    assert [row["action_held"] for row in manifest_rows] == [0, 1, 1, 0]
    assert all(row["split"] == "train" for row in manifest_rows)

    first_observation = Path(manifest_rows[0]["observation_path"]).read_bytes()
    first_stack = Path(manifest_rows[0]["frame_stack_path"]).read_bytes()
    second_stack = Path(manifest_rows[1]["frame_stack_path"]).read_bytes()
    assert first_observation == bytes([10, 11])
    assert first_stack == bytes([10, 11, 10, 11, 10, 11])
    assert second_stack == bytes([10, 11, 10, 11, 20, 21])

    summary_json = json.loads((output_dir / "dataset_summary.json").read_text())
    assert summary_json["manifest_path"] == str(manifest_path.resolve())
    assert summary_json["held_count"] == 2


def test_build_stage1_dataset_resets_stack_at_attempt_boundary(
    tmp_path: Path,
) -> None:
    capture_dir = tmp_path / "capture"
    output_dir = tmp_path / "dataset"
    write_pgm_capture_fixture(capture_dir, attempts=("attempt-1", "attempt-2"))

    build_stage1_dataset(
        Stage1DatasetConfig(
            capture_dir=capture_dir,
            output_dir=output_dir,
            observation_width=2,
            observation_height=1,
            frame_stack_length=2,
        )
    )

    manifest_rows = [
        json.loads(line)
        for line in (output_dir / "stage1_manifest.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    first_attempt_2 = next(
        row for row in manifest_rows if row["attempt_id"] == "attempt-2"
    )
    stack_bytes = Path(first_attempt_2["frame_stack_path"]).read_bytes()

    assert stack_bytes == bytes([110, 111, 110, 111])


def test_build_stage1_dataset_reports_missing_class_weight_as_null(
    tmp_path: Path,
) -> None:
    capture_dir = tmp_path / "capture"
    output_dir = tmp_path / "dataset"
    write_pgm_capture_fixture(capture_dir, include_press=False)

    summary = build_stage1_dataset(
        Stage1DatasetConfig(
            capture_dir=capture_dir,
            output_dir=output_dir,
            observation_width=2,
            observation_height=1,
            frame_stack_length=1,
        )
    )

    assert summary.released_count == 4
    assert summary.held_count == 0
    assert summary.class_weights == {"released": 0.5, "held": None}


def test_build_stage1_dataset_discards_terminal_windows(tmp_path: Path) -> None:
    capture_dir = tmp_path / "capture"
    output_dir = tmp_path / "dataset"
    write_pgm_capture_fixture(capture_dir)
    terminal_event = {
        "run_id": "run-1",
        "attempt_id": "attempt-1",
        "timestamp": 10.205,
        "device": "/dev/input/event5",
        "key_code": 78,
        "kind": "press",
        "terminal_type": "death",
    }
    (capture_dir / "terminal_events.jsonl").write_text(
        json.dumps(terminal_event, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    summary = build_stage1_dataset(
        Stage1DatasetConfig(
            capture_dir=capture_dir,
            output_dir=output_dir,
            observation_width=2,
            observation_height=1,
            frame_stack_length=2,
            death_tail_s=0.05,
            reset_skip_s=0.2,
        )
    )

    manifest_rows = [
        json.loads(line)
        for line in (output_dir / "stage1_manifest.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    assert [row["frame_index"] for row in manifest_rows] == [0, 1]
    assert all(row["terminal_cleaning_applied"] for row in manifest_rows)
    assert summary.terminal_event_count == 1
    assert summary.discarded_terminal_window_count == 1
    assert summary.death_tail_s == 0.05
    assert summary.reset_skip_s == 0.2


def test_build_stage1_dataset_counts_multiple_terminal_windows(tmp_path: Path) -> None:
    capture_dir = tmp_path / "capture"
    output_dir = tmp_path / "dataset"
    write_pgm_capture_fixture(capture_dir, attempts=("attempt-1", "attempt-2"))
    terminal_events = [
        {
            "run_id": "run-1",
            "attempt_id": "attempt-1",
            "timestamp": 10.205,
            "device": "/dev/input/event5",
            "key_code": 78,
            "kind": "press",
            "terminal_type": "death",
        },
        {
            "run_id": "run-1",
            "attempt_id": "attempt-2",
            "timestamp": 10.205,
            "device": "/dev/input/event5",
            "key_code": 78,
            "kind": "press",
            "terminal_type": "death",
        },
    ]
    (capture_dir / "terminal_events.jsonl").write_text(
        "".join(json.dumps(event, sort_keys=True) + "\n" for event in terminal_events),
        encoding="utf-8",
    )

    summary = build_stage1_dataset(
        Stage1DatasetConfig(
            capture_dir=capture_dir,
            output_dir=output_dir,
            observation_width=2,
            observation_height=1,
            death_tail_s=0.05,
            reset_skip_s=0.2,
        )
    )

    assert summary.terminal_event_count == 2
    assert summary.discarded_terminal_window_count == 2


def test_build_stage1_dataset_rejects_encoded_frames(tmp_path: Path) -> None:
    capture_dir = tmp_path / "capture"
    write_pgm_capture_fixture(capture_dir, image_format="jpeg", suffix=".jpg")

    with pytest.raises(CaptureRecordError, match="PGM/gray8"):
        build_stage1_dataset(
            Stage1DatasetConfig(
                capture_dir=capture_dir,
                output_dir=tmp_path / "dataset",
                observation_width=2,
                observation_height=1,
            )
        )


def test_build_stage1_dataset_accepts_cwd_relative_frame_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    capture_dir = workspace / "data" / "raw" / "run-1"
    output_dir = workspace / "data" / "datasets" / "run-1-stage1"
    write_pgm_capture_fixture(capture_dir)
    rows = [
        json.loads(line)
        for line in (capture_dir / "frames.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    for row in rows:
        row["frame_path"] = str(Path(row["frame_path"]).relative_to(workspace))
    (capture_dir / "frames.jsonl").write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    monkeypatch.chdir(workspace)

    summary = build_stage1_dataset(
        Stage1DatasetConfig(
            capture_dir=Path("data/raw/run-1"),
            output_dir=Path("data/datasets/run-1-stage1"),
            observation_width=2,
            observation_height=1,
        )
    )

    assert summary.sample_count == 4
    assert output_dir.joinpath("stage1_manifest.jsonl").exists()


def test_build_stage1_dataset_cli_writes_summary(tmp_path: Path) -> None:
    capture_dir = tmp_path / "capture"
    output_dir = tmp_path / "dataset"
    write_pgm_capture_fixture(capture_dir)

    result = subprocess.run(
        [
            sys.executable,
            "tools/build_stage1_dataset.py",
            str(capture_dir),
            "--output",
            str(output_dir),
            "--observation-width",
            "2",
            "--observation-height",
            "1",
            "--frame-stack-length",
            "2",
            "--split",
            "validation",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    summary = json.loads(result.stdout)
    assert summary["sample_count"] == 4
    assert summary["split"] == "validation"
    assert Path(summary["manifest_path"]).exists()


def write_pgm_capture_fixture(
    root: Path,
    *,
    attempts: tuple[str, ...] = ("attempt-1",),
    image_format: str = "pgm",
    suffix: str = ".pgm",
    press_timestamp: float = 10.05,
    include_press: bool = True,
) -> None:
    root.mkdir(parents=True, exist_ok=True)
    frames_dir = root / "frames"
    frames_dir.mkdir()
    frame_rows: list[dict[str, object]] = []
    event_rows: list[dict[str, object]] = []
    for attempt_index, attempt in enumerate(attempts):
        base_pixel = attempt_index * 100
        for index in range(4):
            frame_path = frames_dir / f"{attempt}-{index:06d}{suffix}"
            if image_format == "pgm":
                frame_path.write_bytes(
                    b"P5\n2 1\n255\n"
                    + bytes(
                        [base_pixel + 10 + index * 10, base_pixel + 11 + index * 10]
                    )
                )
            else:
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
                    "capture_backend": f"test-{image_format}",
                    "image_format": image_format,
                    "source_width": 2,
                    "source_height": 1,
                    "frame_width": 2,
                    "frame_height": 1,
                    "capture_resized": False,
                }
            )
        if include_press:
            event_rows.append(
                {
                    "run_id": "run-1",
                    "attempt_id": attempt,
                    "timestamp": press_timestamp,
                    "device": "/dev/input/event5",
                    "key_code": 17,
                    "kind": "press",
                    "action": 1,
                }
            )
        event_rows.append(
            {
                "run_id": "run-1",
                "attempt_id": attempt,
                "timestamp": 10.25,
                "device": "/dev/input/event5",
                "key_code": 17,
                "kind": "release",
                "action": 0,
            }
        )
    (root / "frames.jsonl").write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in frame_rows),
        encoding="utf-8",
    )
    (root / "input_events.jsonl").write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in event_rows),
        encoding="utf-8",
    )
