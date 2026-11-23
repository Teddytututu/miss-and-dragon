# Upgrade to 0.6 from 0.5 or 0.4.3

[简体中文](upgrade-0.6.zh-CN.md) · [Optional integrations](integrations.md)

Keep the existing source and complete data directory together as a rollback copy. Extract the selected 0.6 source archive into a separate folder, create its project environment and install `requirements.txt` with the same interpreter. Copy the existing project's records into the new installation's `data/`, then start the copied data on a separate loopback port:

```sh
python scripts/install_deps.py
python -m board start --data-dir data --port 18780
```

Use [agent installation](install-with-agent.md) for environment setup and dependency installation. For a read-only rehearsal after data initialization, add `--read-only` to the start command. Keep the original instance on its own data directory while reviewing the copy. Choose the cutover time after reviewing the task board, discussion, reports, schedule, identities and both themes.

## Existing project records

Keep `project.json`, `board.md`, `overview.json`, task cards, discussion ledgers and the complete `attachments/` tree. These preserve manual packet answer versions, custom artwork, reading state, service preferences and local records. Existing task and report files retain their current locations inside the copied data directory. The [0.5 upgrade guide](upgrade-0.5.md) describes the earlier stable report identity and manual-packet changes for installations coming directly from 0.4.3.

0.6 creates feature records when their corresponding actions are used. Existing projects can open with their current records; use the commands to create new feature state rather than manufacturing empty schemas by hand.

| Project-relative file or directory | Created or updated by |
|---|---|
| `attachments/current-assignments.json` | `integrations.py current --task …`; the latest explicit assignment per assistant |
| `attachments/work-records.json` | Continuity work receipts |
| `attachments/consumers/` | Event/inbox consumer acknowledgements |
| `attachments/delivery.json` | Versioned stage configuration, submission and review |
| `attachments/host-events.json` | Explicit host event enqueue, claim and settlement |
| `attachments/publications.json`, `attachments/published/` | Registration of an accepted report and its local dependency closure |
| `attachments/import-observers/` | Enabled directory-observation passes |
| `attachments/reply-results.jsonl` | Reply completion receipts |
| `attachments/accounts.json` | Explicit optional account initialization |
| `attachments/avatar-catalog/`, `attachments/avatar-choices/` | Installation-supplied raster catalog and selected crops |

`attachments/voice.json` remains a local voice preference file. Optional account, speech, hook, queue and service settings belong to the installation and should stay outside public source packages. Preserve existing manual packet metadata when importing another answer version.

The report checker reads private display names from `user_name` and the optional `report_internal_names` string array in `data/project.json`. Add the installation's own internal names there when checking reader-facing reports. The source checker carries generic rules; the configured names determine the private-name checks. Run `python templates/report-kit/check_report.py report.html --root data` to select the project data explicitly.

## New explicit commands

Run `python scripts/integrations.py --help` for the command list and `<command> --help` for arguments. Place `--data-dir` before the subcommand.

```sh
python scripts/integrations.py --data-dir data current --actor GPT --task T001 --stage implementation --artifact board.md --authorization "Explicit project assignment"
python scripts/integrations.py --data-dir data stage configure --task T001 --stage implementation --actor GPT --reviewer Claude
python scripts/integrations.py --data-dir data stage submit --task T001 --stage implementation --actor GPT --files report.md
```

The submit result returns the artifact `version`. The designated reviewer passes that exact value to `stage review --task T001 --stage implementation --actor Claude --version <version> --decision accept`. Stages can declare dependencies with `stage configure --depends <upstream-stage>` after the upstream stages exist. Changed submissions invalidate dependent stages; review binds to the current artifact contents.

`publish --task T001 --stage implementation --file report.md --title "Result"` registers an accepted current report in the local board. Here, publication means local report registration; external Git hosting and deployment remain separate actions.

Other new subcommands cover `import`, `watch`, `schedule`, `decision`, `event`, `reply`, `queue`, `gpu`, `budget`, `services`, `voice`, `mail` and `accounts`. Event delivery uses an explicit claim and transport outcome before settlement; the integration CLI manages the ledger while the host supplies actual transport. See [optional integrations](integrations.md) for plugin inputs and activation.

## Optional plugins stay opt-in

Ordinary startup keeps single-owner mode. Account mode requires initialization and `--accounts`; reply speech requires `enabled: true` in its voice configuration; directory observation requires `enabled: true` and one explicit `watch` call per pass. Hooks require the Owner to merge a generated template into the host configuration. Queue submission requires `--submit` and explicit SSH destination arguments. The process-control CLI defaults to identity preview and uses `--apply` for a separately authorized stop.

Service, GPU, quota and mail checks run when called. Local image choices stay empty until a catalog is supplied; bundled character art remains available. An upgrade preserves existing optional-service choices rather than automatically installing new watchers or changing host settings.

## Verify the copied installation and cut over

Open `http://127.0.0.1:18780/` and review existing tasks, discussion, report links and schedule. Check both language and theme selections; test only the optional integrations chosen for this installation. Complete a small task through its normal submission and review flow on the copied data. Inspect actual command results and local output files.

For source contributions, run `python scripts/check_eol.py`, `python -m pytest tests -q -p no:cacheprovider` and the documented JavaScript checks in [validation](validation.md). Keep source tests and sample artifacts separate from the copied project records.

At cutover, stop this project's old service through its normal launcher, start the chosen source with the reviewed data copy, and update project-specific launch paths through their documented installers. Login startup, host hooks and night-watch installation follow the Owner's explicit choices. Keep the original source and its matching data copy together for rollback.
