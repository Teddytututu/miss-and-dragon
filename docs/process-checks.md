# Consecutive process checks

A process issue closes after ten successful observations in a row. A failed observation resets the count to zero. An unavailable observation preserves the count and records why it was unavailable.

```sh
python scripts/agent.py --as GPT checks run
python scripts/agent.py --as GPT checks show
```

The existing `wake` command runs due checks too. The default interval is three hours, measured from the last actual observation; repeated wakes during that interval reuse the saved count. Observations happen on the next existing wake after they become due. The saved `next_at` tells the assistant when to check again. Existing provider schedules and operating-system settings retain their configured behavior.

The included example asks whether each active execution role has running, returned or ready-now work on the task board. Paused roles follow the existing project settings; when all roles are paused, the observation is unavailable. A result describes recorded workflow state. The lead reviews its meaning and the underlying work.

Two further checks audit the collaboration records. `patrols_on_time` checks both assistants against their recorded next patrol times, with a forty-five-minute grace period; missing or invalid records produce an unavailable observation. `owner_answered` checks live research and study messages aged two to twenty-four hours. A text reply from either assistant, or an explicit active `react --enough` decision tied to the current message, resolves the reminder. Ordinary reactions, example messages and attachment-only replies leave the text reminder active. Saved library items keep their collection behavior.

`board/checks.py` defines a registry of read-only observation functions. Each returns `ok` as `true`, `false` or `null`, plus a short `detail`. Add a registry entry with a title, positive target, interval in minutes and its runner. Choose checks that measure explicit records, keeping scientific judgments with the lead.

Time-sensitive runners use `clocked=True` in their registry entry and accept `now` as a keyword argument. The run supplies its actual observation clock, including explicit clocks used for reproducible checks. The observers read workflow records; their saved counters use the existing project lock.

The module saves the current count, last observation, next due time and up to sixty observations in `data/attachments/checks.json`, under the existing project lock. Storage retains previous bytes. Reaching the target sets `solved`; solved checks retain their history and stop sampling. Changing a registered target or interval starts a fresh count with the old history retained. `checks show` reads the record directly.
