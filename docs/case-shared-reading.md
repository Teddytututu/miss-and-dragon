# Reading state across tabs

Two open tabs can observe the same report at different times. Reading a report should follow its identity, survive a server restart, and become unread when its visible result changes.

## Request path

`board/index.html` computes a result key and a content version. `board/tree-read-sync.js` sends the choice to `POST /api/tree/read`. `board/app.py` dispatches it to `board/tree_reads.py`, which updates `attachments/tree-reads.json` through `storage.update_json`.

The key prefers the result's `id`, then its main report path, then its title. A result with a stable ID or path keeps its reading identity when renamed. The content version tracks the summary, main report reference, page and status. Two reports with the same title retain separate keys.

## Write and refresh behavior

The browser queues its writes in a Promise chain. The server serializes each read-modify-write under `storage.locked`, changes only the selected key, increments a revision and writes JSON by atomic file replacement. State remains on disk across process restarts.

Every response contains the revision and the marker map. A tab ignores a response older than the highest revision it has already applied. The existing board refresh fetches shared state every 20 seconds; a manual refresh fetches it immediately. Changes to different keys survive concurrent writers. For competing choices on the same key, the last serialized server write determines the final state.

An explicit unread choice stores `null`, so older browser title markers stay superseded. On first refresh, matching historical browser markers migrate only where shared state has no choice for that result.

## Failure semantics

A request failure shows an error and offers a retry through the existing button. The browser's Promise chain is in-memory; server-acknowledged choices persist in the project file. Each retry sets a node's desired state again, so repeated read requests preserve the desired marker while advancing the revision.

This design uses a server lock and revision ordering. The revision is for applying responses; the mutation endpoint accepts the requested state without an expected-revision precondition.

## Trace it in the code

- `board/index.html`: `treeVersion`, `treeReadKey`, `treeSavedVersion`, `treeReadVersionMatches`.
- `board/tree-read-sync.js`: `install`, `apply`, `mark`, `mergeLocal`.
- `board/tree_reads.py`: `node_key`, `choose`, `snapshot`.
- `board/storage.py`: `locked`, `update_json`, `write`.
- `tests/tree-read-identity.test.cjs`: renames, duplicate titles, old response ordering, explicit unread and migration.
- `tests/test_v060_integrations.py`: shared state in the board snapshot.

For an interview, demonstrate the two-tab sequence in the [local walkthrough](portfolio-demo.md), then explain why stable identity and content version are separate values.
