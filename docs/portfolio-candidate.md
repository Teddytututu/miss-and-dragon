# Portfolio demonstration candidate

This candidate builds on the current public source and adds a repeatable path for trying the existing synthetic research workflow.

## Changes

- A single launcher creates or reuses the marked demo, starts the local board, and accepts an explicit port.
- Reset archives the previous marked demo before rebuilding it. The launcher restricts its data to a descendant of the repository's `work` directory.
- English and Chinese walkthroughs connect the two answer versions, review decisions, report, CSV and next task.
- Two implementation cases explain shared reading state and task claims using the current code paths and failure behavior.

Start with [the walkthrough](portfolio-demo.md). The launcher uses the standard board server and existing synthetic data generator. Your regular project continues using its own data directory.

## Try and adopt

Extract the source candidate into a new directory, install its requirements and run the guided demo. Test a separate copy of existing project data before selecting a replacement code and data pair. Keep the prior pair together for rollback.
