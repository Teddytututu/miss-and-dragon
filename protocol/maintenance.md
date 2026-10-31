# Board and exchange maintenance

All tools are in this repository and use the worker workspace lock. Runtime records live under data/.

```sh
python scripts/task_number.py --title "A concrete task"
python scripts/maintenance.py board
python scripts/maintenance.py exchange
```

Number reservation scans task files, the active board, archived tasks and existing reservations, then exclusively reserves the next T number. The dispatcher registers scope before a worker claims it.

Board compaction transfers accepted, cancelled and archived rows to data/tasks/archive.md while keeping running and review tasks active. Original row bytes and the complete preceding board are preserved. Repeating the operation keeps the existing archive.

Exchange maintenance groups dated third-level headings, respecting code fences. The complete source is retained under data/exchange/history-<hash>.md; daily files use YYYY-MM-DD.md and exchange.md is a hard link to the current day. board.workers.append_shared preserves that link while retaining earlier bytes in history. Keep source and daily files on one filesystem supporting hard links.

Read [roles](roles.md) and the [worker protocol](workers.md) for authorization and shared writes. Further task-page ETA presentation can be integrated after that interface version is ready; the current package keeps estimates and their basis in state.

## Workflow improvements

Record Owner-requested workflow improvements in the deployment's local improvement ledger: the concrete problem, desired behavior, implemented change, public applicability and resulting commit. Carry reusable rules, tools and documentation into the public project when they fit its role and authorization contracts. Keep personal records, account details and deployment-specific paths in the local ledger; publish the general behavior and a reviewable implementation. Preserve local history, existing artwork choices and published releases while applying the change.

用户提出 workflow 改进时，先在本机登记具体问题、期望行为、实际落地、公开适用性和对应提交。适合通用使用的规则、工具与说明随实现同步到开源项目；个人资料、账号和专属路径保留本机。公开改动遵循角色与授权约定，并保留现有历史、图像选择和已发布版本。

## Generated files and local snapshots

Keep deployment outputs, temporary work and large runtime payloads outside version snapshots through scoped ignore rules. For an approved existing checkout, remove generated paths from the Git index while preserving their working files, and record the change in a normal commit scoped to that cleanup. Preserve the Owner's other staged changes and published history. Source artwork, documentation images and release inputs remain tracked according to the explicit source manifest. Observe object growth after the change and identify the paths behind any continuing large writes.

部署产生的输出、临时工作和大型运行数据采用明确的忽略规则。已有仓库按获批范围取消生成文件的索引跟踪，保留工作文件，并用仅包含本次清理的正常提交记录；其他暂存改动与已发布历史保持。源码图片、文档插图和发布输入按明确清单继续跟踪。修改后观察对象增长，继续出现的大文件按实际来源路径定位。

## Application goals and actual work

After an original blocker is approved and work resumes, the owning chat reads the host goal with its native tool and records a timestamped structured observation alongside the exact blocker and current execution evidence. Associate observations with the goal instance and status revision, including creation and update metadata when exposed by the host. Fresh blocked status with a resolved original blocker and running work produces one deduplicated consistency event for that instance and revision. A genuine pending approval remains a dependency. A fresh empty goal plus an explicit Owner clear is a valid terminal state; missing or stale observations remain unknown. Close the event after fresh reconciliation and preserve host goal controls, resource policy and notification cadence. For adapters with native goal observations, require a fresh actual tool observation before a successful patrol receipt; missing or expired observations return a concrete refresh step while existing jobs continue. Distinguish an observed empty goal from an explicit Owner clear.

原阻塞获批并恢复工作时，由所属会话实际读取宿主目标，并把带时间的结构化快照与该目标、该阻塞、当前执行事实关联。实例及状态版本采用宿主提供的创建和更新时间等字段，旧批复与旧事件回执各自关联原版本。已解决原阻塞且实际运行、目标仍为 blocked 时，只产生一条去重一致性事件；真实待批继续作为依赖，用户明确清除且工具返回空目标时保留清除状态。过期或缺失的观察归为未知，fresh 协调结果使事件收口；目标控制、资源规则和通知节奏沿当前授权。

## Directed assignment receipts

Route an explicitly addressed lead assignment to the owning executor chat, accepting configured display names and stable role aliases. That chat acknowledges receipt with a safe reaction during claim or handoff. Reading, reactions, substantive replies and task execution keep separate records. Other role chats retain their own assignments and cursors.

明确派给某个执行角色的指令，由实际接单会话在认领或交接时贴安全表情；显示名与稳定角色别名指向同一角色。阅读、表情、实质文字回复与任务执行分别记账，各角色保持原任务归属及收信游标。
