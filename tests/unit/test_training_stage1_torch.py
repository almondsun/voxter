from __future__ import annotations

from pathlib import Path

import pytest

from voxter.contracts import CaptureRecordError
from voxter.training.stage1_torch import (
    Stage1TorchSmokeConfig,
    run_stage1_torch_smoke,
)


def test_stage1_torch_smoke_validates_batch_size() -> None:
    with pytest.raises(CaptureRecordError, match="batch_size must be positive"):
        run_stage1_torch_smoke(Stage1TorchSmokeConfig(dataset_dirs=(), batch_size=0))


def test_stage1_torch_smoke_reports_missing_torch_dependency() -> None:
    if _torch_available():
        pytest.skip("missing-torch behavior only applies without torch installed")

    with pytest.raises(CaptureRecordError, match="PyTorch is required"):
        run_stage1_torch_smoke(Stage1TorchSmokeConfig(dataset_dirs=(Path("unused"),)))


def _torch_available() -> bool:
    try:
        import torch  # noqa: F401
    except ModuleNotFoundError:
        return False
    return True
