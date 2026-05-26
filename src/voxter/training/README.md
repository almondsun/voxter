# Training

Training code owns optimization workflows and experiment execution.

Expected workflows include:

- Stage 1 reactive behavioral cloning
- Stage 2 sequential behavioral cloning with contiguous sequence windows
- Stage 3 reinforcement fine-tuning from an imitation-initialized policy
- class weighting or sampler logic for binary action imbalance
- checkpointing and training metrics

Training data should be split by trajectory, section, seed, or section family.
Do not evaluate generalization with random frame-level splits.

Offline loss and accuracy are not sufficient evidence of gameplay competence.
Training workflows should produce artifacts that can be evaluated online through
the runtime and evaluation modules.
