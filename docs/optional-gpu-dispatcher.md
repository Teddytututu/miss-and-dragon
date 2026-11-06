# Queue approved experiments on a shared GPU server

[简体中文](optional-gpu-dispatcher.zh-CN.md) · [Project overview](../README.md)

Tell Claude which server you can use and the resource limits agreed with its users. She decides which experiments may run. GPT can then build and connect a dispatcher for that deployment: a small program that starts approved jobs when resources become available.

This is an optional deployment recipe. The board supplies task records, a local queue runner and progress events; the remote dispatcher follows the server's actual access and resource rules.

## What you get

An approved experiment waits in a queue. When an eligible GPU and enough disk space are available, the dispatcher starts it. Its status file shows running, waiting, completed and failed jobs. The night watch can read that status through a configured adapter and turn changes into events for the assistants.

## Agree on the limits first

Claude and GPT need the approved server access, resource allowance, reservations, disk requirement and stopping conditions. you approves spending and any account action under the current authorization policy. Store server names, users, device preferences and limits in the deployment's own configuration.

The dispatcher starts jobs within that agreement. Running processes and other users' files keep their existing ownership. Results, scores, settings and logs return to the project; large reproducible intermediate files follow the project's retention plan.

<details>
<summary>For developers: dispatch cycle</summary>

1. Observe live GPU memory, processes and ownership using `nvidia-smi`. Apply the configured reservations, eligibility rule and concurrency allowance. Use one shared capacity policy for the dispatcher and its observers, evaluated at each admission. Count each device once across active computation, model loading and valid job reservations. When the allowance drops below current occupancy, preserve approved running jobs and resume admissions as capacity becomes available.
2. Read approved job specifications from `queue/`, highest priority first and oldest first within a priority. Specifications include `task`, `priority`, `cmd`, `cwd`, `mem_gb`, `disk_gb`, `est_hours` and the approval record.
3. Treat device numbers as preferences. Recompute eligibility at launch and choose another eligible device when appropriate. Check capacity before loading.
4. Start the approved command with the selected `CUDA_VISIBLE_DEVICES`. Save process identity, device and start time in `running/`.
5. Move finished specifications into `done/` or `failed/`, preserving the exit status. Permit at most three retries with an attempt count and bounded backoff. Return deterministic configuration and authorization errors for review. Handle planned time limits through the deployment's checkpoint and requeue policy.
6. Write `status.json` for the configured observer. Include actual progress and utilization observations so the assistants can distinguish occupied resources from useful work.

Use the [resource guard](optional-resource-guard.md) during loading and the [event bridge](optional-event-bridge.md) for delivery to chats. Keep credentials and machine-specific commands outside the public repository.

</details>
