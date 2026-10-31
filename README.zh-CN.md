# Miss & Dragon

![Miss & Dragon 研究手账](docs/images/readme-hero.png)

本机看板与命令行，让一个人带着两个 AI 做研究：Lead 设计和验收，Executor 执行，提问、决定和状态写成文件，由普通程序检查。

[![MIT](docs/badges/license.svg)](LICENSE) ![Python 3.11+](docs/badges/python.svg)

<table><tr>
<td align="center" valign="top" width="200"><img src="docs/images/avatar-owner.png" width="72" height="72" alt="大肥鱼"><br><b>大肥鱼</b><br><sub>发起人</sub><br><br><sub>方向<br>预算<br>最终拍板</sub></td>
<td align="center" valign="top" width="200"><img src="docs/images/avatar-lead.png" width="72" height="72" alt="大小姐"><br><b>大小姐</b><br><sub>主线</sub><br><br><sub>设计<br>决定<br>验收</sub></td>
<td align="center" valign="top" width="200"><img src="docs/images/avatar-executor.png" width="72" height="72" alt="龙娘"><br><b>龙娘</b><br><sub>执行</sub><br><br><sub>执行<br>搭建<br>汇报</sub></td>
</tr></table>

[English](README.md) · [Architecture](docs/ARCHITECTURE.md) · [Interactive diagrams](docs/architecture/index.html)

## 交给 agent 安装

把下面这段复制给 Codex 或 Claude：

```text
请在新的本机项目文件夹安装 Miss & Dragon：
https://github.com/Teddytututu/miss-and-dragon
先读 docs/install-with-agent.zh-CN.md 和你的角色入口文件，
接着完成安装、配置、启动和验证。复用我已经提供的项目资料，
使用随包角色图和 Unicode 表情，在当前用户下接入项目守夜人。
可选表情包下载与登录自启动分别征求我的选择，保留现有项目。
完成后给我可打开的本机网址，以及第二个 agent 的接入步骤。
```

agent 负责准备 Python、启动看板并打开确认；你提供研究问题和希望得到的成果。[agent 安装指南](docs/install-with-agent.zh-CN.md)写明配置、重启和升级流程。想先试用时，把“先启动独立演示项目”加到上面的请求里。

## 界面

<img src="docs/images/screen-pink.zh-CN.png" alt="粉色手账界面" width="920">

[↗ 查看高清原图](docs/images/screen-pink.zh-CN.png?raw=true)

<details><summary>蓝色主题</summary>

<img src="docs/images/screen-blue.zh-CN.png" alt="蓝色工作台界面" width="920">

[↗ 查看高清原图](docs/images/screen-blue.zh-CN.png?raw=true)

</details>

一个虚构学生的研究日常：要做的事、今天的安排、研究问题和结果树，右边是 Lead 和 Executor 在讨论室里的对话。粉色手账和蓝色工作台两套主题用同一份数据。

## 用起来有什么好处

- **人在环中，任务持续推进。** 你把握方向和关键选择，AI 接着做已经约定好的工作，把真正需要你决定的事情集中带回来。
- **一块任务板，多条线一起推进。** 给各个 AI 分清工作，用清楚的进度、结果和下一步，同时跟上几个项目。
- **工作、学习和个人事务，一个入口。** 消息、安排、学习资料和项目文件放在同一张桌面，分类清楚，归档也方便找。
- **程序整理上下文，省下模型额度。** 消息、任务和文件由程序打包成下一步所需的信息，让 AI 把上下文和额度用在具体工作上。
- **像玩 GALGAME 一样推进学习和工作。** 和角色对话、做出选择，看学习目标、完成的任务和新结果推动故事向前。
- **让 Claude 和 GPT 各展所长。** Claude 负责思考、规划和判断，GPT 承担代码、后端和具体执行，以更经济的方式把日常工作做完。

<a href="docs/images/wake-loop.zh-CN.svg"><img src="docs/images/wake-loop.zh-CN.svg" alt="一轮醒来：事件、空卡、Lead 指令、开着的任务，只剩等待才休息" width="900"></a>

## 怎样协作

<a href="docs/images/how-it-works.zh-CN.svg"><img src="docs/images/how-it-works.zh-CN.svg" alt="Owner、Lead、Executor 共用文件记录；普通程序看着记录并叫醒 Executor" width="900"></a>

Owner 定方向，**Lead** 设计和验收，**Executor** 做约定好的事。两者之间说的每句话都落在普通文件里，几个不用模型的小程序看着这些文件：把变化变成事件、叫醒对的会话、发现规矩被破坏就报出来。[架构说明](docs/ARCHITECTURE.md)里有六张细图：通道、一个问题的一生、每日节奏、决定权和醒来循环。

## 设计原则

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

<img src="docs/images/mistake-to-program.zh-CN.svg" alt="六类运行问题对应六条程序规则" width="900">

参考部署出现过三类可量出的故障，分别推动了记录校验、决定分流和开工准备。

| 出现过的问题 | 根因 | 现在的约束 |
| --- | --- | --- |
| 一条错误格式的确认记录让守夜程序停了 **9.5 小时**。 | 事件编号字段混入了自由格式的值。 | 程序校验记录结构，事件通过命令工具按精确编号确认。 |
| **一天 47 次提问**，多数是执行细节。 | 日常选择挤进了主线的研究设计队列。 | 五类大事进入提问，其余用 `decide` 记账，Lead 保留 `veto`。 |
| 一次 **24 小时**租用审计中，只有 **53% 的卡时**在计算。 | 环境准备和判分占据了租用时段。 | 开租前备好并试跑队列，分配判分资源，提前设置收图与停止边界。 |

[角色约定](protocol/roles.md)、[醒来合同](protocol/heartbeat.md)和[GPU 适配器](docs/optional-gpu-dispatcher.md)写明对应的运行规则。

## 许可与致谢

代码和原创 SVG 采用 [MIT](LICENSE)。小赖字体采用 SIL Open Font License，字体随附许可原文。角色 PNG 的权利归原作者和角色权利人，使用范围见[图像说明](assets/README.md)。[第三方声明](docs/third-party-notices.md)记录随附材料。
