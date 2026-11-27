# 体验一次完整科研交接

[English](portfolio-demo.md)

通过一个虚构的缓存实验，依次查看问题、第一次回件、修订、部分采纳和下一项任务。示例使用本地文件，模型调用数为零。

## 启动

在仓库目录执行，使用 Python 3.11 或更新版本：

```powershell
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python scripts/portfolio_demo.py
```

macOS 和 Linux 将 `.venv/Scripts/python` 替换成 `.venv/bin/python`。

打开 http://127.0.0.1:18780。需要另选端口时加 `--port 18782`。演示数据保存在 `work/portfolio-demo`，再次启动沿用同一份数据。安装阶段下载 Python 依赖；示例运行使用本地文件，后台任务注册数为零。

## 沿着决定看成果

1. 查看研究进度：配对测量结果已经采纳，下一项工作是测量内存。
2. 打开导航中的“外置大脑”，查看缓存实验的两版回答。第一版混用了单位和批次，审核要求重新做配对测量；第二版采纳时间表，将内存测量留给下一任务。
3. 打开结果树中的“Paired cache pilot”。虚构样例的两批数据合计为基线 5 秒、缓存 3 秒，附带 CSV 展示逐批测量值。
4. 将结果标为已读，再开第二个标签页并刷新，查看共享阅读状态。在第二个标签页改为未读，刷新第一个标签页查看变化。
5. 展开任务清单，找到内存测量任务。手动发送交接包显示在个人待办中，研究任务继续保留负责人。

这里的耗时属于合成示例，用于演示从问题到采纳结果的过程。

## 重新演示并保留旧数据

先按 Ctrl+C 停止服务，再运行：

```powershell
.venv/Scripts/python scripts/portfolio_demo.py --reset
```

程序先把带演示标记的目录移动到相邻的 `portfolio-demo.archive-...`，再建立新示例。旧示例中的编辑保存在归档目录。重置范围限定在仓库 `work` 目录内、由这个入口创建的演示。加 `--init-only` 可单独初始化数据。

## 读实现

- [共享阅读状态](case-shared-reading.md)：稳定结果标识、串行写入和旧响应处理。
- [任务认领](case-task-claims.md)：进程锁、有限租约和写入范围冲突。
- [整体架构](ARCHITECTURE.zh-CN.md)：完整协作过程。

## 使用候选版本

保留现用代码和数据，先用合成示例体验候选，再用独立的数据副本试用。审阅后选择要运行的代码与数据组合，旧组合保留用于回退。
