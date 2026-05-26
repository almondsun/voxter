# Security

Voxter touches screen capture, OS input control, file paths, datasets, external
game assets, and future model artifacts. Treat those as trust boundaries.

## Main Trust Boundaries

Capture:

- reads screen data
- observes or logs input state
- writes raw data

Control:

- sends input to the operating system or game
- may require user permissions

Data tooling:

- reads manifests and file paths
- creates processed artifacts
- may process untrusted or malformed files

Training and evaluation:

- load datasets, configs, checkpoints, and logs

Runtime:

- combines capture, preprocessing, model inference, and input execution in a
  live loop

## Privileged Information Rule

For the main real-time claim, policy input must not include:

- future frames
- full level scripts
- exact future obstacle positions
- fixed click timestamps
- symbolic level representations unavailable to a human
- section ID, seed, mode, speed, or progress metadata unless explicitly marked as
  a privileged-input ablation

Metadata may be used for reward, evaluation, diagnostics, and balancing only
when the boundary is explicit.

## File And Path Handling

Manifest paths must be validated before use.

Do not allow dataset manifests to write outside the intended artifact roots.

Prefer path joins rooted in configured base directories. Reject path traversal
where manifests or configs are user-editable.

## Subprocesses

If tools invoke external commands, pass arguments as arrays instead of shell
strings. Do not interpolate untrusted paths, level names, run IDs, or config
values into shell commands.

## Secrets

Do not log tokens, keys, local account secrets, or private paths beyond what is
needed for debugging.

Do not commit model-service keys, API keys, or private capture paths.

## Deserialization

Treat datasets, checkpoints, and serialized configs as untrusted unless produced
locally by the current workflow.

Avoid unsafe deserialization formats for untrusted input. If a framework loader
can execute code, document that risk and restrict its use to trusted artifacts.

## Safe Defaults

Runtime should fail closed on:

- failed capture
- failed input application
- invalid model output
- repeated deadline misses
- malformed configs
- missing alignment metadata in dataset construction

Do not continue silently in modes that can create misleading training data or
unsafe input behavior.

## Review Triggers

Use heightened security review for changes involving:

- path handling
- subprocesses
- input control
- capture permissions
- checkpoint loading
- parsing manifests or configs
- remote services
- privileged metadata boundaries
- generated code or external assets
