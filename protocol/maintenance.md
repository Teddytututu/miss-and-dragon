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
