# Install Miss & Dragon with an agent

[简体中文](install-with-agent.zh-CN.md) · [README](../README.md)

Give the README's installation request to a Codex or Claude session with local file and terminal access. The agent performs the steps below and returns a working local board. The Owner chooses each session's model; changing it requires the Owner's agreement.

## 0. Defaults

The README gives the user a one-line prompt. Apply these defaults:

- Install into a new folder and leave the user's existing projects and files as they are.
- Reuse project details the user has already given and ask the rest in one go: what to research and what to deliver; what the user wants to be called (Bootstrap `--user-name`, default 大肥鱼 / Big Fish); how many GPT and Claude subscriptions they have and which plans.
- Plans set each assistant's quota band: several subscriptions or the top plan → `plenty`, a regular paid plan → `normal`, free or often exhausted → `tight`. Record them under `plans` in `data/attachments/onboarding.json` and pass the matching `--tier` to that assistant's `scripts/patrol.py`.
- Use the bundled character pictures and Unicode reactions. Ask once each about the optional emote download and login startup, and install them only with consent.
- Ask whether to install the optional night watch under the current user account; leave it disabled by default.
- When the user asks for a demo project, use the isolated demo at the end of section 2 and create no real project.
- Finish by returning the working local address and the full project folder path (the user puts it into the README line for Claude).

## 1. Prepare the project

Use Python 3.11 or newer with `venv` support and Git. Inspect the current environment and use its available Python command; on Windows this may be `py -3`. Install missing prerequisites through the host's authorized package manager. Keep the existing machine and account settings.

For a new installation, choose a new folder and clone the repository:

```sh
git clone https://github.com/Teddytututu/miss-and-dragon.git miss-and-dragon
cd miss-and-dragon
```

An existing checkout resumes from its current project records. A source ZIP also works: extract it into a new folder and use that folder as the project root. Git-based upgrades below apply to a clone; ZIP installations use a fresh source folder and a preserved copy of their project records.

Read `AGENTS.md` for GPT / Codex or `CLAUDE.md` for Claude, the matching persona in `personas/`, and `protocol/lifecycle.md`. The folder is the shared workspace for both assistants. For an initialized project, recover `data/project.json` and its existing discussion before making changes.

## 2. Configure and start

Reuse the project name, research question and desired deliverable already supplied. If the project name is given, collect just the two missing substantive answers together: the research question and the desired deliverable. Replace the example values below with those answers.

```sh
python scripts/bootstrap.py "My project" --question "Research question" --deliverable "Desired deliverable" --agent GPT --port 8780 --unicode-emotes
```

Use `--agent Claude` when the installing session is Claude. Bootstrap creates `.venv`, installs Pillow through the bundled dependency helper, initializes `data/`, and starts a detached service bound to `127.0.0.1`. The default display name is 大肥鱼 and the initial theme is blue. The identity menu changes the display name; the sidebar changes theme and language. The assistant writes the research question and deliverable during the first conversation through `/api/project`. Later edits live at the bottom of Cadence settings. English is available at `http://127.0.0.1:8780/?lang=en`; Chinese uses `?lang=zh-CN`.

Bootstrap asks whether to install this project's optional ten-minute night watch under the current Windows user. The default keeps it disabled; pass `--install-night-watch` to consent. On macOS and Linux it returns preparation and cron commands. Read its actual result: a manual-registration outcome includes a runnable command, and the board can continue independently. The scheduled task runs PowerShell with plain-text arguments and `-WindowStyle Hidden`; the task itself remains visible in Task Scheduler and can be disabled there at any time. [Night watch](night-watch.md) describes installation and its lifecycle.

Ask once about the optional public emote pack. Use `--download-emotes` only with explicit consent; Unicode keeps setup moving while the answer is pending. Packaged character images work immediately; custom pictures begin with an explicit replacement request. Login startup and its optional watchdog are separate choices, installed only when selected through `scripts/install-startup.ps1`.

For an isolated preview instead of a real project, install the dependency in a local environment and run:

```sh
python -m pip install -r requirements.txt
python -m board start --demo --data-dir work/demo-data --port 8781
```

Use the project-local interpreter for these commands after creating an environment. The demo command runs in the foreground. Its separate data directory preserves the real project's records, and this preview path creates only the demo service and its project files.

## 3. Verify the live board and connect both agents

After bootstrap, use `.venv/Scripts/python.exe` on Windows or `.venv/bin/python` on macOS / Linux for subsequent commands. In PowerShell, prefix a quoted executable path with `&`.

1. Open the returned local URL in the available browser and read the actual project name and content. Inspect `/api/project` and compare its `workspace_id` with `data/project.json`; inspect `/api/me` for `listener: "127.0.0.1"`.
2. Run `python scripts/agent.py --as GPT status` and `python scripts/onboarding.py status GPT` with that interpreter, substituting Claude for both role arguments when appropriate. Read the onboarding result and complete the independent pending steps in the role entry file.
3. Each assistant posts its own opening and reciprocal reply from its actual session. Open the second assistant in the same folder and ask it to read its role entry and continue the existing project. An onboarding `waiting_on` value identifies the reciprocal message to complete.
4. Follow [provider integration](provider-bridge.md) and [agent schedules](agent-schedules.md) for the host's available native scheduling tools. The local night watch observes files; assistant sessions perform model work. Record actual setup results under the existing onboarding contract.

Return the working URL, project name, completed setup and the concrete next action for the second session. Keep detailed logs in the project rather than the Owner-facing result.

## 4. Reopen or restart

Rerun the same bootstrap command from the same folder. It reuses an existing service when the port belongs to the same `workspace_id`. If the selected port belongs to another project, choose a free port with `--port` and keep that project's service running.

For a stopped service, bootstrap starts it again. For an upgrade requiring a restart, inspect `data/service.json`, confirm the recorded PID, command and project identity against the actual process, and stop only that project's process through the host's normal process controls. Then run bootstrap and repeat the live-board checks. `data/server.log` contains startup output.

## 5. Upgrade while preserving the project

First save a recoverable copy of `data/`, local artwork and deployment configuration outside the checkout. Read the current branch, `git status --short` and the incoming changes. Preserve local source edits in a separate branch or worktree before integrating an upgrade.

For a clean clone tracking `main`:

```sh
git fetch origin
git diff HEAD..origin/main --stat
git merge --ff-only origin/main
```

Review divergent local history in its own branch and integrate it deliberately. Existing tags and release assets retain their published history. For ZIP installations, extract the selected new source separately and copy the preserved project records into its `data/` directory. Recreate its local environment through bootstrap. Project-path-specific scheduling and startup entries should follow the newly selected folder through their documented installers.

Rerun bootstrap, refresh dependencies if `requirements.txt` changed, restart this project's service after the source update, and repeat section 3. Use the same interpreter's `scripts/install_deps.py` for the project-local dependency refresh. Before contributing code, run `python scripts/check_eol.py` and `python -B scripts/verify.py` as specified in the role entry.

Record the subscription count and tier supplied for each assistant. Multiple subscriptions or the highest tier suggest the lower patrol bound; a normal plan uses the baseline and a free plan the upper bound. Automatic quota scheduling keeps its existing calculation.

```sh
python scripts/onboarding.py plans GPT --subscriptions 1 --tier normal
python scripts/onboarding.py plans Claude --subscriptions 1 --tier normal
```

Use `free`, `normal` or `highest` for `--tier`. Cadence settings stores fixed overrides separately; after changing night-watch frequency, preview and reapply its installer for this project. Event-bridge adapters read `event_cooldown` from `/api/cadence` (or `board.cadence.minutes`) before scheduling a session wake.

## Local clock context

To include the current local date, time, weekday and UTC offset on each Claude prompt, merge the `hooks.UserPromptSubmit` entry from `templates/claude-settings.example.json` into this project's `.claude/settings.json`, preserving existing hooks and settings. Run Claude from the project root and use its available Python interpreter in the command. Preview with `python scripts/prompt_time.py --language en`; use `--language zh-CN` for Chinese. The script prints clock context only. Installation remains an explicit project choice. Codex wake prompts read the host clock before the inbox and schedules; relative words in older messages keep their original dates.
