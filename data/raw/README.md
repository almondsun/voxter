# Raw Data

Raw captures and source logs belong here.

A raw capture should preserve enough information to reconstruct training samples,
debug timing, and validate deployment assumptions. At minimum, keep:

- raw frame path or frame payload
- binary held-state input
- timestamp or game-tick index
- run and attempt identity when available

Useful optional metadata includes alive/done state, progress, section ID, mode,
speed, Ghost Mode setting, random seed, and notes. Metadata may be used for
analysis, balancing, reward, and evaluation, but privileged metadata should not
be fed to the deployed policy for the main real-time claim.
