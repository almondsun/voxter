from __future__ import annotations

import json
import subprocess
import sys
import time

import pytest

from voxter.contracts import ActionState, CaptureRecordError
from voxter.runtime import (
    RuntimeBenchmarkConfig,
    run_frame_driven_runtime_benchmark,
    run_runtime_benchmark,
)


def test_runtime_benchmark_records_stage_timings_and_actions() -> None:
    actions: list[ActionState] = []

    report = run_runtime_benchmark(
        RuntimeBenchmarkConfig(
            duration_s=1.0,
            target_hz=1000.0,
            max_cycles=3,
        ),
        capture_frame=lambda frame_index: f"frame-{frame_index}",
        preprocess_frame=lambda frame: frame.upper(),
        run_policy=lambda observation: 1.0 if observation.endswith("1") else 0.0,
        apply_action=actions.append,
    )

    assert report.measured_cycle_count == 3
    assert report.capture.count == 3
    assert report.total.count == 3
    assert [cycle.cycle_index for cycle in report.cycles] == [0, 1, 2]
    assert [cycle.action for cycle in report.cycles] == [
        ActionState.RELEASED,
        ActionState.HELD,
        ActionState.RELEASED,
    ]
    assert actions == [
        ActionState.RELEASED,
        ActionState.HELD,
        ActionState.RELEASED,
    ]


def test_runtime_benchmark_drops_warmup_cycles_from_report() -> None:
    report = run_runtime_benchmark(
        RuntimeBenchmarkConfig(
            duration_s=1.0,
            target_hz=1000.0,
            max_cycles=4,
            warmup_cycles=2,
        ),
        capture_frame=lambda frame_index: frame_index,
        preprocess_frame=lambda frame: frame,
        run_policy=lambda _observation: 0.0,
        apply_action=lambda _action: None,
    )

    assert report.measured_cycle_count == 2
    assert report.warmup_cycle_count == 2
    assert [cycle.cycle_index for cycle in report.cycles] == [2, 3]


def test_runtime_benchmark_reports_deadline_misses() -> None:
    def slow_capture(_frame_index: int) -> bytes:
        time.sleep(0.003)
        return b"frame"

    report = run_runtime_benchmark(
        RuntimeBenchmarkConfig(
            duration_s=1.0,
            target_hz=1000.0,
            max_cycles=2,
        ),
        capture_frame=slow_capture,
        preprocess_frame=lambda frame: frame,
        run_policy=lambda _observation: 0.0,
        apply_action=lambda _action: None,
    )

    assert report.missed_deadline_count == 2
    assert not report.passed_tick_budget
    assert all(cycle.deadline_missed for cycle in report.cycles)


def test_runtime_benchmark_rejects_invalid_probability() -> None:
    with pytest.raises(CaptureRecordError, match="policy probability"):
        run_runtime_benchmark(
            RuntimeBenchmarkConfig(
                duration_s=1.0,
                target_hz=60.0,
                max_cycles=1,
            ),
            capture_frame=lambda _frame_index: b"frame",
            preprocess_frame=lambda frame: frame,
            run_policy=lambda _observation: 1.2,
            apply_action=lambda _action: None,
        )


def test_frame_driven_runtime_benchmark_splits_wait_from_decision() -> None:
    actions: list[ActionState] = []

    report = run_frame_driven_runtime_benchmark(
        RuntimeBenchmarkConfig(
            duration_s=1.0,
            target_hz=60.0,
            max_cycles=3,
        ),
        receive_frame=lambda frame_index: f"frame-{frame_index}",
        preprocess_frame=lambda frame: frame.upper(),
        run_policy=lambda observation: 1.0 if observation.endswith("2") else 0.0,
        apply_action=actions.append,
    )

    assert report.schema_version == "frame-driven-runtime-benchmark-v1"
    assert report.measured_frame_count == 3
    assert report.frame_wait.count == 3
    assert report.decision.count == 3
    assert report.passed_decision_budget
    assert [frame.frame_index for frame in report.frames] == [0, 1, 2]
    assert [frame.action for frame in report.frames] == [
        ActionState.RELEASED,
        ActionState.RELEASED,
        ActionState.HELD,
    ]
    assert actions == [
        ActionState.RELEASED,
        ActionState.RELEASED,
        ActionState.HELD,
    ]


def test_frame_driven_runtime_benchmark_reports_decision_deadline_misses() -> None:
    def slow_preprocess(frame: bytes) -> bytes:
        time.sleep(0.003)
        return frame

    report = run_frame_driven_runtime_benchmark(
        RuntimeBenchmarkConfig(
            duration_s=1.0,
            target_hz=1000.0,
            max_cycles=2,
        ),
        receive_frame=lambda _frame_index: b"frame",
        preprocess_frame=slow_preprocess,
        run_policy=lambda _observation: 0.0,
        apply_action=lambda _action: None,
    )

    assert report.missed_deadline_count == 2
    assert not report.passed_decision_budget
    assert all(frame.deadline_missed for frame in report.frames)


def test_runtime_benchmark_cli_synthetic_smoke() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/runtime_benchmark.py",
            "--backend",
            "synthetic",
            "--max-cycles",
            "2",
            "--target-hz",
            "60",
            "--synthetic-capture-ms",
            "0",
            "--synthetic-preprocess-ms",
            "0",
            "--synthetic-inference-ms",
            "0",
            "--synthetic-control-ms",
            "0",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["schema_version"] == "runtime-benchmark-v1"
    assert payload["measured_cycle_count"] == 2
    assert payload["target_hz"] == 60.0


def test_runtime_benchmark_cli_frame_driven_synthetic_smoke() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/runtime_benchmark.py",
            "--backend",
            "synthetic",
            "--loop-mode",
            "frame-driven",
            "--max-cycles",
            "2",
            "--target-hz",
            "60",
            "--synthetic-capture-ms",
            "0",
            "--synthetic-preprocess-ms",
            "0",
            "--synthetic-inference-ms",
            "0",
            "--synthetic-control-ms",
            "0",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["schema_version"] == "frame-driven-runtime-benchmark-v1"
    assert payload["measured_frame_count"] == 2
    assert payload["target_hz"] == 60.0
