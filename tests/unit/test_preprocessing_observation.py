from __future__ import annotations

import pytest

from voxter.contracts import CaptureRecordError
from voxter.preprocessing import (
    OBSERVATION_SCHEMA_VERSION,
    ObservationConfig,
    preprocess_grayscale_observation,
    preprocess_rgb_observation,
)


def test_preprocess_rgb_observation_converts_to_grayscale_uint8() -> None:
    rgb = bytes(
        [
            255,
            0,
            0,
            0,
            255,
            0,
            0,
            0,
            255,
            255,
            255,
            255,
        ]
    )

    observation = preprocess_rgb_observation(
        rgb,
        source_width=2,
        source_height=2,
        config=ObservationConfig(width=2, height=2),
    )

    assert observation.schema_version == OBSERVATION_SCHEMA_VERSION
    assert observation.width == 2
    assert observation.height == 2
    assert observation.color_mode == "grayscale"
    assert observation.dtype == "uint8"
    assert observation.layout == "hw"
    assert observation.data == bytes([76, 149, 28, 255])
    assert observation.to_json_metadata()["byte_count"] == 4


def test_preprocess_rgb_observation_resizes_with_nearest_neighbor() -> None:
    rgb = bytes(
        [
            0,
            0,
            0,
            64,
            64,
            64,
            128,
            128,
            128,
            255,
            255,
            255,
        ]
    )

    observation = preprocess_rgb_observation(
        rgb,
        source_width=2,
        source_height=2,
        config=ObservationConfig(width=1, height=1),
    )

    assert observation.data == bytes([0])
    assert observation.width == 1
    assert observation.height == 1


def test_preprocess_grayscale_observation_passes_through_matching_shape() -> None:
    observation = preprocess_grayscale_observation(
        bytes([0, 64, 128, 255]),
        source_width=2,
        source_height=2,
        config=ObservationConfig(width=2, height=2),
    )

    assert observation.data == bytes([0, 64, 128, 255])
    assert observation.width == 2
    assert observation.height == 2


def test_preprocess_grayscale_observation_resizes_with_nearest_neighbor() -> None:
    observation = preprocess_grayscale_observation(
        bytes([0, 64, 128, 255]),
        source_width=2,
        source_height=2,
        config=ObservationConfig(width=1, height=1),
    )

    assert observation.data == bytes([0])


def test_preprocess_rgb_observation_rejects_short_payload() -> None:
    with pytest.raises(CaptureRecordError, match="smaller"):
        preprocess_rgb_observation(
            b"abc",
            source_width=2,
            source_height=2,
            config=ObservationConfig(width=2, height=2),
        )


def test_preprocess_grayscale_observation_rejects_short_payload() -> None:
    with pytest.raises(CaptureRecordError, match="smaller"):
        preprocess_grayscale_observation(
            b"a",
            source_width=2,
            source_height=2,
            config=ObservationConfig(width=2, height=2),
        )


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"width": 0, "height": 2}, "width"),
        ({"width": 2, "height": 0}, "height"),
        ({"width": 2, "height": 2, "color_mode": "rgb"}, "grayscale"),
        ({"width": 2, "height": 2, "dtype": "float32"}, "uint8"),
        ({"width": 2, "height": 2, "layout": "chw"}, "hw"),
    ],
)
def test_observation_config_rejects_unsupported_contracts(
    kwargs: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(CaptureRecordError, match=message):
        ObservationConfig(**kwargs)  # type: ignore[arg-type]
