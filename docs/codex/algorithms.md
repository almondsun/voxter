# Algorithms

Algorithm implementations should be small, testable, and explicit about
contracts.

## General Rule

Write one pure implementation plus a thin adapter for file, CLI, runtime, or
framework integration.

State:

- input shape
- output shape
- dtype or numeric domain
- indexing convention
- time complexity
- memory complexity
- assumptions about missing, malformed, or boundary inputs

## Voxter-Specific Algorithms

Important algorithmic areas:

- label alignment by `delta_sys`
- frame-stack construction
- valid prefix extraction around death or reset
- action transition extraction
- press and release timing matching
- weighted binary cross-entropy bookkeeping
- sequence-window generation
- dataset split validation
- threshold and hysteresis
- reward computation
- deadline accounting

Each should have unit tests covering edge cases.

## Timing And Indexing

Timing-sensitive algorithms must state whether they operate on:

- wall-clock timestamps
- game ticks
- capture frame indexes
- dataset sequence indexes

Do not mix these silently.

Alignment code must preserve the model-theory sign convention when persisting or
reporting offsets.

## Transition Metrics

Press and release events are derived from adjacent held-state labels. Edge cases
must be explicit for the first frame of a sequence.

Matching predicted transitions to demonstration transitions should define:

- tolerance window
- one-to-one or many-to-one matching behavior
- behavior when one side has no transitions
- units of timing error

## Numerical Behavior

Metric code should handle:

- empty sequences
- all-held sequences
- all-released sequences
- no predicted transitions
- no target transitions
- NaN or invalid model probabilities

Do not hide invalid numeric states. Return structured missing metrics or raise
clear exceptions, depending on the caller contract.
