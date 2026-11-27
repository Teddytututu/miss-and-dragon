# Try a complete research handoff

[简体中文](portfolio-demo.zh-CN.md)

Use a fictional caching experiment to follow a question, a returned answer, a revision, partial acceptance and the next task. The example runs with local files and zero model calls.

## Start

From the repository directory, with Python 3.11 or newer:

```powershell
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python scripts/portfolio_demo.py
```

On macOS or Linux, replace `.venv/Scripts/python` with `.venv/bin/python`.

Open http://127.0.0.1:18780. Use `--port 18782` to select another port. The launcher keeps demo data under `work/portfolio-demo`; rerunning it reuses that data. Installation downloads Python dependencies. The demo itself uses local files and registers zero background tasks.

## Follow the decision

1. Read the research progress: the paired timing table has been adopted and the next task measures memory.
2. Open **External brain** in the navigation. Find the cache pilot packet and its two saved answers. The first mixed units and batches; its review requests a paired measurement. The second is partially adopted, with memory left as the next task.
3. Open **Paired cache pilot** in the result tree. The fictional paired measurements total 5 seconds for the baseline and 3 seconds for the cached run. Open the attached CSV to inspect both rows.
4. Mark the result as read. Open the board in a second tab and refresh it: the marker follows the shared project state. Mark it unread in the second tab and refresh the first.
5. Open the task list and find the memory measurement. The pending manual packet remains a human action, while the task retains its owner.

The timing numbers describe this synthetic example. They illustrate the path from a question to an adopted result.

## Start over and keep the previous demo

Stop the server with Ctrl+C, then run:

```powershell
.venv/Scripts/python scripts/portfolio_demo.py --reset
```

The launcher moves the marked demo to a sibling `portfolio-demo.archive-...` directory before creating a fresh copy. Your edits remain in the archive. The reset path accepts only marked demos inside this repository's `work` directory. To initialize without serving, add `--init-only`.

## Read the implementation

- [Shared reading state](case-shared-reading.md): stable result identities, serialized writes and stale-response handling.
- [Task claims](case-task-claims.md): process locks, finite leases and overlapping write scopes.
- [Architecture](ARCHITECTURE.md): the wider collaboration flow.

## Adopt this candidate

Keep the current code and data together. Try this candidate with the synthetic workspace, then with a separate copy of your project data. Select the code and data pair to serve after review. Keep the previous pair available for rollback.
