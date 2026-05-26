# FFI And Interop

The repository is currently documentation and Python-oriented scaffolding, but
the project may later use C or C++ for low-latency capture, preprocessing,
runtime control, or model-serving adapters. Any such boundary must be explicit.

## When To Add Native Code

Use C or C++ only when it improves correctness, latency, ABI stability, or access
to platform APIs enough to justify the boundary.

Good candidates:

- capture adapters
- input-control adapters
- image preprocessing hot paths
- runtime timing primitives
- stable C ABI wrappers around C++ internals

Poor candidates:

- ordinary experiment orchestration
- metrics that are not performance bottlenecks
- config parsing without a strong reason
- code added only for architectural ceremony

## Boundary Design

Keep native boundaries narrow and stable.

Prefer simple C-compatible boundary types when ABI stability matters:

- pointers plus explicit lengths
- fixed-width integer types
- explicit status codes
- caller-provided buffers with capacities
- opaque handles for owned native resources

Do not expose C++ STL types, exceptions, or object layouts across a C ABI.

## Ownership

Every interop function must document:

- who allocates memory
- who frees memory
- whether data is copied or borrowed
- whether pointers may be null
- how long borrowed data must remain valid
- whether buffers may alias
- required alignment or packing assumptions

No hidden ownership transfer.

## Error Model

Do not let C++ exceptions cross C or Python boundaries.

Translate native failures into one boundary error model:

- status code plus error buffer
- status enum plus retrievable last error
- Python exception at the adapter boundary

Use one model per subsystem.

## Threading And Reentrancy

Document whether native objects are:

- thread-safe
- thread-confined
- reentrant
- safe during callback execution

Do not use `volatile` as a threading primitive. Use real synchronization.

## Validation

Native or interop changes require stronger validation than pure Python docs or
tools:

- compile with warnings enabled
- unit tests for ownership and error paths
- sanitizer runs when available
- Python adapter tests, if Python calls native code
- stress or timing tests for runtime hot paths when relevant
