# Codex Companion Docs

These files are implementation guidance for Voxter. The theory source remains
`research/model-theory/voxter-v1.tex`; these docs translate that theory into
repository engineering rules.

Read the most specific file for the subsystem being changed:

- `architecture.md`: package boundaries and dependency direction
- `build-and-test.md`: canonical validation path and expected future tooling
- `data-and-datasets.md`: capture records, preprocessing artifacts, splits
- `dataset-phases.md`: collection phase definitions and current Phase A batch
- `runtime-and-control.md`: real-time loop, input execution, deadline behavior
- `training-and-evaluation.md`: learning stages, metrics, and benchmarks
- `security.md`: trust boundaries, privileged information, safe defaults
- `performance.md`: latency budgets and profiling priorities
- `code-review.md`: repository-specific review checklist
- `ffi-and-interop.md`: future C/C++/Python boundary rules
- `algorithms.md`: standalone algorithm and metric implementation rules
- `frontend.md`: future UI guidance if a dashboard or tools UI is added
- `implementation-roadmap.md`: staged build-out order for the full project

If these docs conflict with a closer `AGENTS.md`, follow the closer instruction
file for its scope. If these docs conflict with the model-theory contract,
update the theory or document the deviation explicitly.
