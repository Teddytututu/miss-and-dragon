# Roles and authorization

Use the [task lifecycle](lifecycle.md) for registration, execution, review and archival. During accepted work, routine task questions go to the existing research-lead exchange with two options and a recommendation. The executor continues independent work while the lead decides. Thirty-minute recommendation handling applies to reversible authorized work within resource limits. Specific user-operated actions and consequential approvals follow the user's current policy.

| Participant | Responsibility | Decision boundary |
| --- | --- | --- |
| User, default display name 大肥鱼 | Project goal, personal choices, resources and final tradeoffs | Direct user instructions take precedence |
| Claude | Research direction, design, evidence, report review and task acceptance | Register tasks and start conditions on the board; put review decisions in the task |
| GPT | Experiments, implementation, organization, engineering recovery and delivery | Execute within authorization; dispatch workers and integrate results |
| Optional work-information assistant | Daily work candidates | Use existing authorization and submit candidates for research-lead review |

Preserve the user's wording and time when relaying a request, distinguishing it from other speakers and assistant advice. Later direct instructions supersede earlier arrangements. Expanded reading, external accounts and permission changes require their applicable user authorization. A login establishes identity; reading, sending, submitting and paying each follow the task's scope. Claude owns scientific changes and brings user tradeoffs to the user. GPT delivers through the board; Claude records acceptance. Workers hold one task and declared paths. Shared writes use locks, recovery state lives under data/attachments/state.json, and human conversation carries useful results and decisions.

## Executor chat split

Reference deployments use three existing chats with independent inbox cursors and write scopes. The public CLI identities remain Lead (`Claude`) and Executor (`GPT`); a provider adapter maps executor role chats to those identities.

| Chat | Scope | Wake cadence |
| --- | --- | --- |
| Front desk | Owner messages, factual answers, dispatch and scoped local repairs | Events and a ten-minute fallback |
| Experiment | Research jobs, scoring, GPU hosts and result collection | Events and a sixty-minute fallback |
| Chores | Web pages, documentation, learning materials, open source and shared tools | Events and a two-hour fallback |

After handling an event, continue through lead orders, open work and returned items; Experiment also checks eligible resources. Close with a patrol only when actual dependencies remain. Shared-code changes retain write ownership and a recoverable before state. [Architecture](../docs/ARCHITECTURE.md) shows the complete loop.
