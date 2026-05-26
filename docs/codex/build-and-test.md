# Build And Test

This repository does not currently define a canonical build system, package
manifest, formatter, linter, or test runner. Until those exist, use the smallest
available validation that matches the changed files and state what remains
unverified.

## Current Canonical Commands

Documentation-only changes:

```bash
git diff --check
find . -name README.md -not -path './.git/*' -print | sort
```

If Markdown tooling is later added, the canonical documentation check should be
recorded here.

There is currently no canonical command for:

- Python tests
- linting
- formatting
- type checking
- package build
- model training smoke tests
- runtime smoke tests

Do not invent a passing validation result. If tooling is absent, say so.

## Expected Future Tooling

When Python package code is added, prefer a `pyproject.toml` based workflow with
explicit commands for:

- unit tests
- integration tests
- formatting
- linting
- type checking
- package build or import check

Recommended command names, once wired:

```bash
python -m pytest tests/unit
python -m pytest tests/integration
python -m ruff check .
python -m ruff format --check .
python -m mypy src
```

Only list these as canonical after the repository actually defines the tools and
configuration.

## Validation Selection

Use narrow validation for isolated docs, configs, pure metric code, or leaf
utilities.

Use full validation when changes touch multiple modules, dataset contracts,
training workflows, runtime orchestration, or user-visible CLI behavior.

Use escalated validation for:

- capture or control side effects
- dataset schema changes
- label alignment changes
- real-time runtime behavior
- reinforcement learning reward behavior
- security-sensitive path, subprocess, or privileged metadata handling
- future C/C++ or FFI boundaries

## Minimum Checks By Area

Documentation:

- `git diff --check`
- inspect rendered-sensitive Markdown manually when no Markdown linter exists

Dataset schema or preprocessing:

- unit tests for alignment, frame indexing, invalid segment handling, and schema
  validation
- representative manifest validation
- regression fixture for at least one aligned sequence

Policy:

- import or construction test
- shape and dtype test
- deterministic inference smoke test
- threshold compatibility test with runtime

Training:

- minimal batch loading test
- one tiny optimization-step smoke test when practical
- checkpoint metadata test when checkpointing is touched

Evaluation:

- metric unit tests, including imbalanced actions and missing transitions
- timing-window edge cases
- runtime-log parsing tests

Runtime and control:

- threshold and hysteresis unit tests
- deadline accounting tests
- mocked capture/control integration test
- live test only when the environment is available and explicitly in scope

## Reporting

Final reports must separate:

- commands run
- checks that passed
- checks that failed
- checks not run because tooling or environment is absent
- behavior still unverified
