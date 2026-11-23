# Pro 手动研究包

一个包放同一个问题、原始资料、各版回件和 Claude 最后采用的内容。发送和下载由操作者在自己选择的 ChatGPT 聊天中完成，本地程序保存历史并串起后续任务。

## 跑一次虚构示例

在项目目录运行：

```sh
python scripts/demo_manual_packet.py --output data/attachments/manual-packets/example
python scripts/manual_packet.py --packet-dir data/attachments/manual-packets/example show
```

示例比较两批相同输入的缓存耗时。第一版混用了计量单位和批次，Claude 退回重做；第二版对齐了输入与秒数，Claude 采用配对时间表，把内存测量交给 T002。两版正文和两张表都保存在原包里。

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

第二版回件继续使用 `paste`。审核选择为 `accepted` 采用、`partial` 部分采用、`rejected` 退回；部分采用的具体范围写进 `--note`，承接任务写进 `--task`。后续采用或部分采用的版本成为采用版本，每版仍保留自己的审核意见。

## 沿用旧包

查看旧包时，程序把历史回答文件列为各版回件，原文件名和内容保留。历史附件归属由 Claude 结合正文核对，旧的附件总清单继续保留；确认版本后沿用同一条审核命令登记。

同一正文和附件重复贴回时沿用已存版本。同名附件内容变化时，程序用内容后缀保存新文件。提问所带的资料 ZIP 始终保存原始输入。
