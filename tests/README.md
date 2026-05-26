# Tests

Tests should follow the repository boundaries.

`unit/` contains focused tests for pure logic and small module contracts, such
as alignment offsets, frame-stack indexing, thresholding, metric calculations,
and dataset split validation.

`integration/` contains tests that cross module boundaries, such as raw capture
metadata to processed dataset manifest, policy inference through runtime
thresholding, or evaluation over saved rollout logs.

Hardware, game-window, or OS-input-dependent tests should be clearly marked so
they are not confused with deterministic local checks.
