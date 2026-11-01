# Task-linked owner notes

Use `python scripts/agent.py --as GPT todo add --what "Choose a review slot" --task T001` for an owner action that unlocks a task. When that task starts, finishes or moves into the archive, the lead receives a reminder to review the note. Confirm the owner’s action before marking it done. Unlinked notes and accepted-task owner steps retain their existing behavior.
