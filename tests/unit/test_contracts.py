from __future__ import annotations

from collections.abc import Callable

import pytest

from voxter.contracts import (
    ActionState,
    CaptureRecordError,
    RawCaptureRecord,
    TransitionKind,
    align_records,
    aligned_label_index,
    coerce_action_state,
    extract_action_transitions,
    validate_capture_records,
)


def record(
    frame_index: int,
    action: ActionState | int,
    *,
    timestamp: float | None = None,
    run_id: str = "run-1",
    attempt_id: str | None = "attempt-1",
) -> RawCaptureRecord:
    return RawCaptureRecord(
        run_id=run_id,
        attempt_id=attempt_id,
        frame_index=frame_index,
        timestamp=float(frame_index) if timestamp is None else timestamp,
        frame_path=f"frames/{frame_index:06d}.png",
        action=action,
    )


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (0, ActionState.RELEASED),
        (1, ActionState.HELD),
        (ActionState.RELEASED, ActionState.RELEASED),
        (ActionState.HELD, ActionState.HELD),
    ],
)
def test_coerce_action_state_accepts_binary_values(
    value: ActionState | int,
    expected: ActionState,
) -> None:
    assert coerce_action_state(value) is expected


@pytest.mark.parametrize("value", [-1, 2, True, False])
def test_coerce_action_state_rejects_non_contract_values(value: int | bool) -> None:
    with pytest.raises(CaptureRecordError):
        coerce_action_state(value)


def test_raw_capture_record_normalizes_integer_action() -> None:
    assert record(0, 1).action is ActionState.HELD


@pytest.mark.parametrize(
    "bad_record",
    [
        lambda: RawCaptureRecord("run-1", "attempt-1", -1, 0.0, "frame.png", 0),
        lambda: RawCaptureRecord("run-1", "attempt-1", 0, float("nan"), "frame.png", 0),
        lambda: RawCaptureRecord("run-1", "attempt-1", 0, 0.0, "", 0),
        lambda: RawCaptureRecord("run-1", "attempt-1", 0, 0.0, "frame.png", 2),
    ],
)
def test_raw_capture_record_rejects_invalid_fields(
    bad_record: Callable[[], RawCaptureRecord],
) -> None:
    with pytest.raises(CaptureRecordError):
        bad_record()


def test_validate_capture_records_accepts_monotonic_records() -> None:
    validate_capture_records([record(0, 0), record(1, 1), record(2, 1)])


def test_validate_capture_records_rejects_empty_input() -> None:
    with pytest.raises(CaptureRecordError):
        validate_capture_records([])


def test_validate_capture_records_rejects_duplicate_frame_index_per_attempt() -> None:
    records = [
        record(0, 0, timestamp=0.0),
        record(0, 1, timestamp=0.1),
    ]

    with pytest.raises(CaptureRecordError, match="duplicate frame_index"):
        validate_capture_records(records)


def test_validate_capture_records_allows_same_index_in_different_attempts() -> None:
    validate_capture_records(
        [
            record(0, 0, attempt_id="attempt-1"),
            record(0, 1, attempt_id="attempt-2"),
        ]
    )


def test_validate_capture_records_rejects_non_monotonic_timestamps() -> None:
    records = [
        record(0, 0, timestamp=1.0),
        record(1, 1, timestamp=0.5),
    ]

    with pytest.raises(CaptureRecordError, match="monotonic"):
        validate_capture_records(records)


def test_extract_action_transitions_derives_press_and_release_events() -> None:
    transitions = extract_action_transitions([0, 0, 1, 1, 0, 1])

    assert [(item.index, item.kind) for item in transitions] == [
        (2, TransitionKind.PRESS),
        (4, TransitionKind.RELEASE),
        (5, TransitionKind.PRESS),
    ]
    assert transitions[0].previous_action is ActionState.RELEASED
    assert transitions[0].current_action is ActionState.HELD


def test_aligned_label_index_uses_project_delta_sys_sign_convention() -> None:
    assert aligned_label_index(frame_index=10, delta_sys=3) == 13
    assert aligned_label_index(frame_index=10, delta_sys=-2) == 8


def test_aligned_label_index_rejects_negative_frame_index() -> None:
    with pytest.raises(CaptureRecordError):
        aligned_label_index(frame_index=-1, delta_sys=0)


def test_align_records_uses_later_action_for_positive_delta_sys() -> None:
    samples = align_records(
        [
            record(0, 0),
            record(1, 0),
            record(2, 1),
            record(3, 1),
        ],
        delta_sys=2,
    )

    assert [(sample.record.frame_index, sample.label_index) for sample in samples] == [
        (0, 2),
        (1, 3),
    ]
    assert [sample.action_label for sample in samples] == [
        ActionState.HELD,
        ActionState.HELD,
    ]


def test_align_records_drops_out_of_range_samples() -> None:
    samples = align_records([record(0, 0), record(1, 1)], delta_sys=1)

    assert [(sample.record.frame_index, sample.label_index) for sample in samples] == [
        (0, 1)
    ]


def test_align_records_does_not_cross_attempt_boundaries() -> None:
    samples = align_records(
        [
            record(0, 0, attempt_id="attempt-1"),
            record(1, 1, attempt_id="attempt-1"),
            record(0, 1, attempt_id="attempt-2"),
        ],
        delta_sys=1,
    )

    assert len(samples) == 1
    assert samples[0].record.attempt_id == "attempt-1"
    assert samples[0].label_record.attempt_id == "attempt-1"
