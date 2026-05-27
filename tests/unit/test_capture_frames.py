from __future__ import annotations

import pytest

from voxter.capture.frames import (
    FrameCaptureRecord,
    MonitorGeometry,
    parse_geometry,
    validate_frame_records,
)
from voxter.contracts import ActionState, CaptureRecordError, RawCaptureRecord


def frame_record(frame_index: int, timestamp: float) -> FrameCaptureRecord:
    return FrameCaptureRecord(
        run_id="run-1",
        attempt_id="attempt-1",
        frame_index=frame_index,
        timestamp=timestamp,
        frame_path=f"frames/{frame_index:06d}.jpg",
        action=ActionState.HELD,
        action_sample_timestamp=timestamp - 0.01,
        geometry="1920,0 1920x1080",
        capture_duration_s=0.04,
        capture_backend="grim-jpeg",
        image_format="jpeg",
        frame_width=1920,
        frame_height=1080,
        source_width=1920,
        source_height=1080,
        capture_resized=False,
    )


def test_parse_geometry_accepts_grim_geometry_string() -> None:
    assert parse_geometry("1920,0 1920x1080") == MonitorGeometry(
        x=1920,
        y=0,
        width=1920,
        height=1080,
    )


@pytest.mark.parametrize("geometry", ["1920x1080", "0,0 0x1080", "0,0 1920x0"])
def test_parse_geometry_rejects_invalid_geometry(geometry: str) -> None:
    with pytest.raises(CaptureRecordError):
        parse_geometry(geometry)


def test_frame_capture_record_converts_to_raw_capture_record() -> None:
    raw = frame_record(0, 1.0).to_raw_capture_record()

    assert raw == RawCaptureRecord(
        run_id="run-1",
        attempt_id="attempt-1",
        frame_index=0,
        timestamp=1.0,
        frame_path="frames/000000.jpg",
        action=ActionState.HELD,
    )


def test_validate_frame_records_uses_shared_frame_contract() -> None:
    validate_frame_records([frame_record(0, 1.0), frame_record(1, 1.1)])


def test_validate_frame_records_rejects_negative_capture_duration() -> None:
    bad_record = FrameCaptureRecord(
        run_id="run-1",
        attempt_id="attempt-1",
        frame_index=0,
        timestamp=1.0,
        frame_path="frames/000000.jpg",
        action=ActionState.HELD,
        action_sample_timestamp=0.99,
        geometry="1920,0 1920x1080",
        capture_duration_s=-0.1,
        capture_backend="grim-jpeg",
        image_format="jpeg",
        frame_width=1920,
        frame_height=1080,
        source_width=1920,
        source_height=1080,
        capture_resized=False,
    )

    with pytest.raises(CaptureRecordError, match="capture_duration_s"):
        validate_frame_records([bad_record])
