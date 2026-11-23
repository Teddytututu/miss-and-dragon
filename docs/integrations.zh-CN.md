# 可选集成

[English](integrations.md) · [升级到 0.6](upgrade-0.6.zh-CN.md)

`board/plugins/` 提供本地适配器，导入模块本身只加载代码。标准 `python -m board start` 启动单人使用的回环地址看板。可选命令由调用者显式执行；目录观察、回复语音和账号模式另有下文的开关。安装专属设置与凭据保存在源码归档之外的本地文件中。

在项目根目录使用项目的 Python 解释器运行命令。`scripts/integrations.py --data-dir data` 选择项目资料目录，`--data-dir` 放在子命令之前。各命令输出 JSON 结果。

## 排队协议

`board/plugins/queue_protocol.py` 校验可移植作业票据，并根据传入的资源实测判断加载准入。

```sh
python scripts/integrations.py --data-dir data queue --input queue-input.json
```

输入含 `ticket`、`policy`、`sample`，可选 Unix 时间戳 `now`。票据必填 `id`、`task`、`job_group`、绝对 POSIX 路径 `cwd`、`cmd`、`next`，以及正数 `vram_gb`、`mem_gb`、`max_seconds`、非负整数 `priority` 和 `allowed_cards`。策略提供 `cards`，可选 `max_cards`、`disk_reserve_gb`、`loading_reserve_gb`、`max_age_seconds`；采样提供 `at`、`ram_free_gb`、`disk_free_gb`、`running_cards` 和含 `card`、`free_gb` 的 `gpus` 列表。

默认命令只校验和计算。显式提交时，在输入参数后追加 `--submit --host <ssh-host> --queue-root <absolute-posix-directory>`。准入通过后，使用现有 SSH 批处理认证将票据原子写入远端 `pending/`。远端队列需有 `pending/`、`running/`、`done/`；运行和调度由该安装自己的排队器负责。参见[可选显卡调度器](optional-gpu-dispatcher.zh-CN.md)。

## 语音后端

`board/plugins/voice_backend.py` 执行配置中的参数列表；后端以零退出码返回含 `"played": true` 的 JSON 时，记录播放完成。

```sh
python scripts/integrations.py --data-dir data voice --config voice-backend.json --actor GPT --text "结果已完成。"
python scripts/integrations.py --data-dir data reply --actor GPT --text-file reply.md
```

直接调用 `voice` 即为一次明确播放请求。配置必填列表 `backend_command`，例如 `["python", "local_speech_backend.py"]`；`backend_timeout` 默认 120 秒，最高 600 秒。后端从标准输入接收含 `who`、`text` 的 UTF-8 JSON。

`reply` 默认读取 `data/attachments/voice.json`，也可用 `--config` 指定文件。回复语音默认关闭；启用时写入 `enabled: true` 和后端设置。可选 `mute_until` 将 `GPT` 或 `Claude` 映射到带时区的静音截止时间。回复记录写入 `attachments/reply-results.jsonl`，正文留在传入的文本文件中。两个入口均使用 `attachments/voice.lock` 串行播放。

## 宿主钩子

`board/plugins/host_hooks.py` 为明确选择的工作区和宿主生成命令钩子模板。

```sh
python board/plugins/host_hooks.py --config host-hooks.json --template claude
python board/plugins/host_hooks.py --config host-hooks.json --template codex
```

配置必填已存在的 `workspace`。压缩恢复可配置项目相对路径 `pointer` 和允许的会话 ID 列表 `sessions`。可选 `reply_rules` 每项含 `id`、`pattern`；`protected_roots` 列出明确保护的读取范围。Claude 模板覆盖 `UserPromptSubmit`、`PreToolUse`、`Stop`；Codex 模板覆盖 `SessionStart`、`Stop`。省略 `--template` 时，脚本从标准输入接收宿主事件 JSON。生成模板后，由 Owner 审阅并合入宿主原生配置；新安装默认保持插件钩子关闭。

## 文件导入与目录观察

`board/plugins/file_import.py` 对显式配置的目录进行一次有界观察。

```sh
python scripts/integrations.py --data-dir data import --packet example path/to/answer.md
python scripts/integrations.py --data-dir data watch --config import-watch.json
```

`import` 将指定文件附到已有手动资料包，`--version` 选择回答版本。目录观察默认关闭。执行启用的一次观察时，配置 `enabled: true`、绝对路径 `directory`、已有资料包名 `packet`，可选 `version_id` 和至少为 1 的 `settle_seconds`。首次观察记录文件签名，后续调用在签名稳定达到间隔后导入。观察状态保存到 `attachments/import-observers/`。每次观察跳过符号链接、云占位文件和超过 50 MiB 的文件；重复调度由调用者显式安排。参见[手动资料包](manual-packets.zh-CN.md)。

## 邮件语气检查

`board/plugins/mail_lint.py` 对指定英文邮件草稿给出逐条规则反馈，HTML 草稿按可见正文读取。

```sh
python scripts/integrations.py --data-dir data mail draft.md
python board/plugins/mail_lint.py draft.html --json
```

检查按需执行。独立命令在发现问题时返回退出码 1；集成命令返回 `issues` 列表。草稿修改和邮件发送分别授权、分别执行。

## 进程控制

`board/plugins/process_control.py` 预览或终止一个明确登记的进程。

```sh
python board/plugins/process_control.py --record process-record.json --pid <pid>
```

记录需含实际进程的 `pid`、`create_time`、`executable`。默认调用只预览身份检查；明确授权停止时追加 `--apply`。终止前再次核对 PID、可执行文件与创建时间，并排除脚本自身。进程观察与终止采用分开的调用入口。

## 账号与访客

`board/plugins/accounts.py` 保存密码哈希和带版本的签名会话，`account_roles.py` 定义 Owner 与访客权限，`account_server.py` 提供可选回环地址账号服务。

```sh
python scripts/integrations.py --data-dir data accounts init
python scripts/integrations.py --data-dir data accounts password --person owner
python scripts/integrations.py --data-dir data accounts password --person visitor
python -m board start --data-dir data --accounts --port 8780
```

初始化在 `attachments/accounts.json` 创建一位 Owner 和一位访客；密码命令在本机交互输入。普通启动默认关闭账号模式，初始化后用 `--accounts` 显式选择。`accounts revoke --person visitor` 使访客现有会话失效。访客可查看访客看板和讨论室、留便利贴、选择自己的头像。账号服务继续使用直连回环地址，公网监听和代理部署属于独立配置。

## 服务观察

`board/plugins/services.py` 检查显式给定的本机服务目录，并提供 Windows 监听端口只读清单。

```sh
python scripts/integrations.py --data-dir data services --config local-services.json
```

目录文件为 JSON 列表，每项含 `url`，可加说明字段，例如 `[{"name":"Local board","url":"http://127.0.0.1:8780/"}]`。检查接受直连 `http://127.0.0.1` 地址并报告 HTTP 状态。调用命令时采集快照；标准看板启动保持服务观察关闭。监听清单适用于 Windows，受观察的服务照常运行。

## 额度准入

`board/plugins/budget.py` 根据明确策略和用量观测计算宿主额度准入。

```sh
python scripts/integrations.py --data-dir data budget --input budget-input.json
```

输入含 `state`、`sample`、`policy`，可选 `now`、`direct`。采样含 `account`、百分比 `used`、Unix 重置时间戳 `reset`。策略含 `daily_percent`、`reserve_percent`、`max_daily_turns`、`interval_seconds`，可选 `timezone_offset_hours`。`now` 接受带时区的 ISO 时间或 Unix 时间戳。输出含决策与更新后的状态，调用者负责保存状态和登记实际调度。这是按需执行的纯计算；看板内置巡检调度器继续使用自己的设置，参见[额度说明](quota.md)。

## 显卡观察

`board/plugins/gpu_observer.py` 将传入的队列与显卡采样投影成逐卡状态。

```sh
python scripts/integrations.py --data-dir data gpu --input gpu-input.json
```

输入含 `queue`、`gpu_status`，可选 Unix 时间戳 `now`、`profile`。`profile.host` 选择采集主机名，`profile.titles` 可将任务号映射为显示标题。采集器提供带时间戳的主机、显卡和进程归属观测，队列提供当前作业及预计时间。投影核对新鲜度和进程、任务的一致性后展示作业归属。该入口按需只读执行；采集器与排队器分别配置。

## 本地素材选择

`board/plugins/asset_choices.py` 读取安装方拥有的栅格图目录，按明确方形裁剪参数保存选择。

```sh
python -m board.plugins.asset_choices --catalog data/attachments/avatar-catalog
python -m board.plugins.asset_choices --catalog data/attachments/avatar-catalog --state data/attachments/avatar-choices --member owner --select example --crop 0 0 128
```

在素材目录提供 `catalog.json`，内容如 `[{"id":"example","file":"example.png"}]`，图片放在同一目录；裁剪范围应位于图片内。CLI 的成员可选 `owner`、`Claude`、`GPT`；账号模式下的浏览器选择绑定到登录账号。看板通过 `/api/avatar/catalog` 和 `/api/avatar/select` 使用本地素材，安装方提供目录前选择列表为空，默认随包角色图照常可用。选择结果以哈希命名 PNG 和 `selection.json` 写入所选状态目录。
