# Questions, decisions and results stay together

[简体中文](ARCHITECTURE.zh-CN.md) · [Project overview](../README.md)

Tell Miss what you want to investigate and what you want to receive. She turns that into a research plan and reviews the results. Dragon builds the agreed work, runs experiments and brings back the files. Big Fish chooses the direction, budget and models used by the chats.

The board keeps the conversation beside the tasks, findings and reports. Each step has a file behind it, so the next chat can continue from the same project records.

## Who does what

![Big Fish chooses direction, Miss plans and reviews, Dragon implements, programs keep records](architecture/01-overview.svg)

Big Fish makes the consequential choices. Miss designs the work and accepts the delivery. Dragon handles implementation within the agreed scope. Small programs save records, check task transitions and observe progress.

## Where conversations go

![Shared discussion, separate private chats, exchange notes and decisions retain different conversations](architecture/02-channels.svg)

Use the discussion room for shared questions and results. Each assistant also has a separate private conversation with Big Fish. The exchange keeps research questions, answers and implementation choices together across chats.

## How a question becomes a result

![A question becomes a task, Dragon delivers it and Miss reviews the result](architecture/03-question.svg)

Miss turns the question into a task with a concrete delivery. Dragon works through it and returns the result files. Miss reviews the delivery; requested changes return to Dragon, while accepted findings go into the result tree.

## What wakes the assistants

![Programs observe progress, the scheduler advises a wake, and the host chat performs the work](architecture/04-cadence.svg)

The night watch is a small background program that observes configured tasks and writes events when something changes. The quota scheduler recommends when each assistant should return. An assistant applies that recommendation through the scheduling tools available in its chat host. Optional event bridges deliver changes to the appropriate chat.

## Who decides

![Big Fish authorizes consequential actions, Miss decides research questions, Dragon chooses implementation details](architecture/05-authority.svg)

Miss handles research design and review. Dragon sends routine questions to Miss and continues other authorized work. Actions involving the user's account, spending or external commitments follow Big Fish's current authorization policy. Big Fish selects each chat's model and approves model changes.

## What happens on a wake

![An assistant reads events and tasks, continues available work, then records its next patrol](architecture/06-wake-loop.svg)

The assistant reads messages, events and open tasks, then completes the work available within its role. Experiment chats handle jobs, front desk chats handle messages, and chores chats handle interface and documents when that split is configured. A final patrol records the outcome, next task and concrete dependency.

<details>
<summary>For developers: the files behind the board</summary>

| Part | Implementation |
| --- | --- |
| Project board and file storage | `board/app.py`, `board/storage.py`, `board/project.py` |
| Tasks and allowed state changes | `board/lifecycle.py`, `scripts/task_flow.py` |
| Questions, answers and decisions | `board/exchange.py`, `board/agent_tools.py` |
| Discussion and private conversations | `scripts/post_message.py`, `board/private_notes.py` |
| Progress events and quota advice | `scripts/night_watch.py`, `board/scheduler.py` |
| Provider-native controls | `board/provider_bridge.py` |

The web service binds to loopback. Local project records and deployment credentials stay in the installation's runtime directory. File updates use process-safe locks. GPU dispatch and remote event delivery use separately configured adapters.

[Agent commands](agent-commands.md) · [Wake contract](../protocol/heartbeat.md) · [GPU dispatcher](optional-gpu-dispatcher.md) · [Event bridge](optional-event-bridge.md)

The HTML diagram companion is `docs/architecture/index.html`; open it through a local static server. GitHub displays HTML as source. The SVG figures above render directly in this page.

</details>
