# Optional integrations

[简体中文](integrations.zh-CN.md) · [Upgrade to 0.6](upgrade-0.6.md)

The modules in `board/plugins/` supply local adapters. Importing them starts no service. A standard `python -m board start` uses the single-owner loopback board. Optional commands run only when explicitly invoked; directory observation, reply speech and account mode have the additional switches described below. Keep installation-specific settings and credentials in local files outside the source archive.

Run commands from the project root with the project's Python interpreter. `scripts/integrations.py --data-dir data` selects the project records; put `--data-dir` before the subcommand. Each command prints a JSON result.

## Queue protocol

`board/plugins/queue_protocol.py` validates portable job tickets and checks loading admission from supplied resource measurements.

```sh
python scripts/integrations.py --data-dir data queue --input queue-input.json
```

The input contains `ticket`, `policy` and `sample`, with optional Unix timestamp `now`. A ticket requires `id`, `task`, `job_group`, absolute POSIX `cwd`, `cmd`, `next`, positive `vram_gb`, `mem_gb`, `max_seconds`, nonnegative integer `priority` and `allowed_cards`. Policy supplies `cards` and may set `max_cards`, `disk_reserve_gb`, `loading_reserve_gb` and `max_age_seconds`; the sample supplies `at`, `ram_free_gb`, `disk_free_gb`, `running_cards` and `gpus` entries with `card` and `free_gb`.

The default command only validates and calculates. Explicit submission adds `--submit --host <ssh-host> --queue-root <absolute-posix-directory>` after the input argument. It uses existing SSH batch authentication and publishes a ticket atomically into the remote `pending/` directory after admission succeeds. The remote queue directory needs `pending/`, `running/` and `done/`; running jobs and queue execution remain the responsibility of that installation's dispatcher. See [optional GPU dispatcher](optional-gpu-dispatcher.md).

## Voice transport

`board/plugins/voice_backend.py` runs a configured argument list and accepts playback only when the backend returns JSON with `"played": true` and exit code zero.

```sh
python scripts/integrations.py --data-dir data voice --config voice-backend.json --actor GPT --text "The result is ready."
python scripts/integrations.py --data-dir data reply --actor GPT --text-file reply.md
```

The direct `voice` command is itself an explicit playback request. Its configuration needs `backend_command`, a list such as `["python", "local_speech_backend.py"]`; `backend_timeout` defaults to 120 seconds and accepts up to 600. The backend receives UTF-8 JSON containing `who` and `text` on standard input.

The `reply` command reads `data/attachments/voice.json` unless `--config` supplies another file. Reply speech is off by default: set `enabled` to `true` and provide the backend settings to enable it. Optional `mute_until` maps `GPT` or `Claude` to a timezone-aware deadline. Reply receipts go to `attachments/reply-results.jsonl`; the body stays in the supplied text file. Both entry points serialize playback with `attachments/voice.lock`.

## Host hooks

`board/plugins/host_hooks.py` generates command-hook templates for an explicitly selected workspace and host.

```sh
python board/plugins/host_hooks.py --config host-hooks.json --template claude
python board/plugins/host_hooks.py --config host-hooks.json --template codex
```

The configuration requires an existing `workspace`. For compaction recovery, provide a project-relative `pointer` and the allowed `sessions` IDs. Optional `reply_rules` entries contain `id` and `pattern`; `protected_roots` lists explicitly protected read scopes. Claude templates cover `UserPromptSubmit`, `PreToolUse` and `Stop`; Codex templates cover `SessionStart` and `Stop`. The script reads host event JSON from standard input when called without `--template`. Template generation leaves host settings untouched; the Owner reviews and merges selected hooks into the host's own configuration. Fresh installations have no installed plugin hooks.

## File import and directory observation

`board/plugins/file_import.py` performs one bounded pass over an explicitly configured directory.

```sh
python scripts/integrations.py --data-dir data import --packet example path/to/answer.md
python scripts/integrations.py --data-dir data watch --config import-watch.json
```

The `import` command attaches named files to an existing manual packet; `--version` selects an answer version. Observation is off by default. To enable one pass, use a configuration with `enabled: true`, absolute `directory`, existing packet name `packet`, optional `version_id` and `settle_seconds` of at least 1. A file first establishes its observed signature; a later invocation imports it once the signature has stayed stable for the settling interval. Observation records live in `attachments/import-observers/`. The pass skips symlinks, cloud placeholders and files over 50 MiB. Repeated scheduling is an explicit caller choice. See [manual packets](manual-packets.md).

## Mail tone checks

`board/plugins/mail_lint.py` returns rule-level feedback for a named English email draft and reads visible text from HTML drafts.

```sh
python scripts/integrations.py --data-dir data mail draft.md
python board/plugins/mail_lint.py draft.html --json
```

This check runs on demand. The standalone command returns exit code 1 when it finds issues; the integration command returns an `issues` list. Draft editing and sending remain separate actions.

## Process control

`board/plugins/process_control.py` previews or terminates one explicitly registered process.

```sh
python board/plugins/process_control.py --record process-record.json --pid <pid>
```

The record needs `pid`, `create_time` and `executable` from the actual process. The default invocation previews the identity check. Add `--apply` only for an authorized stop. The adapter checks PID, executable and creation time again before termination and excludes its own process. Importing or observing processes triggers no stop.

## Accounts and visitors

`board/plugins/accounts.py` stores password hashes and versioned signed sessions; `account_roles.py` defines Owner and guest permissions; `account_server.py` exposes the optional loopback account server.

```sh
python scripts/integrations.py --data-dir data accounts init
python scripts/integrations.py --data-dir data accounts password --person owner
python scripts/integrations.py --data-dir data accounts password --person visitor
python -m board start --data-dir data --accounts --port 8780
```

Initialization creates `attachments/accounts.json` with one Owner and one visitor. Password commands prompt locally. Ordinary startup leaves account mode off; `--accounts` selects it after initialization. `accounts revoke --person visitor` invalidates the visitor's existing sessions. A guest sees the guest board and discussion and can select their own avatar. The account server keeps the direct loopback boundary; enabling it creates no public listener or proxy deployment.

## Service observation

`board/plugins/services.py` checks an explicit local service catalog and provides a read-only Windows listener inventory.

```sh
python scripts/integrations.py --data-dir data services --config local-services.json
```

The catalog is a JSON list of entries with `url` and optional descriptive fields, such as `[{"name":"Local board","url":"http://127.0.0.1:8780/"}]`. Checks accept direct `http://127.0.0.1` URLs and report the HTTP status. Invoke the command to collect a snapshot; a standard board startup installs no service observer. Listener inventory is Windows-specific. Observation leaves the inspected services running.

## Quota admission

`board/plugins/budget.py` calculates a host quota decision from explicit policy and observed usage.

```sh
python scripts/integrations.py --data-dir data budget --input budget-input.json
```

The input contains `state`, `sample` and `policy`, plus optional `now` and `direct`. The sample has `account`, percentage `used` and Unix reset timestamp `reset`. Policy has `daily_percent`, `reserve_percent`, `max_daily_turns`, `interval_seconds` and optional `timezone_offset_hours`. `now` accepts a timezone-aware ISO timestamp or Unix timestamp. The output contains the decision and updated state; the caller persists that state and records actual dispatches. This pure calculation starts no host job or polling loop. The board's built-in patrol scheduler retains its own settings; see [quota](quota.md).

## GPU observation

`board/plugins/gpu_observer.py` projects supplied queue and GPU samples into per-card rows.

```sh
python scripts/integrations.py --data-dir data gpu --input gpu-input.json
```

The input has `queue`, `gpu_status`, optional Unix `now` and `profile`. Set `profile.host` to the collector host name; `profile.titles` optionally maps task IDs to display titles. The collector supplies timestamped hosts, GPU samples and process ownership. Queue metadata supplies current job and estimate information. The projection checks freshness and process/task agreement before showing job attribution. It is read-only and runs on demand; collectors and dispatchers are configured separately.

## Local asset choices

`board/plugins/asset_choices.py` catalogs installation-owned raster images, makes an explicit square crop and stores the selected image.

```sh
python -m board.plugins.asset_choices --catalog data/attachments/avatar-catalog
python -m board.plugins.asset_choices --catalog data/attachments/avatar-catalog --state data/attachments/avatar-choices --member owner --select example --crop 0 0 128
```

Provide `catalog.json` in the catalog directory as a list such as `[{"id":"example","file":"example.png"}]` and keep the image beside it. The selected crop must fit the image. The CLI accepts members `owner`, `Claude` and `GPT`; account mode also binds browser selection to the signed-in account. Local images are selected through `/api/avatar/catalog` and `/api/avatar/select`. These endpoints are available in the board, with an empty choice list until the installation supplies a catalog. The default bundled character artwork continues to work. Selection writes hashed PNG files and `selection.json` under the selected state directory.
