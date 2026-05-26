# Frontend

Voxter does not currently have a frontend. If a UI is added later, it should
serve engineering workflows rather than marketing.

## Likely Interfaces

Potential future UI surfaces:

- capture session monitor
- runtime latency dashboard
- dataset browser
- evaluation report viewer
- death-location and progress analysis
- training run comparison

## Design Direction

Use a dense, operational interface optimized for repeated inspection:

- clear tables and charts
- stable navigation
- accessible controls
- visible loading, empty, partial, and error states
- no decorative landing page for internal tools

## Data Boundaries

A UI must not blur policy input and diagnostic metadata. If a view shows section
IDs, modes, progress, seeds, or reward metadata, label it as diagnostic or
evaluation data.

## Runtime Views

Runtime views should prioritize:

- current action state
- policy probability
- threshold settings
- stage timings
- deadline misses
- capture status
- input application status

Errors should be actionable and should not hide failed capture, failed control,
or missed deadlines.

## Validation

Frontend changes should be checked with the repository's future frontend tool
chain. Until such tooling exists, any UI work must define its own local
validation path in the final report.
