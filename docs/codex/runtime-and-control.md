# Runtime And Control

Runtime code is responsible for making the trained policy play in real time
under the same information constraints as a human player.

## Main Loop

The deployed loop is:

1. capture frame
2. preprocess frame
3. update frame stack or recurrent state
4. run policy inference
5. threshold probability into held/released action
6. apply input state through `control`
7. log runtime data
8. repeat at the configured rate

## Real-Time Budget

The runtime contract is:

```text
capture + preprocess + inference + input <= tick interval
```

For 60 Hz, the interval is about 16.67 ms.

For 120 Hz, the interval is about 8.33 ms.

Runtime logs should record enough timing data to identify which stage missed a
deadline.

## Policy Output

The policy output is a probability that the input should be held:

```text
p_t = P(action_held = 1 | history)
```

Runtime converts that probability into a binary action using a threshold:

```text
action_t = 1 if p_t > threshold else 0
```

Hysteresis may be used:

```text
press if p_t > press_threshold
release if p_t < release_threshold
otherwise keep previous action
```

Thresholds are timing-sensitive and must be configurable.

## Dropped Frames And Deadlines

Dropped-frame behavior must be explicit. Acceptable strategies include:

- hold previous action for one cycle
- release as a fail-safe
- skip inference and log a deadline miss
- terminate the run when misses exceed a configured limit

Do not silently ignore deadline misses.

## Control Boundary

`control` consumes binary held-state actions and applies them to the game or OS.

It must report:

- permission errors
- failed input application
- unsupported platform behavior
- timing failures when measurable

Do not call OS input APIs from policy, preprocessing, training, or evaluation
code.

## Runtime Logging

Runtime logs should include:

- timestamp
- capture duration
- preprocessing duration
- inference duration
- input duration
- total control-cycle duration
- policy probability
- thresholded action
- previous action
- deadline miss flag
- optional frame or observation reference
- optional diagnostic metadata kept out of policy input

## Reset And Terminal Behavior

Death, completion, manual reset, and environment failures must produce explicit
terminal states in logs. Runtime should not let reset screens or menus enter
normal gameplay traces without labels that allow preprocessing to remove them.

## Privileged Information

Runtime may use metadata for logging or evaluation. It must not pass privileged
metadata into the policy for the main transfer claim unless the experiment is
explicitly marked as a privileged-input ablation.
