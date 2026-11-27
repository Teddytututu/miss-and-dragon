# Manual research packets

A packet keeps one question, its input files, every returned answer and the lead's choice together. The person operating ChatGPT sends the files and downloads the result. The local tools keep the history and show which version led to the next task.

## Try the fictional example

From the project directory:

```sh
python scripts/demo_manual_packet.py --output work/manual-packet-example
python scripts/manual_packet.py --packet-dir work/manual-packet-example show
```

The example compares two cache measurements. Version 1 mixes units and batches and is returned for correction. Version 2 uses the same paired inputs. Claude adopts its timing table, keeps the memory question for a later measurement and hands that work to T002. Both answer texts and both tables stay in the packet.

Use a new or empty output directory. The example needs no account or model call. To see the same packet inside the board and read its report, use the [complete research example](research-workflow.md). A standalone packet under `work/` stays separate from your project's `data/`.

The JSON has two entries in `answer_versions`. The first review says `rejected`; the second says `partial`, points to `T002`, and has the same `id` as `adopted_answer`. Its `files` list identifies `result-v2.csv`, with rows A = 2/1 seconds and B = 3/2 seconds. The two totals are 5 and 3 seconds. These fictional timings demonstrate the review workflow.

## Use your own materials

```sh
python scripts/manual_packet.py --packet-dir data/attachments/manual-packets/my-question create --title "Cache pilot" --question demo/manual-packet/question.md --source demo/manual-packet/inputs.csv --task T001
```

Send `ask.md` and `materials.zip` from that packet in your chosen ChatGPT chat. Read the answer, download its attachments, save the answer text to a local file, then paste it into the same packet:

```sh
python scripts/manual_packet.py --packet-dir data/attachments/manual-packets/my-question paste --answer demo/manual-packet/answer-v1.md --file demo/manual-packet/result-v1.csv
python scripts/manual_packet.py --packet-dir data/attachments/manual-packets/my-question show
```

Use the returned version `id` when the lead records a review:

```sh
python scripts/manual_packet.py --packet-dir data/attachments/manual-packets/my-question review --version VERSION_ID --decision rejected --note "Use seconds and the same two batches" --task T001
```

For a revised answer, repeat `paste` with the new text and files. The review choices are `accepted`, `partial` and `rejected`. `partial` records the adopted part in `--note`; `--task` points to the work taking it forward. Name each adopted attachment with `--adopt-file`, so a report can check that its table was selected. A later accepted or partial answer becomes the adopted version. Each earlier answer keeps its own review.

```sh
python scripts/manual_packet.py --packet-dir data/attachments/manual-packets/my-question paste --answer demo/manual-packet/answer-v2.md --file demo/manual-packet/result-v2.csv
python scripts/manual_packet.py --packet-dir data/attachments/manual-packets/my-question review --version VERSION_ID --decision partial --note "Adopt the timing table; measure memory separately" --adopt-file result-v2.csv --task T002
```

Replace `VERSION_ID` with the second answer's `id` printed by `paste` or `show`. Repeat `--adopt-file` for multiple selected attachments. An accepted review with no file selection adopts the whole answer; a partial review without a file selection stays readable but must be reviewed with explicit file scope before generating a timing report.

### Collect attachments before review

The optional `import` and `watch` entries can collect files for an unfinished answer. An accepted or partial review binds that version's file list and contents. Later imports of new or changed files are rejected before writing; an identical retry of an already registered file succeeds without changing packet metadata, including a file saved with a collision suffix.

For a late attachment, paste the complete answer with all its intended files as a new version, then review that version. If using directory observation, update the configuration's `version_id` to that new answer before invoking `watch` again. See [file import and observation](integrations.md#file-import-and-directory-observation).

## Change an adoption after reviewing the evidence

Run `show`, copy the earlier answer's `id`, and use the same `review` command with `--decision accepted` or `--decision partial`. Record why the older version is now useful in `--note`; use `--adopt-file result-v2.csv` when restoring the example's timing-only review. Rejecting the currently adopted answer clears the adoption until another version is selected. Both answer texts and their returned files stay in the packet; previous metadata bytes stay in its `history/` directory.

A report remains a saved result until you explicitly refresh it. The complete example's report command checks whether its cited answer is still the adopted answer and whether its table has changed. See [report checking and refresh](research-workflow.md).

## Recover from an input error

| Message or exit code | Next action |
| --- | --- |
| `Choose a new packet directory` or `Choose an empty packet directory` | Inspect that packet with `show`, or choose a different directory for a new question. Existing files are kept. |
| `Choose an ordinary result filename` | Rename the returned file; `meta.json`, `ask.md`, `materials.zip` and hidden names are reserved for the packet. Retry the paste. |
| `Cannot read packet metadata at ...` | Repair the named `meta.json` or restore the intended copy from `history/`, keeping the answer files. |
| `Saved reviewed files changed` | Paste the changed answer and files as a new version, then review that version. Import all returned attachments before review. |
| `Reviewed answer attachments are fixed` | Paste the complete answer and all intended files as a new version, review it, then set `watch.version_id` to the new version if using directory observation. The rejected import keeps existing packet and report files. |
| `Original packet inputs changed` | Restore the original question and input ZIP, or create a new packet for the changed inputs. A newly pasted answer may be reviewed after checking those inputs. |
| A missing question, answer or source filename | Check the printed path. Use a quoted absolute path when running outside the project directory. |
| Exit code `2` with JSON on stderr | Read its `error` and `packet_dir` fields. Successful commands return `0` and print the packet JSON on stdout. |

Question and answer text use UTF-8; a UTF-8 BOM is accepted. Put quotes around paths containing spaces. A failed reserved-filename paste adds no answer version.

## Existing packets

Older answer files are projected into the version list when viewed. Their original filenames and bytes stay in place. Files whose earlier version association requires a human choice appear with an empty per-version attachment list; the original cumulative attachment list remains available.

Viewing an older accepted or partial answer needs no migration. To build or check a current report from a version without `review.artifacts` or `review.inputs`, the lead must first inspect its present original inputs, answer and returned files, then explicitly review that same version once and refresh the report. Use `--adopt-file` for a partial review's timing CSV. The answer ID stays the same; there is no need to re-review every historical version. This review records the bytes checked now, not evidence of what an earlier review saw.

If the old metadata does not register `ask.md` and `materials.zip` in its `attachments` list, first confirm those original files and add their filenames to that list before the review. The [report guide](research-workflow.md) explains checking and refreshing an adopted result.

Repeated pastes of the same answer and attachments return the existing version. A changed file with the same filename receives a content suffix. The input ZIP remains the material sent with the original question.

New accepted and partial reviews record the original input bytes as well as the returned files. A later rejection retains that evidence binding. Editing an already reviewed file or its original input therefore requires a new answer review, rather than relabeling the old version. Older records without these bindings remain readable.
