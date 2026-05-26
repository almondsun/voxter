# Preprocessing

Preprocessing code converts raw captures into model-ready observations and
aligned labels.

Expected responsibilities include:

- stable crop selection when non-game UI must be removed
- resizing to the configured model resolution
- grayscale conversion and pixel normalization
- optional icon standardization when implemented safely
- frame-stack construction
- label alignment after measured system-delay correction
- invalid segment removal, such as death aftermath or reset screens

Preprocessing must not introduce future information or privileged metadata into
model inputs. Timing alignment decisions should be reproducible from raw logs and
configuration.
