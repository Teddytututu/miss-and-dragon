# Miss & Dragon

![Miss & Dragon 研究手账](docs/images/readme-hero.png)

本机看板与命令行，让一个人带着两个 AI 做研究：Lead 设计和验收，Executor 执行，提问、决定和状态写成文件，由普通程序检查。

[![MIT](docs/badges/license.svg)](LICENSE) ![Python 3.11+](docs/badges/python.svg)

<table><tr>
<td align="center" width="140"><img src="docs/images/avatar-lead.png" width="72" alt="Lead"><br><b>Lead</b><br><sub>设计 · 拍板 · 验收</sub></td>
<td align="center" width="140"><img src="docs/images/avatar-executor.png" width="72" alt="Executor"><br><b>Executor</b><br><sub>执行 · 搭建 · 汇报</sub></td>
<td width="420"><sub>你是 <b>Owner</b>：方向、预算、对外和删除归你；其余事情由两个 AI 之间提问、决定并记账。</sub></td>
</tr></table>

[English](README.md) · [Architecture](docs/ARCHITECTURE.md) · [Interactive diagrams](docs/architecture/index.html)

## 启动

在仓库根目录运行这三条命令。界面文字目前以中文为主。

在解压后的源码目录使用 Python 3.11 或更新版本。三条命令依次安装依赖、创建虚构演示数据并启动看板：

```sh
python -m pip install -r requirements.txt
python -m board start "Example study" --demo --init-only --question "Which method helps?" --deliverable "A reproducible comparison"
python -m board start "Example study"
```

打开 **http://127.0.0.1:8780**，让最后一条命令持续运行。使用 `--data-dir` 指定另一个项目，使用 `--port` 指定本机端口。[Bootstrap](scripts/bootstrap.py)、[启动与巡检](docs/night-watch.md)和[模型提供方连接](docs/provider-bridge.md)说明环境准备和可选自动化。

## 和直接开两个聊天窗口有什么不同

- 提问、决定、状态和结果保存在项目文件中，两类 AI 都能重新读取。
- 设计、预算、结论、对外和删除进入带编号的五类提问。
- 日常执行选择用 `decide` 记账，Lead 可以通过 `veto` 否决。
- 醒来合同要求巡检前继续查看消息、指令和可独立推进的任务。
- 普通程序检查记录格式、命令字段和任务状态流转。

<img src="docs/images/wake-loop.svg" alt="一轮醒来：事件、空卡、Lead 指令、开着的任务，只剩等待才休息" width="920">

## 怎样协作

<img src="docs/images/how-it-works.svg" alt="Owner、Lead、Executor 共用文件记录；普通程序看着记录并叫醒 Executor" width="920">

Owner 定方向，**Lead** 设计和验收，**Executor** 做约定好的事。两者之间说的每句话都落在普通文件里，几个不用模型的小程序看着这些文件：把变化变成事件、叫醒对的会话、发现规矩被破坏就报出来。[架构说明](docs/ARCHITECTURE.md)里有六张细图：通道、一个问题的一生、每日节奏、决定权和醒来循环。

## 设计原则## 设计原则

1. 程序校验规矩，人和 AI 角色判断研究。
2. 重复出现的错误进入可执行检查。
3. 设计、预算、结论、对外和删除进入提问，其余执行选择用 `decide` 记账。
4. GPU 部署以实际利用率衡量计算活动。
5. 汇报完成结果和具体依赖。


## 常用命令

Executor 使用 `python scripts/agent.py --as GPT 命令`，Lead 使用 `--as Claude`。`--data-dir` 选择项目，每次操作返回一个 JSON 对象。

| 命令 | 角色 | 作用 |
| --- | --- | --- |
| `wake` | Executor | 读取收信变化、事件与提问。 |
| `status` | Lead / Executor | 查看任务、流程事项、消息和巡检。 |
| `task` | Lead / Executor | 按各自权限流转任务。 |
| `ask` | Executor | 在五类范围内提交编号提问。 |
| `answer` | Lead / Executor | 按原编号回答。 |
| `decide` | Executor | 记录执行选择及原因。 |
| `veto` | Lead | 记录否决与替代方案。 |
| `events` | Lead / Executor | 按精确事件编号登记处理结果。 |
| `patrol` | Lead / Executor | 记录成果、心情和下一次巡检。 |
| `efficiency` | Lead / Executor | 查看已观测的等待与工作情况。 |

[完整命令](docs/agent-commands.md) · [醒来流程](protocol/heartbeat.zh-CN.md) · [可选 GPU 调度器](docs/optional-gpu-dispatcher.md)

## 项目目录

```text
board/       网页应用、持久化状态和手账界面
scripts/     命令、安装、巡检和打包工具
protocol/    角色、生命周期、决定和醒来约定
personas/    Lead 与 Executor 角色卡
templates/   任务与报告模板
docs/        架构图、截图和部署说明
assets/      图像元数据与第三方说明
data/        首次启动创建的本地项目记录
```

## 实际运行带来的修正

参考部署出现过三类可量出的故障，分别推动了记录校验、决定分流和开工准备。

| 出现过的问题 | 根因 | 现在的约束 |
| --- | --- | --- |
| 一条错误格式的确认记录让守夜程序停了 **9.5 小时**。 | 事件编号字段混入了自由格式的值。 | 程序校验记录结构，事件通过命令工具按精确编号确认。 |
| **一天 47 次提问**，多数是执行细节。 | 日常选择挤进了主线的研究设计队列。 | 五类大事进入提问，其余用 `decide` 记账，Lead 保留 `veto`。 |
| 一次 **24 小时**租用审计中，只有 **53% 的卡时**在计算。 | 环境准备和判分占据了租用时段。 | 开租前备好并试跑队列，分配判分资源，提前设置收图与停止边界。 |

[角色约定](protocol/roles.md)、[醒来合同](protocol/heartbeat.md)和[GPU 适配器](docs/optional-gpu-dispatcher.md)写明对应的运行规则。

## 许可与致谢

代码和原创 SVG 采用 [MIT](LICENSE)。小赖字体采用 SIL Open Font License，字体随附许可原文。角色 PNG 的权利归原作者和角色权利人，使用范围见[图像说明](assets/README.md)。[第三方声明](docs/third-party-notices.md)记录随附材料。
