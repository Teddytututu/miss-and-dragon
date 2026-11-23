# Upgrade from 0.4.3

Keep your existing installation and data directory as a rollback copy. Extract the new source ZIP into a separate directory, create its environment and install `requirements.txt`. Start it with `python -m board start --data-dir <your-data-copy> --port 18780` first.

Task cards, discussion ledgers, reports and local custom artwork continue using their existing files. Existing report URLs use the same reader catalog. Result reading markers retain the `result-tree-read-v1` browser key: unique title markers are recognized, then new reads use the node ID or report path. Renaming a report title preserves its read state. Changed summaries and main report references become unread. Shared old titles await one explicit read for each report.

Board GET requests now project yesterday's completed items without changing the stored schedule. Explicit scheduling and to-do commands continue performing their existing rollover updates.

The resource forecast and manual packets are optional. Add `attachments/resource-plan.json` to use measured whole-job forecasts. Use `scripts/agent.py resource-plan` for the same calculation as the page. Store new manual packets under `attachments/manual-packets/NAME`; the sidebar shows all saved answer versions and the adopted review. Existing tools and the original page sections remain available.

The archive includes original MIT SVG character art. Runtime custom artwork remains in your data directory and keeps priority. Local fan art PNGs and screenshots remain with their original installation; copy only artwork whose use you have authorized.

## Since the previous formal release

The public main branch after 0.4.3 already added browser-readable reports, explicit reply-or-reaction choices, task/experiment helpers, voice preferences and an opt-in night watcher. This candidate adds measured whole-job resource plans, manual answer versions, stable result reading identity, a read-only board snapshot and the complete local research example. Installations keep their own optional-service choices.

After reviewing the copied data and browser behavior, choose a local cutover time. Keep the old code and data together for rollback. The candidate review material identifies the exact ZIP and selected source files.

Historical image reactions without a matching local entry display as 🙂. See [local reaction setup](local-emotes.md). Existing reaction records and local image files remain in the project data.
