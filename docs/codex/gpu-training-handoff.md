# GPU Training Handoff

This note records the first external GPU training target for Voxter. Keep this
as an operational profile, not a hard-coded training contract.

## Friend GPU Workstation

- OS: CachyOS Linux, Arch-based rolling release
- CPU: AMD Ryzen 5 5500, 6 cores / 12 threads
- RAM: 15 GB total, about 12 GB available during the reported check
- GPU: NVIDIA GeForce RTX 3050 6GB, GA107
- VRAM: 6144 MiB total, about 290 MiB used during the reported check
- NVIDIA driver: 595.71.05
- CUDA reported by driver: 13.2
- `nvcc`: not separately installed
- Python: 3.14.4
- Docker: not currently installed, can be installed if needed
- System packages: can be installed
- Data disk: 1.8 TB USB portable disk, not mounted during the reported check
- Network: about 842 Mbps down, 756 Mbps up, 14 ms ping

## Training Implications

The RTX 3050 6GB is enough for the first Stage 1 reactive policy experiments,
especially for the current accepted dataset:

- samples: 97,275
- observation: 640x360 grayscale `uint8`
- stack length: 4
- frame-stack payload: 4 x 640 x 360 bytes per sample
- class totals: 26,930 held and 70,345 released

Use conservative defaults:

- device: `auto`, preferring CUDA when `torch.cuda.is_available()`
- batch size: start with 8 or 16
- precision: start with fp32; add AMP only after the fp32 path is correct
- workers: start with 0 or 2, because the dataset is small and the disk may be USB
- checkpointing: write metadata every run, not only final model weights

Do not require a local CUDA toolkit for the first training path. PyTorch wheels
should provide their own CUDA runtime when installed with the matching official
index. The driver must be compatible with the selected wheel.

## Recommended Setup Path

Prefer a normal Python virtual environment first. Use Docker only if native
PyTorch/CUDA setup becomes messy.

Suggested initial commands on the GPU machine:

```bash
git clone <repo-url> voxter
cd voxter
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

After training dependencies are added, install them with the project-supported
command rather than ad hoc package pins.

The repository exposes training dependencies as an optional extra:

```bash
python -m pip install -e ".[train]"
```

Sanity checks:

```bash
nvidia-smi
python --version
python -c "import torch; print(torch.__version__, torch.cuda.is_available())"
df -h
free -h
```

## Data Handoff

For first Stage 1 training, send only the materialized dataset unless raw-frame
audit is needed:

```text
data/datasets/training-w-20260527-0001-stage1/
```

The raw capture remains useful for visual and preprocessing audit:

```text
data/raw/training-w-20260527-0001/
```

Package the materialized dataset from the local capture machine:

```bash
tar -czf /tmp/training-w-20260527-0001-stage1.tar.gz \
  -C data/datasets training-w-20260527-0001-stage1
sha256sum /tmp/training-w-20260527-0001-stage1.tar.gz
```

On the GPU machine:

```bash
mkdir -p data/datasets
tar -xzf training-w-20260527-0001-stage1.tar.gz -C data/datasets
```

## Code Requirements

Training code should remain hardware-agnostic:

- expose `--device auto|cpu|cuda`
- expose `--batch-size`
- expose `--num-workers`
- expose `--precision fp32|amp`
- write checkpoint metadata with dataset ID, manifest schema, `delta_sys`,
  observation shape, stack length, class weights, model name, and device
- fail clearly when CUDA is requested but unavailable

The friend workstation profile should influence default recommendations, not
public data formats or model architecture contracts.
