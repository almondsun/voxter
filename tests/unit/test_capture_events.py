from __future__ import annotations

import struct

import pytest

from voxter.capture.events import (
    EV_KEY,
    KEY_KPPLUS,
    KEY_W,
    LINUX_INPUT_EVENT,
    InputEventKind,
    KernelInputEvent,
    RawInputEvent,
    RawTerminalEvent,
    raw_input_event_from_kernel,
    raw_terminal_event_from_kernel,
    reconstruct_held_state,
    unpack_input_events,
    validate_input_events,
    validate_terminal_events,
)
from voxter.contracts import ActionState, CaptureRecordError


def pack_event(
    *,
    seconds: int,
    microseconds: int,
    event_type: int,
    code: int,
    value: int,
) -> bytes:
    return LINUX_INPUT_EVENT.pack(seconds, microseconds, event_type, code, value)


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
        key_code=KEY_W,
        kind=kind,
        action=action,
    )


def test_unpack_input_events_decodes_structs_and_ignores_trailing_bytes() -> None:
    data = (
        pack_event(
            seconds=10,
            microseconds=500_000,
            event_type=EV_KEY,
            code=KEY_W,
            value=1,
        )
        + b"partial"
    )

    events = unpack_input_events(data)

    assert events == [
        KernelInputEvent(
            timestamp=10.5,
            event_type=EV_KEY,
            code=KEY_W,
            value=1,
        )
    ]


@pytest.mark.parametrize(
    ("value", "expected_kind", "expected_action"),
    [
        (1, InputEventKind.PRESS, ActionState.HELD),
        (0, InputEventKind.RELEASE, ActionState.RELEASED),
        (2, InputEventKind.REPEAT, ActionState.HELD),
    ],
)
def test_raw_input_event_from_kernel_maps_w_key_values(
    value: int,
    expected_kind: InputEventKind,
    expected_action: ActionState,
) -> None:
    event = raw_input_event_from_kernel(
        KernelInputEvent(
            timestamp=12.25,
            event_type=EV_KEY,
            code=KEY_W,
            value=value,
        ),
        run_id="run-1",
        attempt_id="attempt-1",
        device="/dev/input/event10",
    )

    assert event is not None
    assert event.kind is expected_kind
    assert event.action is expected_action


def test_raw_input_event_from_kernel_filters_other_event_types_and_keys() -> None:
    assert (
        raw_input_event_from_kernel(
            KernelInputEvent(timestamp=1.0, event_type=0, code=KEY_W, value=1),
            run_id="run-1",
            attempt_id="attempt-1",
            device="/dev/input/event10",
        )
        is None
    )
    assert (
        raw_input_event_from_kernel(
            KernelInputEvent(timestamp=1.0, event_type=EV_KEY, code=30, value=1),
            run_id="run-1",
            attempt_id="attempt-1",
            device="/dev/input/event10",
        )
        is None
    )


def test_raw_terminal_event_from_kernel_maps_numpad_plus_press() -> None:
    event = raw_terminal_event_from_kernel(
        KernelInputEvent(
            timestamp=12.5,
            event_type=EV_KEY,
            code=KEY_KPPLUS,
            value=1,
        ),
        run_id="run-1",
        attempt_id="attempt-1",
        device="/dev/input/event10",
    )

    assert event == RawTerminalEvent(
        run_id="run-1",
        attempt_id="attempt-1",
        timestamp=12.5,
        device="/dev/input/event10",
        key_code=KEY_KPPLUS,
        kind=InputEventKind.PRESS,
        terminal_type="death",
    )


def test_raw_terminal_event_from_kernel_ignores_release_and_other_keys() -> None:
    assert (
        raw_terminal_event_from_kernel(
            KernelInputEvent(
                timestamp=12.5,
                event_type=EV_KEY,
                code=KEY_KPPLUS,
                value=0,
            ),
            run_id="run-1",
            attempt_id="attempt-1",
            device="/dev/input/event10",
        )
        is None
    )
    assert (
        raw_terminal_event_from_kernel(
            KernelInputEvent(timestamp=12.5, event_type=EV_KEY, code=KEY_W, value=1),
            run_id="run-1",
            attempt_id="attempt-1",
            device="/dev/input/event10",
        )
        is None
    )


def test_validate_terminal_events_rejects_non_monotonic_stream() -> None:
    with pytest.raises(CaptureRecordError, match="monotonic"):
        validate_terminal_events(
            [
                RawTerminalEvent(
                    run_id="run-1",
                    attempt_id="attempt-1",
                    timestamp=2.0,
                    device="/dev/input/event10",
                    key_code=KEY_KPPLUS,
                    kind=InputEventKind.PRESS,
                    terminal_type="death",
                ),
                RawTerminalEvent(
                    run_id="run-1",
                    attempt_id="attempt-1",
                    timestamp=1.0,
                    device="/dev/input/event10",
                    key_code=KEY_KPPLUS,
                    kind=InputEventKind.PRESS,
                    terminal_type="death",
                ),
            ]
        )


def test_reconstruct_held_state_ignores_repeat_events_by_default() -> None:
    timeline = reconstruct_held_state(
        [
            raw_event(1.0, InputEventKind.PRESS, ActionState.HELD),
            raw_event(1.1, InputEventKind.REPEAT, ActionState.HELD),
            raw_event(1.2, InputEventKind.RELEASE, ActionState.RELEASED),
        ]
    )

    assert timeline == [
        (1.0, ActionState.HELD),
        (1.2, ActionState.RELEASED),
    ]


def test_validate_input_events_rejects_non_monotonic_stream() -> None:
    with pytest.raises(CaptureRecordError, match="monotonic"):
        validate_input_events(
            [
                raw_event(2.0, InputEventKind.PRESS, ActionState.HELD),
                raw_event(1.0, InputEventKind.RELEASE, ActionState.RELEASED),
            ]
        )


def test_linux_input_event_struct_matches_expected_size() -> None:
    assert LINUX_INPUT_EVENT.size == struct.calcsize("llHHI")
