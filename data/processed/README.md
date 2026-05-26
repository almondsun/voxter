# Processed Data

Processed data contains reproducible artifacts derived from `data/raw`.

Typical outputs include:

- cropped or resized frames
- grayscale or normalized observations
- icon-standardized frames, if that pipeline is validated
- frame stacks
- aligned labels after measured system-delay correction
- cleaned gameplay prefixes with death aftermath removed

Every processed artifact should be traceable to raw inputs and the configuration
used to create it. Timing alignment is part of the dataset contract and must not
be guessed silently.
