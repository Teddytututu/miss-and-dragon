# Questions and execution choices

Use agent.py ask for a lead decision and agent.py note for an implementation update. The question heading opens the request; wording such as “please confirm” in an ordinary note remains part of that note.

Numbered answers close the question with the same identifier. The caption may change while the identifier stays fixed. Existing questions without identifiers continue to close by matching their original title.

After applying an authorized reversible choice, record it with agent.py decide and include the exact question identifier in the body or reason. A GPT decision made after the question stops repeated execution reminders; the question stays open for Claude's review. A Claude veto restores the execution reminder. Explicit external, deletion and conclusion questions stay with the lead for approval.
