from __future__ import annotations

from pathlib import Path

import pytest

from voxter.capture.pipewire import (
    AsyncFrameWriter,
    EncodedFrame,
    GrayFrame,
    PipeWireFramePayload,
    RgbFrame,
    encode_gray_pgm,
    encode_rgb_ppm,
    pipewire_pipeline_description,
    write_encoded_frame,
    write_gray_pgm,
    write_rgb_ppm,
)
from voxter.contracts import CaptureRecordError


def test_pipewire_pipeline_description_uses_fd_node_and_appsink() -> None:
    description = pipewire_pipeline_description(pipewire_fd=7, node_id=42)

    assert "pipewiresrc fd=7 path=42" in description
    assert "video/x-raw,format=RGB" in description
    assert "appsink name=sink" in description
    assert "max-buffers=1" in description


def test_pipewire_pipeline_description_can_encode_jpeg() -> None:
    description = pipewire_pipeline_description(
        pipewire_fd=7,
        node_id=42,
        image_format="jpeg",
        jpeg_quality=65,
    )

    assert "pipewiresrc fd=7 path=42" in description
    assert "jpegenc quality=65" in description
    assert "appsink name=sink" in description


def test_pipewire_pipeline_description_can_downscale_before_sink() -> None:
    description = pipewire_pipeline_description(
        pipewire_fd=7,
        node_id=42,
        image_format="jpeg",
        output_width=960,
        output_height=540,
    )

    assert "videoscale" in description
    assert "video/x-raw,format=RGB,width=960,height=540" in description
    assert "jpegenc quality=70" in description


def test_pipewire_pipeline_description_can_pull_gray8() -> None:
    description = pipewire_pipeline_description(
        pipewire_fd=7,
        node_id=42,
        image_format="gray8",
        output_width=640,
        output_height=360,
    )

    assert "video/x-raw,format=GRAY8,width=640,height=360" in description
    assert "jpegenc" not in description
    assert "appsink name=sink" in description


@pytest.mark.parametrize(
    (
        "pipewire_fd",
        "node_id",
        "image_format",
        "jpeg_quality",
        "output_width",
        "output_height",
    ),
    [
        (-1, 42, "ppm", 70, None, None),
        (7, 0, "ppm", 70, None, None),
        (7, 42, "png", 70, None, None),
        (7, 42, "jpeg", 101, None, None),
        (7, 42, "jpeg", 70, 960, None),
        (7, 42, "jpeg", 70, 0, 540),
    ],
)
def test_pipewire_pipeline_description_rejects_invalid_ids(
    pipewire_fd: int,
    node_id: int,
    image_format: str,
    jpeg_quality: int,
    output_width: int | None,
    output_height: int | None,
) -> None:
    with pytest.raises(CaptureRecordError):
        pipewire_pipeline_description(
            pipewire_fd=pipewire_fd,
            node_id=node_id,
            image_format=image_format,
            jpeg_quality=jpeg_quality,
            output_width=output_width,
            output_height=output_height,
        )


def test_write_rgb_ppm_writes_binary_ppm(tmp_path: Path) -> None:
    output = tmp_path / "frame.ppm"
    frame = RgbFrame(
        width=2,
        height=1,
        data=bytes([255, 0, 0, 0, 255, 0]),
    )

    write_rgb_ppm(output, frame)

    assert output.read_bytes() == b"P6\n2 1\n255\n\xff\x00\x00\x00\xff\x00"


def test_encode_rgb_ppm_returns_binary_ppm_payload() -> None:
    payload = encode_rgb_ppm(
        RgbFrame(
            width=1,
            height=1,
            data=bytes([1, 2, 3]),
        )
    )

    assert payload == b"P6\n1 1\n255\n\x01\x02\x03"


def test_encode_gray_pgm_returns_binary_pgm_payload() -> None:
    payload = encode_gray_pgm(
        GrayFrame(
            width=2,
            height=1,
            data=bytes([1, 255]),
        )
    )

    assert payload == b"P5\n2 1\n255\n\x01\xff"


def test_write_gray_pgm_writes_binary_pgm(tmp_path: Path) -> None:
    output = tmp_path / "frame.pgm"

    write_gray_pgm(output, GrayFrame(width=2, height=1, data=bytes([1, 255])))

    assert output.read_bytes() == b"P5\n2 1\n255\n\x01\xff"


def test_write_rgb_ppm_rejects_short_buffers(tmp_path: Path) -> None:
    with pytest.raises(CaptureRecordError, match="smaller"):
        write_rgb_ppm(tmp_path / "bad.ppm", RgbFrame(width=2, height=1, data=b"abc"))


def test_write_encoded_frame_writes_payload(tmp_path: Path) -> None:
    output = tmp_path / "frame.jpg"

    write_encoded_frame(output, EncodedFrame(data=b"\xff\xd8data\xff\xd9"))

    assert output.read_bytes() == b"\xff\xd8data\xff\xd9"


def test_write_encoded_frame_rejects_empty_payload(tmp_path: Path) -> None:
    with pytest.raises(CaptureRecordError, match="non-empty"):
        write_encoded_frame(tmp_path / "bad.jpg", EncodedFrame(data=b""))


def test_pipewire_frame_payload_records_runtime_frame_metadata() -> None:
    payload = PipeWireFramePayload(
        data=b"rgb",
        image_format="rgb",
        frame_width=2,
        frame_height=1,
        source_width=4,
        source_height=2,
        capture_resized=True,
        capture_duration_s=0.001,
    )

    assert payload.image_format == "rgb"
    assert payload.frame_width == 2
    assert payload.source_width == 4
    assert payload.capture_resized


def test_async_frame_writer_flushes_queued_frames(tmp_path: Path) -> None:
    writer = AsyncFrameWriter(max_queue_size=2)
    first = tmp_path / "first.jpg"
    second = tmp_path / "second.jpg"

    writer.submit(first, b"one")
    writer.submit(second, b"two")
    writer.close()

    assert first.read_bytes() == b"one"
    assert second.read_bytes() == b"two"
