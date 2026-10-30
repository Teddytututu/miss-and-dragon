# Optional shared-resource guard / 可选共享资源守卫

The guard observes configured shared resources and produces bounded events for the original assistant session. Deployment configuration defines approved users, reserved devices, capacity floors, running-job identities and sampling intervals.

- Attribute GPU processes by user and verified process identity; efficiency totals include the acting assistant's owned observations.
- Record timestamped snapshots. Missing or stale observations produce an observation event, with the last valid identity retained for comparison.
- Check free local and remote disk capacity before a new batch. Resolve the destination's actual volume, including directory junctions, and account for the expected write size.
- Keep currently running jobs under their existing contracts. New capacity policies apply at explicit batch-admission boundaries.
- Deduplicate events by resource and condition. Route local capacity to maintenance and remote jobs to the experiment role.
- Recover a helper only when its recorded identity and deployment authorization match the observed process. Existing user jobs keep their owner-controlled lifecycle.

This guide defines an adapter contract. The board's core stays a loopback application; installing a guard and choosing its scope follow the user's deployment choice.

守卫观察资源归属、进程身份、时间戳与容量，并按事件分工送回原会话。容量门按真实目标卷计算新批写入后余量，现役作业沿原有合同运行。安装范围、保留容量与采样周期由部署方配置。
