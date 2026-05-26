# Source

Application and library code belongs under `src/voxter`.

Keep side effects at subsystem boundaries. Core transformations, metrics, model
contract code, and alignment logic should be deterministic and independently
testable where practical.
