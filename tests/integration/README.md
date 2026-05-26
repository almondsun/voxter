# Integration Tests

Integration tests belong here.

Use this folder for tests that verify subsystem contracts across boundaries,
such as:

- raw capture metadata to processed manifest
- processed sequence windows to training batch
- policy output to runtime thresholding
- runtime logs to evaluation metrics
- capture/control timing calibration when the environment supports it

Mark tests that require Geometry Dash, a display server, hardware input
permissions, or large datasets.
