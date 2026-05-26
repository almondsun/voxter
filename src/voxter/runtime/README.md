# Runtime

Runtime code owns the deployed real-time control loop.

The loop sequence is:

1. capture frame
2. preprocess frame
3. update frame stack or recurrent state
4. run policy inference
5. threshold probability into held/released action
6. apply input state through `control`
7. log runtime data
8. repeat at the target rate

Runtime must preserve the real-time contract:

```text
capture + preprocess + inference + input <= tick interval
```

Deadline behavior, dropped-frame handling, fail-safe behavior, thresholds, and
hysteresis settings should be explicit configuration rather than hidden defaults.
