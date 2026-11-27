# One task, one active claim

Several worker processes may wake for the same queued task. They need to agree on ownership before writing into shared files. Miss & Dragon represents that agreement as a finite lease with a worker identity, write scope, heartbeat and random claim token.

## Claim path

`scripts/workers.py claim` enters `board/workers.py::claim`. The function validates the task identifier and relative write scopes, then enters `storage.locked(root)`.

Inside that critical section it archives expired leases, calculates the allowed worker count, and checks active task IDs, worker IDs and overlapping write scopes. An accepted claim is created with exclusive file mode under `attachments/locks/<task>.lock`. Its lifecycle transition is published before the function returns.

The lock combines an in-process reentrant mutex with an operating-system file lock. Windows uses `msvcrt.locking`; Unix uses `fcntl.flock`. Independent Python processes therefore share the same exclusion boundary.

## Heartbeat, release and recovery

The lease expires after 1,800 seconds without a heartbeat. Heartbeat and release require the current random token. If another worker has reclaimed an expired task, the older token cannot update the new lease.

Release publishes the task's next status and archives the lease. If publishing the initial lifecycle transition fails, the claim is moved into an unpublished history record and the caller receives the error. Preserved records make it possible to inspect what happened.

The lease coordinates cooperating local workers. Task acceptance remains a separate lifecycle decision; a worker releasing its claim means its assigned work has reached the submitted status.

## Two useful races

1. Four independent processes request the same task and scope: one obtains the lease, and three receive the occupied result.
2. A worker requests a parent scope while another holds a descendant: the overlap check keeps the current writer's scope reserved. Sibling names such as `board` and `board-extra` remain distinct.

## Trace it in the code

- `scripts/workers.py`: public claim, heartbeat and release commands.
- `board/workers.py`: `claim`, `update`, `scope`, `overlaps`, `effective_worker_limit`.
- `board/storage.py`: `locked` and durable JSON writes.
- `board/lifecycle.py`: `_worker_transition` and the shared state publication.
- `tests/test_v02_workers.py`: thread race, independent-process race, expiry, token checks, scope boundaries and state preservation.
- `tests/test_v025_public_boundaries.py`: publication failure and the lifecycle entry.

For an interview, start with the duplicate-wake scenario, show the process race test, then explain how ownership expiry differs from successful task completion.
