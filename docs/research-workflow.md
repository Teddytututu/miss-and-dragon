# From a question to a usable result

Start with a choice that the result can change. In the bundled fictional study, the choice is whether caching is worth testing further. Compare the same inputs, measure time in the same unit, and keep memory as a separate question.

## Run the complete example

Use Python 3.11 or newer from the extracted project directory:

```sh
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python scripts/demo_research.py --data-dir work/my-study
.venv/Scripts/python -m board start --data-dir work/my-study --port 18780
```

On macOS or Linux, use `.venv/bin/python` for the commands above. Open `http://127.0.0.1:18780`.

1. Open **Results** and read **Paired cache pilot**. Its first paragraph gives the finding, the comparison uses the same batches, and the CSV opens from the report.
2. Mark the result read, refresh the page and reopen it. The marker follows the report through a title change. A new summary becomes unread.
3. Expand **Timeline** under **In progress**. The second measured batch follows the first; the new model says **Trial needed**. Drag horizontally, zoom with Ctrl + wheel, or use the zoom and full-screen buttons. The original board themes and draggable decorations continue working.
4. Open **Manual research packets** in the sidebar. Read both answers. The first was returned for mixed units; the second timing table was partly accepted. Its review points to T002 for a separate memory measurement.
5. The request to send a packet appears in **Needs you**. Resource scheduling reads measured jobs; human actions stay in their own list.

These commands generate files locally. They use zero model calls and register zero background tasks. Closing the foreground server ends the example.

## Keep one measured plan

`attachments/resource-plan.json` contains ordered single-card jobs and explicit measurements. A measurement has `unit`, `seconds` and `units`. Whole-batch measurements use `unit: "batch"`; a nine-hour batch stays a nine-hour job. A job can declare `depends_on`, a running `card` and `elapsed_seconds`. Use the same configuration from the UI or the unified command:

```sh
python scripts/agent.py --as GPT --data-dir work/my-study resource-plan
python scripts/agent.py --as GPT --data-dir work/my-study resource-plan --cards 1 --now 2026-01-01T10:00:00+08:00
python scripts/agent.py --as Claude --data-dir work/my-study packet cache-pilot show
```

With one card, the two-hour trial finishes at 12:00 and the three-hour comparison at 15:00. The third job awaits its own measurement. Current inventory and historical completions are distinct facts. A forecast describes measured available work and retains the observation time separately from the calculation time.

## Review a result where the mistake happened

Keep the question, original inputs, answer text and returned files in one packet. The lead chooses accepted, partial or rejected, names the useful part, and links the next task. A revised answer receives its own version. Original text and files remain available. See [manual packets](manual-packets.md).

Write the result around the decision: conclusion first, matched comparisons together, one concrete example explaining the difference. A failed attempt earns space when it changed the next action. The example's mixed-unit first answer shows exactly that change.

## Choose who does the work

The owner chooses direction and resources; the project lead frames the question and reviews the result; an executor implements the agreed work. These can be people, local tools or optional model sessions. Start with the local example, then connect the tools your project uses through the existing installation guide.
