# Declared Development Capabilities

Use this [Product Truth](index.md) projection when a project declares a
long-lived development capability. It owns what independent callers can
observe and request; cross-domain execution mechanics and runtime persistence
remain with Product TDD and Deployment.

SVC lets independent Agent, Human, editor, and CI callers observe and express
one named long-lived development capability without starting the same intent
twice. Readiness, coordination scope, provisioning, access, and optional stop
cleanup remain Consumer declarations integrated by SVC rather than
reimplementations of HTTP servers, package managers, Compose, or project
scripts. Once readiness is proved, the capability survives the starter CLI and
native output remains available through a stable shared log.

Ensure and stop serialize at the same capability boundary, while equivalent
callers converge on the same observable execution. Stop runs only declared
Consumer cleanup and verifies the final readiness state; a historical PID is
never cleanup authority. This preserves Consumer ownership rules such as an
attached client refusing to tear down another repository's runtime.

## CLI Contract

An optional `dev.targets` map declares named capabilities directly. Each target
has a scope (`worktree`, `repository`, or `host`), one readiness probe (`http`,
`tcp`, or `exec`), an executable or manual provisioner, and an optional
target-local executable or manual `stop` action. Default text serves ordinary
Agent/Human use; compact JSON is the deliberate scripts/CI projection:

```bash
svc dev identity --repo /path/to/project --json
svc dev status --repo /path/to/project --json
svc dev status frontend --repo /path/to/project --json
svc dev ensure frontend --repo /path/to/project --json
svc dev stop frontend --repo /path/to/project --json
```

Root `status` summarizes declarations only; `svc dev status` observes declared
targets without starting or taking over a process. `ensure` handles one declared
target, reuses a healthy endpoint, refuses an occupied but unhealthy endpoint,
and does not run a `manual` provisioner. `stop` runs only Consumer-declared
cleanup and never infers authority from a recorded PID. Executable work is coordinated
at the declared scope and releases process authority once readiness succeeds.
Worktree scope is the default and its probe endpoint must prove the resolved
instance; host scope requires a declared `host_key`.

Dev values may interpolate only `${dev.instance}`, `${dev.worktree.id}`, and
`${dev.target}`. Commands are argument arrays, not shell snippets, and their
configured working directories must remain inside the workspace.
