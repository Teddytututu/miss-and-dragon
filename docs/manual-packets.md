# Manual research packets

A packet keeps one question, its input files, every returned answer and the lead's choice together. The person operating ChatGPT sends the files and downloads the result. The local tools keep the history and show which version led to the next task.

## Try the fictional example

From the project directory:

```sh
python scripts/demo_manual_packet.py --output data/attachments/manual-packets/example
python scripts/manual_packet.py --packet-dir data/attachments/manual-packets/example show
```

The example compares two cache measurements. Version 1 mixes units and batches and is returned for correction. Version 2 uses the same paired inputs. Claude adopts its timing table, keeps the memory question for a later measurement and hands that work to T002. Both answer texts and both tables stay in the packet.

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

For a revised answer, repeat `paste` with the new text and files. The review choices are `accepted`, `partial` and `rejected`. `partial` records the adopted part in `--note`; `--task` points to the work taking it forward. A later accepted or partial answer becomes the adopted version. Each earlier review remains attached to its answer.

## Existing packets

Older answer files are projected into the version list when viewed. Their original filenames and bytes stay in place. Files whose earlier version association requires a human choice appear with an empty per-version attachment list; the original cumulative attachment list remains available. Review the historical answer, then record the chosen version with the existing review command.

Repeated pastes of the same answer and attachments return the existing version. A changed file with the same filename receives a content suffix. The input ZIP remains the material sent with the original question.
