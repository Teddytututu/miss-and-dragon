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
| Front desk | Owner messages, factual answers, dispatch and scoped local repairs | Events and a sixty-minute fallback |
| Experiment | Research jobs, scoring, GPU hosts and result collection | Events and a sixty-minute fallback |
| Chores | Web pages, documentation, learning materials, open source and shared tools | Events and a two-hour fallback |

After handling an event, continue through lead orders, open work and returned items; Experiment also checks eligible resources. Close with a patrol only when actual dependencies remain. Shared-code changes retain write ownership and a recoverable before state. [Architecture](../docs/ARCHITECTURE.md) shows the complete loop.

In deployments with multiple executor chats, route a reply event back to the role that asked the original question. The provider adapter shares that correlation between event dispatch and wake summaries, using the question reference and its time. The owning role acknowledges execution results; dispatch handoffs keep their own receipts, preserving the original work item for its owner.

多个执行会话共用身份时，答复事件沿原问题编号与时间回到提问角色，事件派发与唤醒摘要共用同一套关联。实施结果由实际负责角色确认，交接另记回执，原任务继续由所属会话推进。
