from __future__ import annotations

import json
from pathlib import Path

import pytest

from voxter.capture.analysis import analyze_capture_run


def test_analyze_capture_run_accepts_synchronized_binary_run(tmp_path: Path) -> None:
    write_capture_run(tmp_path)

    analysis = analyze_capture_run(
        tmp_path,
        max_missed_periods=0,
        max_p95_interval_ms=20.0,
        max_p99_interval_ms=20.0,
    )

    assert analysis.passed
    assert analysis.frame_count == 3
    assert analysis.event_count == 2
    assert analysis.frame_actions == (0, 1)
    assert analysis.event_actions == (0, 1)
    assert analysis.sync_mismatch_count_at_action_sample == 0
    assert analysis.missing_frame_file_count == 0
    assert analysis.interval_p95_ms == pytest.approx(10.0)


def test_analyze_capture_run_reports_sync_failures(tmp_path: Path) -> None:
    write_capture_run(tmp_path, frame_actions=[0, 0, 1])

    analysis = analyze_capture_run(tmp_path)

    assert not analysis.passed
    assert analysis.sync_mismatch_count_at_action_sample == 1
    assert analysis.failures == ("frame action mismatches exceed threshold: 1 > 0",)


def test_analyze_capture_run_can_require_input_events_and_both_actions(
    tmp_path: Path,
) -> None:
    write_capture_run(tmp_path, frame_actions=[0, 0, 0], event_rows=[])

    analysis = analyze_capture_run(
        tmp_path,
        min_input_events=1,
        require_both_actions=True,
    )

    assert not analysis.passed
    assert analysis.failures == (
        "input events below threshold: 0 < 1",
        "frame actions must include both 0 and 1",
    )


def write_capture_run(
    root: Path,
    *,
    frame_actions: list[int] | None = None,
    event_rows: list[dict[str, object]] | None = None,
) -> None:
    actions = frame_actions or [0, 1, 1]
    frames_dir = root / "frames"
    frames_dir.mkdir()
    rows = []
    for index, action in enumerate(actions):
        frame_path = frames_dir / f"{index:06d}.jpg"
        frame_path.write_bytes(b"\xff\xd8data\xff\xd9")
        rows.append(
            {
                "run_id": "run-1",
                "attempt_id": "attempt-1",
                "frame_index": index,
                "timestamp": 100.005 + index * 0.01,
                "frame_path": str(frame_path),
                "action": action,
                "action_sample_timestamp": 100.0 + index * 0.01,
                "geometry": "1920,0 1920x1080",
                "capture_duration_s": 0.002,
                "capture_backend": "pipewire-gstreamer-jpeg",
            }
        )
    (root / "frames.jsonl").write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    events = event_rows
    if events is None:
        events = [
            {
                "run_id": "run-1",
                "attempt_id": "attempt-1",
                "timestamp": 100.006,
                "device": "/dev/input/event5",
                "key_code": 17,
                "kind": "press",
                "action": 1,
            },
            {
                "run_id": "run-1",
                "attempt_id": "attempt-1",
                "timestamp": 100.04,
                "device": "/dev/input/event5",
                "key_code": 17,
                "kind": "release",
                "action": 0,
            },
        ]
    (root / "input_events.jsonl").write_text(
        "".join(json.dumps(event, sort_keys=True) + "\n" for event in events),
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
