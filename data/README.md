# Data

Project data is split by reproducibility boundary.

`raw/` contains source captures and logs. Treat these files as immutable once a
recording is accepted.

`processed/` contains artifacts derived from raw captures, such as resized
frames, normalized observations, aligned labels, and intermediate metadata.
These artifacts should be regenerable.

`datasets/` contains stable training and evaluation manifests, sequence windows,
and split definitions consumed by model code.

Do not split train and test data by random individual frames. Prefer trajectory,
section, seed, or section-family splits so evaluation measures generalization
instead of frame leakage.
