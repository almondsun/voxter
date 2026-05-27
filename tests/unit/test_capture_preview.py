from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from voxter.capture.events import InputEventKind, RawInputEvent
from voxter.capture.frames import FrameCaptureRecord
from voxter.capture.preview import (
    PreviewGenerationError,
    generate_capture_preview,
)
from voxter.contracts import ActionState


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg is unavailable")
def test_generate_capture_preview_writes_mp4_and_action_subtitles(
    tmp_path: Path,
) -> None:
    frames = write_preview_fixture(tmp_path)

    result = generate_capture_preview(
        tmp_path,
        frames,
        [
            raw_event(0.015, InputEventKind.PRESS, ActionState.HELD),
            raw_event(0.035, InputEventKind.RELEASE, ActionState.RELEASED),
        ],
        fps=30.0,
    )

    preview_path = Path(result.preview_path)
    subtitle_path = Path(result.subtitle_path)
    assert preview_path.exists()
    assert preview_path.stat().st_size > 0
    subtitle_text = subtitle_path.read_text(encoding="utf-8")
    assert "W ACTION: RELEASED" in subtitle_text
    assert "W ACTION: HELD" in subtitle_text
    assert "EVENT: PRESS" in subtitle_text
    probe = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(preview_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert probe.returncode == 0, probe.stderr
    assert float(probe.stdout.strip()) > 0


def test_generate_capture_preview_rejects_missing_frame(tmp_path: Path) -> None:
    frames = write_preview_fixture(tmp_path)
    Path(frames[0].frame_path).unlink()

    with pytest.raises(Exception, match="preview frame is missing"):
        generate_capture_preview(tmp_path, frames, [], fps=30.0)


def test_generate_capture_preview_reports_missing_ffmpeg(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    frames = write_preview_fixture(tmp_path)
    monkeypatch.setattr("voxter.capture.preview.shutil.which", lambda _: None)

    with pytest.raises(PreviewGenerationError, match="ffmpeg"):
        generate_capture_preview(tmp_path, frames, [], fps=30.0)


def write_preview_fixture(root: Path) -> list[FrameCaptureRecord]:
    frames_dir = root / "frames"
    frames_dir.mkdir()
    actions = [ActionState.RELEASED, ActionState.HELD, ActionState.RELEASED]
    records = []
    for index, action in enumerate(actions):
        frame_path = frames_dir / f"{index:06d}.pgm"
        value = 40 + index * 80
        frame_path.write_bytes(b"P5\n16 16\n255\n" + bytes([value]) * 256)
        records.append(
            FrameCaptureRecord(
                run_id="run-1",
                attempt_id="attempt-1",
                frame_index=index,
                timestamp=index / 30.0 + 0.01,
                frame_path=str(frame_path),
                action=action,
                action_sample_timestamp=index / 30.0,
                geometry="0,0 16x16",
                capture_duration_s=0.001,
                capture_backend="test-pgm",
                image_format="pgm",
                frame_width=16,
                frame_height=16,
                source_width=16,
                source_height=16,
                capture_resized=False,
            )
        )
    return records


def raw_event(
    timestamp: float,
    kind: InputEventKind,
    action: ActionState,
) -> RawInputEvent:
    return RawInputEvent(
        run_id="run-1",
        attempt_id="attempt-1",
        timestamp=timestamp,
        device="/dev/input/event5",
        key_code=17,
        kind=kind,
        action=action,
    )
