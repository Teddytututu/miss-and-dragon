# Changelog

## 0.6.0

- Rebuilt the board around one shared storage lock, a task registry and versioned delivery stages; a stage only opens once its upstream stages are accepted.
- Manual question packets keep every answer version, attachment and review.
- Result-tree read state is stored on the server, keyed by stable node identity, so it survives title changes and stays read-only in snapshots.
- Queue submission is atomic and rejects a ticket whose id already exists in any queue folder.
- New optional integrations, all off by default: queue protocol, voice backend, host hooks, explicit file import, mail tone check, process control, accounts and guests, local service observer, daily budget, GPU observer and avatar choices. See docs/integrations.md.
- The report checker reads private names from project settings instead of shipping them; report categories use generic names.
- The three characters (owner, Claude, GPT) now ship as original PNG avatars and 16 mood pictures, ready after install; the simple SVGs stay as a fallback.
- Queue submission sends its program as one base64 line, so it works under tcsh as well as bash, and rejects a ticket whose command is identical to one already pending or running.
- Upgrade guide: docs/upgrade-0.6.md.

## 0.5.0 candidate

- Forecast whole measured jobs with dependencies; the board and CLI read one resource-plan file.
- Keep each manual answer and attachment version with its lead review and successor task.
- Preserve read states across report title changes and volatile metadata updates; board snapshots stay read-only across midnight.
- Run the complete paired-cache example locally with zero model calls.
- Package original SVG artwork and bilingual setup, workflow and upgrade guides.


## 0.4.3

- Add a full-screen cadence panel with 13 ordered activities, subscription-aware suggestions and persistent overrides; move project details into the panel and display names into the identity menu.
- Add deduplicated weekly report tidying and rule-review events, supporting file links below each finding, and English/Chinese tidying guides.
- Reject promise-only or courtesy-only assistant posts in English and Chinese, and remove two portraits from the mistakes diagram.

## 0.4.2

- Bring Big Fish, Miss and Dragon together in the cover, with matching chibi profile portraits.
- Add four notebook workflow diagrams and a Chinese version of the mistakes-to-programs diagram.
- Use high-resolution English and Chinese interface images with direct full-size links.
- Explain the six everyday benefits in both README languages.
- Open help in the selected interface language and shorten Windows temporary paths for nested installations.
- Align role schedules across guides and diagrams, and document the optional diagram-building tools and font licenses.

## 0.4.1

- Add English and Simplified Chinese interface selection, persistent browser preference and bilingual help.
- Preserve original project content and drafts while switching language.
- Use Miss & Dragon across themes and remove the sidebar synchronization timestamp.

## 0.4.0

- Numbered questions with five decision categories, peer answers, factual questions, execution decisions and lead vetoes.
- A quick wake inbox with absolute local image paths, exact event acknowledgments and recorded outcomes.
- Mood-required patrols and safe automatic reactions; assistant progress reports stay lightweight.
- Schedule, research progress, result-tree, finding and short task-title commands.
- Expiring cards and reminders, archived past dated schedules, and day-old research-state alerts.
- Efficiency summaries covering question waits, blocked tasks, returned work, stale state and observed GPU idle time owned by the acting assistant.
- Miss & Dragon notebook branding, bundled Xiaolai handwriting, dotted white paper, alternating notes, status dots and a full-screen reaction selector.
- Optional dispatcher, event bridge and shared-resource guard deployment guides.
- Atomic concurrent question answers and cross-midnight greeting reminders.

## 0.3.0

- Unified assistant command entry, private conversations, task lifecycle, quota observations and reviewed local source packaging.
