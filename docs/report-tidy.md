# Keep each finding with its supporting files

[简体中文](report-tidy.zh-CN.md)

Big Fish opens one card to read a finding and the small links beneath it to inspect the data. Miss reviews what belongs together; Dragon updates the board after that review.

## Weekly tidy

The night watch creates a `weekly_tidy` event on Sunday at 20:00 in the computer's local time. Miss reads this page and prepares a concrete list of cards to combine, rename or move to older materials. Dragon applies the reviewed list through the board's file commands. Miss checks the resulting board and acknowledges the event. The default `weekly_rules` event follows that acknowledgement.

1. Keep one main card for each finding. Attach its CSV, Markdown, PDF or ZIP files with `under` set to the main card's exact `path`.
2. Rename a superseded report to `Older version (date, incorporated into X)` and archive it with its supporting files.
3. Use titles that explain the result. Keep task numbers in the task records.
4. Keep two entry cards in the overview: **Current conclusions** and **Start here**. Put the detailed findings under their appropriate subject.

An attachment whose parent is archived or missing appears as a normal card, so its file stays reachable. Search includes the names of supporting files. Review files against the project's retention rules before any filesystem cleanup.

<details>
<summary>For the assistants</summary>

Use `python scripts/agent.py --as GPT file --help` to inspect the current file commands. Keep the existing root, `path`, category and archive fields. Use `file add --under <parent-path>` for a new supporting file, or `file edit --title <current-title> --under <parent-path> --new-title <reader-title>` for an existing card. A supporting link in the overview has this shape:

```json
{"title":"Per-example results","path":"reports/results.csv","under":"reports/finding.html","cat":"研究"}
```

Changes go through the existing locked update tools. Record the reviewed list and the completed changes in the exchange. Acknowledge the exact event ID after review. The next patrol keeps the pending event until acknowledgement and issues each calendar period once.

Cadence settings changes the weekday and time, priority order and fixed patrol overrides. Automatic model scheduling continues to use quota observations. Subscription plans affect the displayed suggestion; a fixed override changes the actual interval. Mentions and near deadlines retain the 20-minute priority, and low-quota pauses retain their existing rule. Reapply the night-watch installer after changing its frequency; event-bridge adapters read `event_cooldown` when coalescing wakes.

</details>
