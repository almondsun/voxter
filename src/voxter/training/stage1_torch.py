"""Optional PyTorch Stage 1 optimization smoke."""

from __future__ import annotations

import importlib
import json
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any

from voxter.contracts import CaptureRecordError
from voxter.training.stage1_data import Stage1Batch, load_stage1_dataset_index

STAGE1_TORCH_SMOKE_SCHEMA_VERSION = "stage1-torch-smoke-v1"


@dataclass(frozen=True, slots=True)
class Stage1TorchSmokeConfig:
    """Configuration for a tiny Stage 1 optimization smoke."""

    dataset_dirs: tuple[Path, ...]
    batch_size: int = 8
    train_steps: int = 3
    learning_rate: float = 1e-3
    device: str = "auto"
    seed: int = 0


@dataclass(frozen=True, slots=True)
class Stage1TorchSmokeReport:
    """Machine-readable result for the tiny Stage 1 optimization smoke."""

    schema_version: str
    dataset_count: int
    sample_count: int
    held_count: int
    released_count: int
    batch_size: int
    train_steps: int
    device: str
    model_name: str
    input_shape: tuple[int, int, int, int]
    initial_loss: float
    final_loss: float
    parameter_delta_l1: float
    failures: tuple[str, ...]

    @property
    def passed(self) -> bool:
        """Return whether the optimization smoke satisfied the contract."""

        return not self.failures

    def to_json_dict(self) -> dict[str, object]:
        """Return a stable JSON-compatible representation."""

        return {
            "schema_version": self.schema_version,
            "dataset_count": self.dataset_count,
            "sample_count": self.sample_count,
            "held_count": self.held_count,
            "released_count": self.released_count,
            "batch_size": self.batch_size,
            "train_steps": self.train_steps,
            "device": self.device,
            "model_name": self.model_name,
            "input_shape": list(self.input_shape),
            "initial_loss": self.initial_loss,
            "final_loss": self.final_loss,
            "parameter_delta_l1": self.parameter_delta_l1,
            "passed": self.passed,
            "failures": list(self.failures),
        }


def run_stage1_torch_smoke(config: Stage1TorchSmokeConfig) -> Stage1TorchSmokeReport:
    """Run a tiny Stage 1 CNN optimization smoke with optional PyTorch."""

    if config.batch_size <= 0:
        raise CaptureRecordError("batch_size must be positive")
    if config.train_steps <= 0:
        raise CaptureRecordError("train_steps must be positive")
    if config.learning_rate <= 0:
        raise CaptureRecordError("learning_rate must be positive")

    torch, nn = _require_torch()
    torch.manual_seed(config.seed)

    index = load_stage1_dataset_index(config.dataset_dirs)
    batch = next(_iter_one_stage1_batch(index, batch_size=config.batch_size), None)
    if batch is None:
        raise CaptureRecordError("at least one Stage 1 batch is required")

    selected_device = _select_device(torch, config.device)
    model = _build_stage1_smoke_model(nn, in_channels=index.frame_stack_length)
    model.to(selected_device)
    model.train()

    inputs = _batch_inputs(torch, batch, device=selected_device)
    targets = _batch_targets(torch, batch, device=selected_device)
    criterion = nn.BCEWithLogitsLoss(
        pos_weight=torch.tensor(
            [index.released_count / index.held_count],
            dtype=torch.float32,
            device=selected_device,
        )
    )
    optimizer = torch.optim.AdamW(model.parameters(), lr=config.learning_rate)

    parameters_before = _flatten_parameters(torch, model).detach().clone()
    with torch.no_grad():
        initial_loss_tensor = criterion(model(inputs).squeeze(1), targets)
    initial_loss = float(initial_loss_tensor.item())

    final_loss = initial_loss
    for _ in range(config.train_steps):
        optimizer.zero_grad(set_to_none=True)
        logits = model(inputs).squeeze(1)
        loss = criterion(logits, targets)
        loss.backward()
        optimizer.step()
        final_loss = float(loss.item())

    parameters_after = _flatten_parameters(torch, model).detach()
    parameter_delta_l1 = float(
        torch.sum(torch.abs(parameters_after - parameters_before)).item()
    )
    failures = _smoke_failures(
        torch,
        initial_loss=initial_loss,
        final_loss=final_loss,
        parameter_delta_l1=parameter_delta_l1,
    )

    return Stage1TorchSmokeReport(
        schema_version=STAGE1_TORCH_SMOKE_SCHEMA_VERSION,
        dataset_count=len(index.dataset_dirs),
        sample_count=index.sample_count,
        held_count=index.held_count,
        released_count=index.released_count,
        batch_size=batch.batch_size,
        train_steps=config.train_steps,
        device=str(selected_device),
        model_name="stage1-smoke-cnn",
        input_shape=batch.shape,
        initial_loss=initial_loss,
        final_loss=final_loss,
        parameter_delta_l1=parameter_delta_l1,
        failures=tuple(failures),
    )


def write_stage1_torch_smoke_report(
    config: Stage1TorchSmokeConfig,
    output_path: Path,
) -> Stage1TorchSmokeReport:
    """Run a Stage 1 torch smoke and write the report JSON."""

    report = run_stage1_torch_smoke(config)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report.to_json_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def _iter_one_stage1_batch(index: Any, *, batch_size: int) -> Any:
    from voxter.training.stage1_data import iter_stage1_batches

    return iter_stage1_batches(index, batch_size=batch_size, max_batches=1)


def _require_torch() -> tuple[ModuleType, Any]:
    try:
        torch = importlib.import_module("torch")
    except ModuleNotFoundError as exc:
        raise CaptureRecordError(
            "PyTorch is required for Stage 1 optimization smoke. "
            'Install the training extra with `python -m pip install -e ".[train]"` '
            "on a Python version supported by PyTorch."
        ) from exc
    nn = torch.nn
    return torch, nn


def _select_device(torch: ModuleType, requested: str) -> Any:
    if requested == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if requested == "cuda" and not torch.cuda.is_available():
        raise CaptureRecordError("CUDA was requested but torch.cuda is unavailable")
    if requested not in {"cpu", "cuda"}:
        raise CaptureRecordError("device must be auto, cpu, or cuda")
    return torch.device(requested)


def _build_stage1_smoke_model(nn: Any, *, in_channels: int) -> Any:
    return nn.Sequential(
        nn.Conv2d(in_channels, 8, kernel_size=5, stride=4, padding=2),
        nn.ReLU(),
        nn.AdaptiveAvgPool2d((1, 1)),
        nn.Flatten(),
        nn.Linear(8, 1),
    )


def _batch_inputs(torch: ModuleType, batch: Stage1Batch, *, device: Any) -> Any:
    payload = bytearray().join(batch.frame_stacks)
    tensor = torch.frombuffer(payload, dtype=torch.uint8)
    tensor = tensor.reshape(batch.shape).to(device=device, dtype=torch.float32)
    return tensor / 255.0


def _batch_targets(torch: ModuleType, batch: Stage1Batch, *, device: Any) -> Any:
    return torch.tensor(batch.labels, dtype=torch.float32, device=device)


def _flatten_parameters(torch: ModuleType, model: Any) -> Any:
    return torch.cat([parameter.detach().flatten() for parameter in model.parameters()])


def _smoke_failures(
    torch: ModuleType,
    *,
    initial_loss: float,
    final_loss: float,
    parameter_delta_l1: float,
) -> list[str]:
    failures: list[str] = []
    if not bool(torch.isfinite(torch.tensor(initial_loss))):
        failures.append("initial_loss must be finite")
    if not bool(torch.isfinite(torch.tensor(final_loss))):
        failures.append("final_loss must be finite")
    if parameter_delta_l1 <= 0:
        failures.append("optimization step must change at least one parameter")
    return failures
