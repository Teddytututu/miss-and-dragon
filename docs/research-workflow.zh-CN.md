# 从问题走到可用结果

先说清结果会改变哪个决定。虚构示例要决定缓存是否值得继续测试：两种方法使用同一批输入、同一时间单位，内存另开一项测量。

## 跑完示例

准备 Python 3.11 或更新版本，在解压后的项目目录执行：

```sh
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python scripts/demo_research.py --data-dir work/my-study
.venv/Scripts/python -m board start --data-dir work/my-study --port 18780
```

macOS 和 Linux 将后面三行的解释器换成 `.venv/bin/python`。打开 `http://127.0.0.1:18780`。

1. 在“结果”打开 Paired cache pilot。首段给结论，同一批输入放在一起比较，正文可打开 CSV。
2. 标成已读后刷新、重开。阅读状态跟随报告；标题改名保留已读，摘要更新会重新提醒。
3. 展开“正在做”里的“时间表”。第二批接在第一批后面，新模型显示“待试跑”。支持左右拖动、Ctrl 加滚轮、缩放按钮和全屏；主题与装饰拖动沿用原界面。
4. 点侧栏“外置大脑”看两版回答：首版因混用单位退回，第二版的配对计时表被部分采用，审核意见连接到测内存的 T002。
5. 手动发送研究包的事项放在“需要你做的”；资源时间表只排有测量的作业。

这些命令全程使用本地文件，模型调用为零，后台定时任务注册为零。关闭前台服务即结束演示。

## 同一份实测计划贯通页面与命令行

`attachments/resource-plan.json` 保存有顺序的整票作业和测量。测量明确写 `unit`、`seconds`、`units`。整批九小时就写 `unit: "batch"`，整批占一张卡九小时。作业可写前置依赖、正在使用的卡号和已跑秒数。

```sh
python scripts/agent.py --as GPT --data-dir work/my-study resource-plan
python scripts/agent.py --as GPT --data-dir work/my-study resource-plan --cards 1 --now 2026-01-01T10:00:00+08:00
python scripts/agent.py --as Claude --data-dir work/my-study packet cache-pilot show
```

一张卡先跑两小时再跑三小时，依次在 12:00、15:00 结束。第三项等待自己的实测。当前库存和历史完成分别记录；采样时刻与本轮计算时刻分别显示。

## 在原问题下审回答

每包保存原问题、输入、各版原文和回件。负责人选择采用、部分采用或退回，写清采用哪部分、交给哪项任务继续。修订稿单独成版，原文件继续保留。操作见[手动研究包](manual-packets.zh-CN.md)。

报告围绕决定写：开头给结论，同条件比较放一起，用一个例子解释差别。失败改变了后续做法，就把原因和改变写清楚。示例首版混用单位、第二版改为配对计时，正好演示这一点。

## 按项目选分工

本人决定方向与资源，负责人定义问题和审结果，执行者落实已同意的工作。分工可以由人、本地工具或可选模型会话承担。先跑本地例子，再按既有安装指南连接项目所需工具。
