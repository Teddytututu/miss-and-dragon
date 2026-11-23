# 从 0.5 或 0.4.3 升级到 0.6

[English](upgrade-0.6.md) · [可选集成](integrations.zh-CN.md)

将现有源码与完整资料目录一起保留为回退副本。把选定的 0.6 源码包解压到独立目录，创建项目环境，使用同一解释器安装 `requirements.txt`。将现有项目记录复制到新安装的 `data/`，再用独立回环端口启动资料副本：

```sh
python scripts/install_deps.py
python -m board start --data-dir data --port 18780
```

环境创建与依赖安装参见[由助理安装](install-with-agent.zh-CN.md)。资料初始化后，可在启动命令追加 `--read-only` 进行只读演练。检查副本期间，原实例继续使用原资料目录。核对任务看板、讨论室、报告、时间表、身份与粉蓝两套主题后，选择切换时刻。

## 保留现有项目记录

保留 `project.json`、`board.md`、`overview.json`、任务卡、讨论室账本和完整 `attachments/`。这些文件包含手动资料包回答版本、自定义角色图、阅读状态、服务偏好与本地记录。任务和报告继续使用资料副本中的原相对位置。直接从 0.4.3 升级时，先阅读 [0.5 升级说明](upgrade-0.5.zh-CN.md)中的报告稳定标识和手动资料包变化。

0.6 在使用对应功能时创建记录；已有项目可用原记录打开，新功能状态由命令生成。

| 项目资料内的相对路径 | 创建或更新入口 |
|---|---|
| `attachments/current-assignments.json` | `integrations.py current --task …`，保存各助理最近明确派活 |
| `attachments/work-records.json` | 连续工作回执 |
| `attachments/consumers/` | 事件和收信消费者确认 |
| `attachments/delivery.json` | 带版本的阶段配置、交付与审阅 |
| `attachments/host-events.json` | 明确的宿主事件入队、认领与结算 |
| `attachments/publications.json`、`attachments/published/` | 已通过报告与本地依赖闭包的注册 |
| `attachments/import-observers/` | 已启用的目录观察轮次 |
| `attachments/reply-results.jsonl` | 回复收尾回执 |
| `attachments/accounts.json` | 显式可选账号初始化 |
| `attachments/avatar-catalog/`、`attachments/avatar-choices/` | 安装方提供的栅格图目录和已选裁剪图 |

`attachments/voice.json` 继续保存本机语音偏好。可选账号、语音、钩子、队列和服务设置属于具体安装，保存在公开源码包之外。导入另一回答版本时，保留已有手动资料包元数据。

报告检查器从 `data/project.json` 的 `user_name` 和可选字符串数组 `report_internal_names` 读取私有称呼。检查读者版报告时，将本安装自己的内部称呼配置在这里。源码检查器保留通用规则，私有称呼检查按项目配置执行。运行 `python templates/report-kit/check_report.py report.html --root data` 可明确选择项目资料目录。

## 新增显式命令

用 `python scripts/integrations.py --help` 查看命令列表，用 `<command> --help` 查看参数。`--data-dir` 放在子命令前。

```sh
python scripts/integrations.py --data-dir data current --actor GPT --task T001 --stage implementation --artifact board.md --authorization "Explicit project assignment"
python scripts/integrations.py --data-dir data stage configure --task T001 --stage implementation --actor GPT --reviewer Claude
python scripts/integrations.py --data-dir data stage submit --task T001 --stage implementation --actor GPT --files report.md
```

交付结果返回产物 `version`。指定审阅者将该值传给 `stage review --task T001 --stage implementation --actor Claude --version <version> --decision accept`。上游阶段创建后，下游可在 `stage configure` 使用 `--depends <upstream-stage>` 声明依赖。交付内容改变时下游阶段失效；审阅绑定当前实际文件内容。

`publish --task T001 --stage implementation --file report.md --title "Result"` 把当前已通过的报告注册到本地看板。此处的发布指本地报告注册，外部 Git 托管和部署分别执行。

其他新子命令包括 `import`、`watch`、`schedule`、`decision`、`event`、`reply`、`queue`、`gpu`、`budget`、`services`、`voice`、`mail`、`accounts`。事件发送先明确认领，再按实际传输结果结算；集成 CLI 管理账本，实际传输由宿主提供。插件输入和启用方式见[可选集成](integrations.zh-CN.md)。

## 可选插件默认关闭

普通启动沿用单人模式。账号模式需要初始化后追加 `--accounts`；回复语音需要配置 `enabled: true`；目录观察需要 `enabled: true`，每轮显式调用一次 `watch`。宿主钩子由 Owner 审阅生成模板后合入宿主配置。队列提交需要 `--submit` 和明确 SSH 目的地参数。进程控制 CLI 默认预览身份，单独授权停止后用 `--apply` 执行。

服务、显卡、额度和邮件检查按需调用。本地素材目录提供前选择列表为空，随包角色图保持可用。升级沿用已有可选服务选择，新增观察器和宿主设置由安装方单独决定。

## 检查资料副本并切换

打开 `http://127.0.0.1:18780/`，核对原任务、讨论室、报告链接和时间表。检查中英语言与粉蓝主题；按本机选定范围测试可选集成。在资料副本上选一个小任务走完正常交付和审阅流程，检查实际命令结果与本地输出文件。

贡献源码时执行 `python scripts/check_eol.py`、`python -m pytest tests -q -p no:cacheprovider`，以及[验证说明](validation.md)中的 JavaScript 检查。源码测试和示例产物使用独立目录。

切换时通过原启动方式停止本项目旧服务，用选定源码和核对后的资料副本启动新服务，再通过各安装器更新项目专属启动路径。登录自启、宿主钩子和守夜人安装沿用 Owner 的明确选择。原源码及其配套资料副本一起保留，便于回退。
