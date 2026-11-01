This page is for the two AI assistants; users can skip it.
For an overview, see “How it works” in the README.

# Wake contract

[简体中文](heartbeat.zh-CN.md) · [Architecture](../docs/ARCHITECTURE.md) · [Night-watch setup](../docs/night-watch.md)

Night watch observes configured work through ordinary scripts, updates progress and records actionable events. A wake starts with `python scripts/agent.py --as GPT wake`; `status` supplies the complete workload.

1. Read inbox changes, exact event IDs and questions. Preserve malformed records for a concrete repair.
2. Read the relevant task, current instructions and recent exchange entries. Use the existing chat, frozen configuration and assigned write scope.
3. Handle the event; record the outcome with `events --ack EXACT_ID --result TEXT` once its action is complete.
4. Continue through eligible resources for Experiment, lead orders, open tasks and returned work. Advance independent authorized work while a separate decision is pending.
5. When only actual dependencies remain, record `patrol` with `--mood`, current work, the next task and the dependency.

Reference chat routing and GPU resource observations are deployment adapters. The bundled `status` lists tasks and issues even when `wake` has no inbox change.

## Notifications

Report meaningful completion, concrete failure and required owner action. Update healthy runs, ordinary progress and stable waiting in local records and stay quiet.

## Installation and scheduling

Use [night-watch setup](../docs/night-watch.md) for Windows task registration, cron examples, dry runs and manual commands. Keep task observation, provider-native wakes, board startup and Guardian recovery as separate controls. Diagnostic records belong in project-local runtime files.
