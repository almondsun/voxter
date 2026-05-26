# Code Review

Review Voxter changes against project contracts first, style second.

## Finding Priority

Prioritize findings in this order:

1. correctness
2. safety and security
3. contract clarity
4. validation evidence
5. maintainability
6. performance
7. UX at CLI or tooling boundaries
8. style consistency

## Stop-Ship Review Questions

Does the change leak privileged information into policy input?

Does it preserve binary held-state action semantics?

Does it maintain causal label alignment?

Does it split data by trajectory, section, seed, or equivalent rather than random
frames when reporting generalization?

Does it hide capture, preprocessing, inference, or input failures?

Does it silently ignore deadline misses?

Does it change a dataset, config, checkpoint, CLI, or log format without
documenting compatibility impact?

Does it add side effects to core policy, preprocessing logic, or metrics?

Does it use unsafe path or subprocess handling?

## Area-Specific Checks

Capture:

- timestamps are explicit
- input held-state is logged, not only click events
- calibration data is preserved
- side effects are isolated

Preprocessing:

- shape and dtype contracts are explicit
- alignment offset sign is unambiguous
- invalid gameplay segments are handled deliberately
- no future or privileged information enters model inputs

Policy:

- input history assumptions are explicit
- previous-action handling is correct for recurrent models
- output semantics are held probability
- model code is independent of capture and control APIs

Training:

- sequence ordering is preserved where required
- class weighting or balancing is documented
- checkpoint metadata is sufficient
- evaluation split is appropriate for the claim

Evaluation:

- transition metrics are included when action timing matters
- online metrics are not replaced by offline accuracy
- baselines are meaningful
- per-section or held-out results are reported when available

Runtime and control:

- deadline behavior is explicit
- threshold and hysteresis settings are configurable
- input failures are surfaced
- logs are sufficient for diagnosis

## Validation Expectations

Do not approve non-trivial changes without relevant validation when tools are
available. If validation cannot run because tooling or hardware is absent, the
review should say what remains unverified.
