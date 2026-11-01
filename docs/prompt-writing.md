# Writing prompts people can read

1. Keep lasting rules in prompts. Put progress, incidents and dated observations in tasks or the exchange.
2. Give steps in order, one action per line.
3. Give every rule one home. Link to it elsewhere.
4. Use ordinary words and concrete actions.
5. Keep the reason short enough to explain why the rule exists.
6. Enforce reliable checks in code; link to the check from the prompt.
7. Review weekly: remove expired rules, duplicates and checks that create noise.
8. The lead maintains shared prompts. Executors propose edits through a note; the owner chooses models and approves model changes.

The lifecycle check reads project-local `instructions.md` or `当前指令.md` and exported host prompts in `attachments/wake-prompts.json`, an object mapping role names to prompt text. It reports standing instructions above 4500 characters, wake prompts above 1200, dense internal terms and standing instructions that name archived tasks. The check reports to the lead; it leaves host settings with the existing owner-controlled setup.

Use [plain exchange notes](plain-notes.md) for result-first coordination. Owners may configure a response self-check for their lead assistant.
