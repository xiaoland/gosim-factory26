# Double Runtime

Use this [Deployment](index.md) depth when a Double run's process, control,
storage, sealing, egress, or recovery behavior matters. Product claims and
module/compiler compatibility remain with Product Truth and Product TDD.

Each successful `svc double start` owns one UUIDv4 run beneath the platform
user runtime directory's `svc/double/runs` tree. The module's resolved location
selects and records its workspace identity; later commands locate the strict
self-describing run record by ID rather than interpreting the caller's current
directory. The run contains the normalized IR and workspace-contained
asset/contract snapshots, replay and digest facts, a bounded merged carrier log,
private control coordinates/capability, and carrier-written observation data.
Directories and files request user-only permissions under the established
same-user local trust boundary.

The carrier binds responder and control listeners to numeric loopback
addresses. Startup retains the exact isolated child handle until an
authenticated readiness receipt proves the expected run and snapshot; only
then may the mechanical launch attempt be released. Before readiness, failure
or interruption may terminate only that still-owned attempt. After release,
the execution record and historical PID are never double lifecycle or cleanup
authority.

Carrier memory alone owns active bindings, match counts, and journal state.
Startup and command-triggered files remain explicitly `sealed: false`
projections. Graceful stop closes response intake, settles owned work, writes
one same-directory atomically replaced `sealed: true` final snapshot, returns
the stop receipt, and exits. That sealed snapshot owns later observe and
idempotent stop. Journal projections always report total, retained, and omitted
counts. Missing, malformed, mismatched, or unreachable active control returns a
bounded `control-unavailable` result with the last labeled projection; the
client writes no terminal fact and performs no PID or process-tree action.

Default event targets are numeric loopback origins. A remote origin is admitted
only when both the scenario declares `explicit-remote` and start names the
target in an explicit remote allowlist; delivery follows no redirect and makes
one attempt. The responder, built-in generators, managed assets, and built-in
event injector have no undeclared egress path. The unsandboxed external
materializer and the independently launched Consumer retain explicit
`egress: not-enforced` operational non-claims, so safe CI also removes real
write credentials and supplies network isolation where required.

Double run data is volatile local evidence, not archival storage. Every start
is fresh, no latest-run or reuse lookup exists, and no automatic provider event,
timer, retry, stale-run takeover, or cleanup policy is inferred. Missing
volatile data fails closed rather than reconstructing authority from a module,
workspace, log, or process table.
