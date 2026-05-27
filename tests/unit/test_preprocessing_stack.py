from __future__ import annotations

import pytest

from voxter.contracts import CaptureRecordError
from voxter.preprocessing import (
    FRAME_STACK_SCHEMA_VERSION,
    FrameStackConfig,
    Observation,
    RollingFrameStack,
)


def test_rolling_frame_stack_warms_up_by_repeating_first_observation() -> None:
    stacker = RollingFrameStack(FrameStackConfig(length=3, width=2, height=1))

    stack = stacker.update(observation(bytes([1, 2])))

    assert stack.schema_version == FRAME_STACK_SCHEMA_VERSION
    assert stack.length == 3
    assert stack.width == 2
    assert stack.height == 1
    assert stack.layout == "khw"
    assert stack.data == bytes([1, 2, 1, 2, 1, 2])
    assert stack.to_json_metadata()["byte_count"] == 6


def test_rolling_frame_stack_drops_oldest_and_appends_newest() -> None:
    stacker = RollingFrameStack(FrameStackConfig(length=3, width=1, height=1))

    first = stacker.update(observation(bytes([1]), width=1))
    second = stacker.update(observation(bytes([2]), width=1))
    third = stacker.update(observation(bytes([3]), width=1))
    fourth = stacker.update(observation(bytes([4]), width=1))

    assert first.data == bytes([1, 1, 1])
    assert second.data == bytes([1, 1, 2])
    assert third.data == bytes([1, 2, 3])
    assert fourth.data == bytes([2, 3, 4])


def test_rolling_frame_stack_rejects_mismatched_observation_contract() -> None:
    stacker = RollingFrameStack(FrameStackConfig(length=2, width=2, height=1))

    with pytest.raises(CaptureRecordError, match="width"):
        stacker.update(observation(bytes([1]), width=1))


def test_rolling_frame_stack_rejects_bad_byte_count() -> None:
    stacker = RollingFrameStack(FrameStackConfig(length=2, width=2, height=1))

    with pytest.raises(CaptureRecordError, match="byte count"):
        stacker.update(observation(bytes([1])))


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"length": 0, "width": 2, "height": 1}, "length"),
        ({"length": 2, "width": 0, "height": 1}, "width"),
        ({"length": 2, "width": 2, "height": 0}, "height"),
        ({"length": 2, "width": 2, "height": 1, "dtype": "float32"}, "uint8"),
        ({"length": 2, "width": 2, "height": 1, "layout": "hwk"}, "khw"),
    ],
)
def test_frame_stack_config_rejects_unsupported_contracts(
    kwargs: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(CaptureRecordError, match=message):
        FrameStackConfig(**kwargs)  # type: ignore[arg-type]


def observation(data: bytes, *, width: int = 2, height: int = 1) -> Observation:
    return Observation(
        schema_version="observation-v1",
        width=width,
        height=height,
        color_mode="grayscale",
        dtype="uint8",
        layout="hw",
        data=data,
    )
