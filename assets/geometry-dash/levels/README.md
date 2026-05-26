# Geometry Dash Levels

Level files in this folder define gameplay environments used for data
collection, training-generator evaluation, or tests.

`training-level.gmd` is the randomized training-level asset currently present in
the repository. The model-theory document describes this level as an endless
generator of randomized sections derived from main RobTop levels, with variation
in gameplay form, cosmetic icon appearance, speed, Ghost Mode, and path choices.

Do not turn level files into model-input scripts for the main real-time policy.
They may be used to set up the environment, collect demonstrations, define
evaluation cases, or document provenance.
