# Performance

Voxter performance is primarily about real-time latency and reliability, not raw
throughput.

## Runtime Budget

The deployed control cycle must satisfy:

```text
capture + preprocess + inference + input <= tick interval
```

Target intervals:

- 60 Hz: about 16.67 ms
- 120 Hz: about 8.33 ms

Every runtime implementation should make these stage timings measurable.

## Priorities

Optimize in this order:

1. correctness and causal alignment
2. stable real-time control
3. deadline miss reduction
4. memory use and artifact size
5. training throughput

Do not trade away causal correctness for speed.

## Hot Paths

Expected hot paths:

- screen capture
- frame resize and grayscale conversion
- frame-stack update
- model inference
- threshold or hysteresis
- input application
- runtime logging

Avoid repeated allocations or unnecessary copies in these paths once the first
correct implementation exists.

## Measurement

Runtime logs should capture per-stage timings:

- capture duration
- preprocessing duration
- inference duration
- input duration
- total cycle duration
- deadline miss flag

Measure before optimizing. A model that is accurate but misses deadlines is
invalid for the real-time claim.

## Model Complexity

Start with the simplest serious architecture:

- CNN plus frame stack for Stage 1
- CNN plus GRU for Stage 2

Introduce LSTM, Transformer, or higher-resolution inputs only when metrics show
the simpler model is insufficient and latency budget allows the added cost.

## Dataset And Training Throughput

Training throughput matters, but it is secondary to dataset correctness. Avoid
optimizations that obscure:

- alignment offset
- sequence ordering
- split identity
- preprocessing provenance
- class or mode balancing

Cache processed artifacts only when the cache records enough configuration to be
reproducible.

## Boundary Crossing

If future C/C++ acceleration is added, batch expensive operations where possible
and keep Python/native boundaries coarse. Do not cross language boundaries once
per pixel, per object, or per tiny metric operation in hot paths.
