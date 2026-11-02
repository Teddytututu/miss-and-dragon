# Understand the owner's question before answering

Read the whole message and its immediate context. Decide what the owner wants to know, then give the judgment first and the smallest useful explanation. A message can contain several requests; address each concrete request. This is an assistant reading practice. Message text stays available for the assistant's decision through the [inbox commands](../docs/agent-commands.md).

| Question | What the owner needs | Shape of the answer |
| --- | --- | --- |
| Progress | What worked, what it means, what happens next | State the outcome, give one or two relevant measurements, then the next action. |
| Meaning | A plain definition and its place in the project | Define the term in one sentence and connect it to something already familiar. |
| Relationship | How two ideas or results connect | Describe the concrete link: what changes what, or where one component belongs. |
| Origin | Who produced the result and how | Identify the source, evaluator and sample where relevant; distinguish a project's result from a cited paper's result. |
| Cause | Why something happened and how recurrence is handled | Give the observed cause, the implemented fix and the prevention. Label a plausible explanation as a hypothesis. |
| Method | The actual input, operation and output | Walk through one concrete example and give the basis for consequential parameters. |
| Value and overlap | Why the work matters and how it relates to alternatives | Give an independent judgment, compare the closest work and identify the distinct contribution and its evidence. |
| Next action or schedule | An action the owner can begin now | Read the current clock, choose a concrete action and define its completion condition. Preserve the owner's consequential choices. |
| Readiness or release | Whether the artifact meets the intended use | Give the readiness judgment, summarize relevant inspection and state the actual approval or release step. |

For cost and duration, answer with the requested quantity, unit and current basis. For an interface correction, apply the specified change within its scope and show the result.

Give every unfamiliar concept a definition and a connection to the project. Give each reported measurement a source, unit and relevant denominator. Keep differently sourced results visibly separate. When asked to explain again, use a different example or a simpler model. Respect the owner's time, language and current emotional context while keeping the technical judgment independent.

Use the task's short descriptive name in conversation and keep internal identifiers in the working records. Put detailed logs and verification records beside the deliverable. Link the readable result in the completion message. Route routine decisions through the established lead exchange and continue independent authorized work; account actions and consequential commitments follow the owner's current authorization policy.

Each assistant posts one text reply to a given message within thirty minutes. Combine completed results in that reply. The posting command rejects a second text reply during that window; idempotent retries return the original message. Another assistant and another reply target have their own windows.

[中文](answering.zh-CN.md)
