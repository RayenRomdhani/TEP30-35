# Project history: how the study was built

This folder is the lab notebook. If you want to *learn* the topic, start with the [README](../../README.md) instead; come here when you want to check how a result was produced or why a decision was taken.

The study was built in five phases, each ending with evidence before the next one started.

| Phase | What happened | Write-up |
|---|---|---|
| 1 | A one-bus toy model of Tunisia, to learn the method and test the code | [phase1-toy-model.md](phase1-toy-model.md) |
| 2 | PyPSA-Earth installed on Windows and the 2-node Tunisia network built | [phase2-base-network.md](phase2-base-network.md) |
| 3 | The network checked against official 2024 statistics and calibrated | [phase3-validation.md](phase3-validation.md) |
| 4 | The 11 scenarios built, solved and checked | [phase4-scenarios.md](phase4-scenarios.md) |
| 5 | Figures, report, slides and the reusable skill | (this repository's README and `report/`) |

Other records:

- [plan.md](plan.md): the task-by-task plan the study followed, with every step ticked.
- [config-changes.md](config-changes.md): every software install and every change to PyPSA-Earth's settings, with the reason.
- [evidence/phase2-run-logs.txt](evidence/phase2-run-logs.txt): verbatim log lines behind the Phase 2 timing figures.
- [specs/](specs/): the design documents: the study itself, and this reorganisation of the repository.
- [plans/](plans/): the plan for this reorganisation.

Numbers in these files were correct when written. Where a later phase changed something (for example a calibration), the later write-up says so.
