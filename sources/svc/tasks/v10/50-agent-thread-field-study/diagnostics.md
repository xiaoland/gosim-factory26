# Windows List-Isolation Diagnostic

## Observation

On `win-ws.localhost`, released SVC 10.0.1 installed successfully at user scope,
but `svc telemetry agent-thread list --limit 100 --json` returned
`thread-source-unsafe` rather than safe descriptors.

## Safe Evidence

A read-only, query-only SQLite aggregate inspected no rollout content, paths,
thread IDs, titles, previews, or message data. It established that SVC's
selected `rollout_path` column contained 1,570 nonblank values: 1,568 resolved
inside `CODEX_HOME`, two resolved outside it, and none were unresolvable.

## Diagnosis

Path containment is the correct security boundary. The list operation lacks
per-row isolation: a small number of unsafe rows makes the complete bounded
inventory unavailable, including valid rows that it could safely report as
normal descriptors. This blocks safe selection and masks the distinction
between a bad source record and an unavailable provider inventory.

## Collection-Scope Workaround

For this field study only, a read-only query can select descriptors from rows
independently verified inside `CODEX_HOME`, exposing no fields beyond the list
schema. Each later capture must still invoke `svc telemetry agent-thread export`
by exact ID, which re-applies the provider's containment and source checks.

No CLI implementation change is made by this collection task. A future product
slice should define whether unsafe rows are represented as redacted descriptor
warnings, omitted with aggregate diagnostics, or handled through a separate
safe inspection command.
