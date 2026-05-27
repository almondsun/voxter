from __future__ import annotations

from pathlib import Path

from voxter.capture.events import InputEventKind, RawInputEvent
from voxter.capture.frames import FrameCaptureError, FrameCaptureRecord
from voxter.capture.session import (
    CaptureSessionConfig,
    _build_summary,
    run_capture_session,
)
from voxter.contracts import ActionState


def test_build_summary_reports_event_and_frame_transition_counts() -> None:
    config = CaptureSessionConfig(
        output_dir=Path("/tmp/voxter-test"),
        run_id="run-1",
        attempt_id="attempt-1",
        geometry="1920,0 1920x1080",
        event_device="/dev/input/event10",
        duration_s=2.0,
        target_hz=2.0,
    )
    frames = [
        frame_record(0, ActionState.RELEASED),
        frame_record(1, ActionState.HELD),
        frame_record(2, ActionState.HELD),
        frame_record(3, ActionState.RELEASED),
    ]
    events = [
        raw_event(1.0, InputEventKind.PRESS, ActionState.HELD),
        raw_event(1.5, InputEventKind.RELEASE, ActionState.RELEASED),
    ]

    summary = _build_summary(
        config=config,
        capture_backend="grim-jpeg",
        frame_records=frames,
        input_events=events,
        capture_durations=[0.01, 0.02, 0.03, 0.04],
        dropped_frame_count=3,
        missed_deadline_estimate=1,
    )

    assert summary.frame_count == 4
    assert summary.effective_hz == 2.0
    assert summary.press_release_count == 2
    assert summary.frame_transition_count == 2
    assert summary.held_frame_count == 2
    assert summary.released_frame_count == 2
    assert summary.mean_capture_duration_ms == 25.0
    assert summary.dropped_frame_count == 3
    assert summary.missed_deadline_estimate == 1
    assert summary.image_format == "jpeg"
    assert summary.frame_width == 1920
    assert summary.frame_height == 1080
    assert summary.source_width == 1920
    assert summary.source_height == 1080
    assert not summary.capture_resized
    assert summary.capture_side_preprocessing == ()


def test_build_summary_reports_capture_side_resize_metadata() -> None:
    config = CaptureSessionConfig(
        output_dir=Path("/tmp/voxter-test"),
        run_id="run-1",
        attempt_id="attempt-1",
        geometry="1920,0 1920x1080",
        event_device="/dev/input/event5",
        duration_s=1.0,
        target_hz=60.0,
        backend="pipewire",
        output_width=960,
        output_height=540,
    )

    summary = _build_summary(
        config=config,
        capture_backend="pipewire-gstreamer-jpeg",
        frame_records=[frame_record(0, ActionState.RELEASED)],
        input_events=[],
        capture_durations=[0.01],
        dropped_frame_count=0,
        missed_deadline_estimate=0,
    )

    assert summary.image_format == "jpeg"
    assert summary.frame_width == 960
    assert summary.frame_height == 540
    assert summary.source_width == 1920
    assert summary.source_height == 1080
    assert summary.capture_resized
    assert summary.capture_side_preprocessing == ("resize",)


def test_run_capture_session_counts_dropped_frame_without_aborting(
    tmp_path: Path,
    monkeypatch,
) -> None:
    backend = FlakyFrameCapture()
    monkeypatch.setattr(
        "voxter.capture.session._make_capture_backend", lambda _: backend
    )
    monkeypatch.setattr("voxter.capture.session.InputEventReader", FakeEventReader)

    summary = run_capture_session(
        CaptureSessionConfig(
            output_dir=tmp_path,
            run_id="run-1",
            attempt_id="attempt-1",
            geometry="1920,0 1920x1080",
            event_device="/dev/input/event10",
            duration_s=0.08,
            target_hz=30.0,
        )
    )

    assert summary.frame_count >= 1
    assert summary.dropped_frame_count == 1
    assert (tmp_path / "capture_summary.json").exists()


class FlakyFrameCapture:
    def __init__(self) -> None:
        self.calls = 0

    @property
    def file_suffix(self) -> str:
        return ".ppm"

    @property
    def backend_name(self) -> str:
        return "fake"

    def close(self) -> None:
        return

    def capture(
        self,
        frame_path: Path,
        *,
        run_id: str,
        attempt_id: str | None,
        frame_index: int,
        action: ActionState,
        action_sample_timestamp: float,
    ) -> FrameCaptureRecord:
        self.calls += 1
        if self.calls == 1:
            raise FrameCaptureError("transient sample timeout")
        frame_path.parent.mkdir(parents=True, exist_ok=True)
        frame_path.write_bytes(b"P6\n1 1\n255\n\x00\x00\x00")
        return FrameCaptureRecord(
            run_id=run_id,
            attempt_id=attempt_id,
            frame_index=frame_index,
            timestamp=action_sample_timestamp + 0.001,
            frame_path=str(frame_path),
            action=action,
            action_sample_timestamp=action_sample_timestamp,
            geometry="1920,0 1920x1080",
            capture_duration_s=0.001,
            capture_backend=self.backend_name,
            image_format="ppm",
            frame_width=1920,
            frame_height=1080,
            source_width=1920,
            source_height=1080,
            capture_resized=False,
        )


class FakeEventReader:
    current_action = ActionState.RELEASED

    def __init__(
        self,
        event_device: str,
        *,
        run_id: str,
        attempt_id: str | None,
        key_code: int,
    ) -> None:
        self.event_device = event_device
        self.run_id = run_id
        self.attempt_id = attempt_id
        self.key_code = key_code

    def __enter__(self) -> FakeEventReader:
        return self

    def __exit__(self, *exc_info: object) -> None:
        return

    def read_available(self) -> list[RawInputEvent]:
        return []


def frame_record(frame_index: int, action: ActionState) -> FrameCaptureRecord:
    return FrameCaptureRecord(
        run_id="run-1",
        attempt_id="attempt-1",
        frame_index=frame_index,
        timestamp=float(frame_index),
        frame_path=f"frames/{frame_index:06d}.jpg",
        action=action,
        action_sample_timestamp=float(frame_index) - 0.01,
        geometry="1920,0 1920x1080",
        capture_duration_s=0.01,
        capture_backend="grim-jpeg",
        image_format="jpeg",
        frame_width=1920,
        frame_height=1080,
        source_width=1920,
        source_height=1080,
        capture_resized=False,
    )


def raw_event(
    timestamp: float,
    kind: InputEventKind,
    action: ActionState,
) -> RawInputEvent:
    return RawInputEvent(
        run_id="run-1",
        attempt_id="attempt-1",
        timestamp=timestamp,
        device="/dev/input/event10",
        key_code=17,
        kind=kind,
        action=action,
    )
