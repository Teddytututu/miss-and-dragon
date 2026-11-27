# Pro 手动研究包

一个包放同一个问题、原始资料、各版回件和 Claude 最后采用的内容。发送和下载由操作者在自己选择的 ChatGPT 聊天中完成，本地程序保存历史并串起后续任务。

## 跑一次虚构示例

在项目目录运行：

```sh
python scripts/demo_manual_packet.py --output work/manual-packet-example
python scripts/manual_packet.py --packet-dir work/manual-packet-example show
```

示例比较两批相同输入的缓存耗时。第一版混用了计量单位和批次，Claude 退回重做；第二版对齐了输入与秒数，Claude 采用配对时间表，把内存测量交给 T002。两版正文和两张表都保存在原包里。

输出目录应为新目录或空目录。示例不需要账户，也不调用模型。要在看板里查看同一流程和报告，请运行[完整研究示例](research-workflow.zh-CN.md)。单独演示保存在 `work/`，与真实项目的 `data/` 分开。

JSON 的 `answer_versions` 有两项：第一版审核为 `rejected`，第二版为 `partial`、连接 `T002`，且第二版的 `id` 与 `adopted_answer` 相同。其 `files` 指向 `result-v2.csv`：A 批为 2/1 秒，B 批为 3/2 秒，两列合计为 5 秒和 3 秒。这些虚构计时用于演示审核流程。

## 放入自己的问题

```sh
python scripts/manual_packet.py --packet-dir data/attachments/manual-packets/my-question create --title "Cache pilot" --question demo/manual-packet/question.md --source demo/manual-packet/inputs.csv --task T001
```

把包内的 `ask.md` 和 `materials.zip` 手动发送到选定的 ChatGPT 聊天。阅读回答、下载附件后，把正文存为本地文件，再贴回同一包：

```sh
python scripts/manual_packet.py --packet-dir data/attachments/manual-packets/my-question paste --answer demo/manual-packet/answer-v1.md --file demo/manual-packet/result-v1.csv
python scripts/manual_packet.py --packet-dir data/attachments/manual-packets/my-question show
```

Claude 核对后，用 `show` 显示的版本 `id` 记录结论：

```sh
python scripts/manual_packet.py --packet-dir data/attachments/manual-packets/my-question review --version VERSION_ID --decision rejected --note "用相同两批输入，耗时统一为秒" --task T001
```

第二版回件继续使用 `paste`。审核选择为 `accepted` 采用、`partial` 部分采用、`rejected` 退回；部分采用的具体范围写进 `--note`，承接任务写进 `--task`。每个被采用附件用 `--adopt-file` 明确列出，报告据此检查计时表是否被选中。后续采用或部分采用的版本成为采用版本，每版答案仍保留自己的审核意见。

```sh
python scripts/manual_packet.py --packet-dir data/attachments/manual-packets/my-question paste --answer demo/manual-packet/answer-v2.md --file demo/manual-packet/result-v2.csv
python scripts/manual_packet.py --packet-dir data/attachments/manual-packets/my-question review --version VERSION_ID --decision partial --note "采用计时表；内存另测" --adopt-file result-v2.csv --task T002
```

将 `VERSION_ID` 换成 `paste` 或 `show` 输出的第二版 `id`。选择多个附件时重复 `--adopt-file`。`accepted` 未指定附件范围时采用整份答案；`partial` 未指定附件范围时仍可查看，生成计时报告前需明确文件范围后重新审核。

### 审核前收齐附件

可选的 `import` 与 `watch` 入口用于为尚未完成审核的答案收集文件。新的采用或部分采用审核会绑定该版的文件清单及内容。之后再导入新增或变化的文件，会在写入前拒绝；对已登记文件的同字节重试仍可成功，包元数据保持不变，碰撞后带内容后缀的文件也可重试。

需要补交附件时，把完整答案与所有拟保留文件作为新版本 `paste`，再审核该版。使用目录观察时，随后把配置里的 `version_id` 换成新版本，再调用 `watch`。参见[文件导入与目录观察](integrations.zh-CN.md)。

## 复核后改回早先版本

先运行 `show`，复制早先答案的 `id`，再用同一条 `review` 命令设置 `--decision accepted` 或 `--decision partial`，在 `--note` 写明重新采用的理由。恢复示例中“只采用计时表”的审核时，补上 `--adopt-file result-v2.csv`。退回当前采用的答案会清除采用关系，直到选定另一版。两版正文与回件继续保留；改动前的元数据保存在包内的 `history/`。

报告保存上次明确生成的结果。完整示例的报告命令会检查引用的答案是否仍被采用、表格是否变化；刷新需显式执行。操作见[报告检查与刷新](research-workflow.zh-CN.md)。

## 输入出错后怎么继续

| 提示或退出码 | 下一步 |
| --- | --- |
| `Choose a new packet directory` 或 `Choose an empty packet directory` | 用 `show` 查看现有包，或换目录创建新问题；原有文件会保留。 |
| `Choose an ordinary result filename` | 给回件改名后重试；`meta.json`、`ask.md`、`materials.zip` 与隐藏文件名保留给研究包使用。 |
| `Cannot read packet metadata at ...` | 修复提示中具名的 `meta.json`，或从 `history/` 恢复选定副本，保留答案文件。 |
| `Saved reviewed files changed` | 将改动后的正文与回件作为新版本贴回，再审核新版本；所有回件应在审核前导入。 |
| `Reviewed answer attachments are fixed` | 将完整答案和全部拟保留附件作为新版本贴回并审核；使用目录观察时，再把 `watch.version_id` 换成新版本。被拒绝的导入保留现有包和报告文件。 |
| `Original packet inputs changed` | 恢复原提问和资料 ZIP，或为变化后的输入创建新包。确认新输入后，也可贴回新答案再审核。 |
| 问题、答案或输入文件不存在 | 检查输出中的路径；从其他目录执行时使用加引号的绝对路径。 |
| 退出码 `2`，标准错误中输出 JSON | 阅读 `error` 和 `packet_dir` 字段。成功时退出码为 `0`，标准输出给完整 JSON。 |

问题和答案文本使用 UTF-8，允许 UTF-8 BOM；含空格路径加引号。因保留文件名而失败的贴回不会新增答案版本。

## 沿用旧包

查看旧包时，程序把历史回答文件列为各版回件，原文件名和内容保留。历史附件归属由 Claude 结合正文核对，旧的附件总清单继续保留。

查看旧的 `accepted` 或 `partial` 答案不需要迁移。需要生成报告或核验为 current 时，若所选版本没有 `review.artifacts` 或 `review.inputs`，负责人须先检查现有原始输入、答案和回件，再对同一版本显式审核一次，随后刷新报告。部分采用时以 `--adopt-file` 指定计时 CSV。原答案 ID 不变，也不需要批量重审所有历史版本；这次审核记录的是现在核对过的内容，不能补回旧审核当时未保存的证据。

若旧元数据的 `attachments` 尚未登记 `ask.md` 和 `materials.zip`，先确认这些原件，再把文件名补入清单，然后审核。报告检查和刷新步骤见[报告指南](research-workflow.zh-CN.md)。

同一正文和附件重复贴回时沿用已存版本。同名附件内容变化时，程序用内容后缀保存新文件。提问所带的资料 ZIP 始终保存原始输入。

新的采用/部分采用审核会同时记录原输入和回件的内容，之后退回也保留该证据关联。已审文件或原输入被修改后，需要审核新答案，不能把变化后的内容重新标成旧版本。没有这些关联字段的旧记录仍可查看。
