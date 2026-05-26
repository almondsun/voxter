# Training And Evaluation

Training and evaluation must measure gameplay competence, not only frame-level
imitation.

## Training Stages

Stage 1 is reactive behavioral cloning:

- input: short stack of preprocessed frames
- model: CNN encoder plus binary head
- output: held-input probability
- objective: weighted binary cross-entropy

Stage 2 is memory-based sequential behavioral cloning:

- input: visual embedding plus previous action
- model: CNN encoder plus recurrent memory, initially GRU
- sequence data: contiguous windows, not shuffled individual frames
- objective: sequential weighted binary cross-entropy

Stage 3 is reinforcement fine-tuning:

- initialization: Stage 2 policy
- environment: real-time wrapper or simulator-like interface
- reward: progress, survival, section completion, death penalty, optional
  instability penalty
- regularization: behavioral cloning or KL penalty to preserve useful imitation

## Dataset Use

Training must respect dataset splits. Do not train and evaluate on randomly
intermixed frames from the same trajectory when reporting generalization.

Use metadata for balancing and analysis when available, but do not feed it to
the policy unless explicitly testing a privileged-input ablation.

## Offline Metrics

Offline metrics should include:

- binary cross-entropy
- accuracy
- balanced accuracy
- held-input precision, recall, and F1
- press transition precision and recall
- release transition precision and recall
- press timing error
- release timing error
- per-mode breakdown
- per-Ghost-Mode breakdown
- per-section or held-out-section breakdown

Frame-level accuracy is not enough because rare transition mistakes can kill the
agent.

## Online Metrics

Online metrics should include:

- survival time
- progress percentage
- section completion rate
- full-level completion rate
- death location distribution
- mean attempts to completion
- held-out generator success rate
- standard-level transfer performance
- performance under Ghost Mode
- latency and inference deadline misses

Online evaluation is the main behavioral test of Voxter.

## Benchmarks

Use three benchmark levels of evidence:

1. training-generator evaluation
2. held-out-generator evaluation
3. standard-level transfer evaluation

The project claim is strongest only when a fixed trained policy performs on
unseen standard levels without timestamp scripts or privileged policy inputs.

## Baselines

Important baselines:

- timestamp bot
- always release
- always hold
- reactive CNN
- CNN plus frame stack
- CNN plus GRU
- CNN plus LSTM
- temporal Transformer, if resources justify it
- human demonstrator reference

The timestamp bot is central because Voxter is meant to learn visual control
rather than fixed replay.

## Checkpoints And Artifacts

Training artifacts should record:

- code version or commit
- dataset manifest version
- preprocessing config
- alignment offset
- model architecture
- input resolution
- frame-stack length
- sequence length
- threshold settings used for evaluation
- class weights or sampler settings
- training metrics
- evaluation metrics

Without this metadata, offline and online results are hard to interpret.
