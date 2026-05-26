# Configs

Versioned configuration files belong here.

Expected configuration areas include:

- capture settings: frame rate, capture region, timestamp source, input logger
- preprocessing settings: crop, resize, grayscale, normalization, frame stack
- dataset settings: alignment offset, split definitions, balancing strategy
- training settings: model stage, optimizer, class weights, sequence length
- evaluation settings: metrics, held-out sections, online trial parameters
- runtime settings: action threshold, hysteresis, deadline behavior

Configs should make timing-sensitive assumptions explicit, especially sampling
rate, label alignment offset, frame-stack length, sequence length, and action
thresholds.
