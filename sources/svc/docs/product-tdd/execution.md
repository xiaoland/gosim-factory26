# Shared Execution Contract

Use this [Product TDD](index.md) depth when `run` and `dev` must share process
execution without sharing domain authority. It returns the cross-unit identity,
ownership, lifecycle, and failure contract; Product behavior and runtime data
locations remain with Product Truth and Deployment.

`run` and `dev` are separate public/configuration domains that share only a
private mechanical execution boundary. Domain controllers derive convergence
identity and retain semantic authority: `run` owns one named bounded command
intent in a worktree; `dev` owns capability scope, probes, readiness,
provisioning, stop, and later reuse. The shared mechanism owns one concrete
execution ID, atomic lifecycle facts, process ownership, policy-selected
capture, observation, settlement, and explicit release. Its neutral persisted
identity is `domain`, `operation`, `subject`, `workspace_instance`,
`intent_digest`, and `coordination_key`; domain projections restore names such
as run entry/effective-entry digest or dev target/effective-target digest.

One coordination lock is the ownership authority. The winning caller holds it
from publication through domain settlement; contenders join only the same
operation and intent. A different intent at the same coordination boundary
waits, re-evaluates, then executes rather than running in parallel. The
execution record is authoritative for its neutral identity, resolved argv/cwd,
non-secret env-file paths, log addresses, owner PID, timestamps, and mechanical
state. Native output remains project-owned bytes addressed through exact log
references rather than being interpreted as SVC results.

Run lifecycle is `starting -> running -> exited | interrupted | start-failed |
capture-failed | owner-lost`. Dev may additionally request `released` only
after its own readiness proof. An abandoned lifetime lock plus an active record
proves owner loss; the first later caller records that fact without starting a
replacement in the same invocation. PID observation alone never grants
takeover or kill authority.

Dev capability identity is `scope`, `target`, resolved `endpoint_id`, selected
`scope_id`, and `capability_id`. The capability ID binds namespace, scope,
scope ID, and target and is the shared ensure/stop coordination key; endpoint
and action declarations belong to the operation intent digest. Thus ensure and
stop serialize over the same capability while only equivalent ensure or stop
intents converge. Stop executes only a target-local Consumer declaration and
uses its final readiness probe as a postcondition; released process IDs are
never fallback cleanup authority.

Foreground run inherits stdin and the terminal process group, captures stdout
and stderr separately, and stays owned until child exit plus both stream EOFs.
An owner interrupt affects the execution; a follower interrupt only detaches
that caller. Dev provisioners remain isolated with null stdin and merged logs.
No shared public lifecycle API, daemon, process-tree guarantee, output-order
invention, readiness state, or project-artifact model follows from this reuse.
Schema-v1 execution records are an unreleased local cutoff: a still-held legacy
lifetime lock blocks v2 publication, settled files remain untouched, and
explicit inspection fails with `execution-record-schema-unsupported` rather
than field aliases or PID action.
