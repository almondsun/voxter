# Datasets

Training-ready dataset definitions belong here.

Use this folder for manifests, split files, sequence-window indexes, and dataset
metadata consumed by training and evaluation code. The actual frame payloads may
live under `data/raw` or `data/processed`.

Dataset records should support the conceptual schema from the model-theory
document: sample ID, run ID, frame index, timestamp, frame paths, binary
held-state action, alive/done flags, attempt ID, and optional section, mode,
speed, Ghost Mode, progress, or notes.

For sequential training, group records by run or attempt and preserve frame
order. Shuffling should happen at the trajectory or sequence-window level, not
at the individual-frame level.
