# 交给 agent 安装 Miss & Dragon

[English](install-with-agent.md) · [README](../README.zh-CN.md)

把 README 的安装请求交给具有本机文件和终端能力的 Codex 或 Claude。agent 按下面的流程完成操作，交回可以打开的本机看板。每个会话用哪个模型由 Owner 选择，更换模型经过 Owner 同意。

## 0. 默认约定

README 里给用户的只是一句短提示，下面这些都按默认照做：

- 在新的文件夹里安装，用户已有的项目和文件保持原样。
- 用户已经说过的项目信息直接复用，其余一次问完：研究什么、想得到什么；希望怎么称呼（传给 Bootstrap 的 `--user-name`，默认大肥鱼）；GPT 和 Claude 各有几个订阅、什么档位。
- 订阅档位决定巡检的额度档：两边各自按“有多个订阅或最高档 → `plenty`，普通付费档 → `normal`，免费或常常用完 → `tight`”选，写进 `data/attachments/onboarding.json` 的 `plans`，各自的 `scripts/patrol.py` 用对应的 `--tier`。
- 用随包角色图和 Unicode 表情。B 站表情包下载、登录自启动各问一次，用户同意才装。
- 守夜人装在当前用户账号下。
- 用户说“演示项目”时，走第 2 节末尾的独立演示，不建正式项目。
- 结束时交回两样：能打开的本机网址；项目文件夹的完整路径（用户会把它填进 README 里给 Claude 的那句话）。

## 1. 准备项目

使用支持 `venv` 的 Python 3.11 或更新版本，以及 Git。先检查现有环境，采用实际可用的 Python 命令；Windows 上也可能是 `py -3`。缺少的基础组件通过当前已授权的软件包管理器安装，沿用本机账号和系统设置。

新安装选择一个新的文件夹，克隆仓库：

```sh
git clone https://github.com/Teddytututu/miss-and-dragon.git miss-and-dragon
cd miss-and-dragon
```

已有仓库从原项目记录接续。源代码 ZIP 也可以安装：解压到新文件夹，并以该文件夹作为项目根目录。下文 Git 升级适用于克隆；ZIP 安装通过新源代码目录和保留的项目记录升级。

GPT / Codex 读 `AGENTS.md`，Claude 读 `CLAUDE.md`，接着读 `personas/` 对应角色和 `protocol/lifecycle.zh-CN.md`。两个助手共用同一个工作目录。已有项目先恢复 `data/project.json` 与讨论记录，再接着做事。

## 2. 配置并启动

复用已经给出的项目名、研究问题和希望交付的成果。项目名已经确定时，只把缺少的两个实质问题一起问完：研究什么、想得到什么。下面的示例值替换为实际答案。

```sh
python scripts/bootstrap.py "我的项目" --question "研究问题" --deliverable "希望得到的成果" --agent GPT --port 8780 --unicode-emotes
```

安装会话是 Claude 时使用 `--agent Claude`。Bootstrap 创建 `.venv`，通过随包依赖脚本安装 Pillow，初始化 `data/`，并在 `127.0.0.1` 启动后台服务。默认显示名是大肥鱼，初始主题是蓝色。身份菜单可改显示名，侧栏可改主题与语言。助手在首次对话里通过 `/api/project` 写入研究问题和成果；之后可在节奏设置底部修改。中文地址为 `http://127.0.0.1:8780/?lang=zh-CN`，英文使用 `?lang=en`。

Bootstrap 也会尝试在当前 Windows 用户下注册本项目每十分钟一次的守夜人。macOS 与 Linux 会收到准备命令和 cron 命令。读取实际返回结果：手动注册状态附有可执行命令，看板本身可以继续启动。[启动与巡检](night-watch.md)说明完整接入与生命周期。

可选公开表情包询问一次，明确同意后才传 `--download-emotes`；等待选择时使用 Unicode 继续安装。随包角色图直接可用，换图从用户明确提出更换开始。登录自启动和可选的卫士（看板或服务挂了自动拉起）分别由用户选择，选定后通过 `scripts/install-startup.ps1` 安装。

先试用时，在本机环境安装依赖，再启动独立演示：

```sh
python -m pip install -r requirements.txt
python -m board start --demo --data-dir work/demo-data --port 8781
```

创建本机环境后，以上命令使用该环境的解释器。演示命令在前台持续运行，独立数据目录保留正式项目记录；这条试用路径只创建演示服务和项目文件。

## 3. 打开确认，再接入两个 agent

Bootstrap 后，Windows 后续命令使用 `.venv/Scripts/python.exe`，macOS / Linux 使用 `.venv/bin/python`。PowerShell 中，带引号的解释器路径前加 `&`。

1. 在可用浏览器打开返回的网址，读取实际项目名和正文。读取 `/api/project`，将 `workspace_id` 与 `data/project.json` 比较；读取 `/api/me` 的 `listener: "127.0.0.1"`。
2. 用上述解释器执行 `python scripts/agent.py --as GPT status` 和 `python scripts/onboarding.py status GPT`；Claude 会话把两处角色都换成 Claude。读取接入结果，按角色入口完成可以独立执行的步骤。
3. 每个助手在自己的实际会话发开场并回复对方。在第二个助手中打开同一文件夹，让它读自己的角色入口并继续已有项目。接入结果的 `waiting_on` 指向需要完成的互相回应。
4. 按[模型提供方连接](provider-bridge.md)和[巡检安排](agent-schedules.md)使用宿主实际提供的原生调度工具。本机守夜人观察文件，模型工作由助手会话完成。实际接入结果沿既有 onboarding 流程登记。

交回可用网址、项目名、完成的配置，以及第二个会话下一步做什么。详细运行日志留在项目内。

## 4. 再次打开与重启

在同一个文件夹重跑原 Bootstrap 命令，端口中的服务与当前 `workspace_id` 一致时会直接复用。端口属于其他项目时，通过 `--port` 选择空闲端口，保留原项目服务。

服务停止后重跑 Bootstrap 即可启动。升级需要重启时，读取 `data/service.json`，把其中 PID、命令和项目身份与实际进程逐一对应，再通过宿主的正常进程控制停止本项目进程。接着运行 Bootstrap，重复第三节的实际页面检查。启动输出保存在 `data/server.log`。

## 5. 保留项目记录并升级

先在仓库外保存一份可恢复的 `data/`、本机图片和部署配置。读取当前分支、`git status --short` 与上游改动。源码有本机修改时，先在独立分支或工作树保存，再整合升级。

跟踪 `main` 且工作树干净的克隆执行：

```sh
git fetch origin
git diff HEAD..origin/main --stat
git merge --ff-only origin/main
```

本地分支分叉时，在其独立分支审阅并合入上游。已有 tag 和发布附件保持历史。ZIP 安装把选定版本解压到另一个源目录，将保留的项目记录复制到其 `data/`，再通过 Bootstrap 创建本机环境。项目目录变化后，相关守夜人和自启动项按各自安装说明对应到新目录。

重跑 Bootstrap；`requirements.txt` 变化时更新依赖；源码更新后重启本项目服务，再完成第三节。项目本机依赖更新使用同一解释器执行 `scripts/install_deps.py`。贡献代码前按角色入口运行 `python scripts/check_eol.py` 与 `python -B scripts/verify.py`。

按用户给出的订阅数和档位分别登记。多订阅或最高档建议取巡检下限，普通档采用基准，免费档采用上限；自动模式沿现有额度算法计算。

```sh
python scripts/onboarding.py plans GPT --subscriptions 1 --tier normal
python scripts/onboarding.py plans Claude --subscriptions 1 --tier normal
```

`--tier` 使用 `free`、`normal` 或 `highest`。固定覆盖单独保存；修改守夜人频率后，预览并重新应用本项目安装器。事件桥适配器从 `/api/cadence` 或 `board.cadence.minutes` 读取 `event_cooldown`，合并同会话叫醒。

## 本机时间提示

希望 Claude 每次接到消息时附上本机日期、时间、星期和 UTC 偏移，可把 `templates/claude-settings.example.json` 的 `hooks.UserPromptSubmit` 项合并到本项目的 `.claude/settings.json`，保留已有钩子和设置。从项目根目录启动 Claude，命令使用可用的 Python 解释器。先运行 `python scripts/prompt_time.py --language zh-CN` 看输出，并把示例中的 `en` 换成 `zh-CN`。脚本只输出时间文本，由用户选择是否安装。Codex 醒来先看本机钟，再读收件箱与日程；历史消息中的相对日期沿原消息日期理解。
