# Proposed `svc dev` Protocol

## Product Model

`svc dev` ensures a declared development capability, not a package-manager command or a guessed process. A target has five independent parts:

| Part | Meaning | Authority |
| --- | --- | --- |
| capability | Stable semantic name such as `frontend` or `backend` | Consumer config |
| profile and scope | Which environment and worktree/repository instance is intended | Consumer config plus resolved workspace identity |
| probe | Observable proof that the intended capability is usable | Current probe result |
| provisioner | Explicit action allowed when the probe proves absence | Consumer config |
| evidence | Attempt ID, process handle, timestamps, observations, and logs | Transient SVC projection |

Process, port, `portless`, Docker, VS Code, and npm are possible implementation surfaces. None is the protocol authority.

## Command Surface

```text
svc dev status [<target>] [--repo <path>] [--json]
svc dev identity [--repo <path>] [--json]
svc dev ensure <target> [--repo <path>] [--json]

svc dev setup vscode [<target>] [--repo <path>] [--plan | --apply <digest>] [--json]
svc dev setup npm [<target>] [--repo <path>] [--plan | --apply <digest>] [--json]
```

`status` resolves `svc.json` plus `svc.local.json`, observes selected targets, and reports configuration/probe/runtime evidence without starting anything. `identity` reports the normalized execution/repository/worktree/profile identity and safe interpolation values for consumer wrappers.

`ensure` resolves the target from effective configuration and converges the runtime directly. It does not accept an arbitrary command string or discover an existing package script. Setup consumes the same declared targets and creates only the selected integration projection.

For commands that perform high-risk writes to non-SVC-owned content, `--plan` and `--apply` are mutually exclusive. Omitting both remains plan-only for compatibility, but documentation uses explicit `--plan`. Apply always reconstructs the current plan and accepts only its exact digest. This rule applies to setup projections; it does not turn `status`, `identity`, or direct runtime `ensure` into planned commands.

## Probe and Provisioner Spine

Initial probe kinds:

- `http`: bounded GET by default, no redirects, explicit accepted status range; strict TLS unless a loopback-only insecure mode is explicitly declared;
- `tcp`: bounded connection to a declared address;
- `exec`: exact argv whose zero exit status is the consumer's readiness proof, with bounded output and timeout.

Initial provisioner kinds:

- `exec/run`: a long-lived process supervised through readiness for this attempt;
- `exec/activate`: a bounded action such as `docker compose up -d` that may exit before the probe becomes ready;
- `manual`: observe-only; if absent, return a required human action without mutation.

All argv boundaries are arrays and run without an SVC-created shell. SVC does not record inherited environment values. Consumer configuration may use only documented, non-secret interpolation tokens such as `${dev.instance}`, `${dev.worktree.id}`, `${dev.profile}`, and `${dev.target}`; substitution never changes argv element boundaries.

## Ensure State Machine

```text
validate config
  -> resolve profile/worktree/instance/endpoint
  -> probe
      healthy and instance verified -> reused
      responder fails predicate      -> blocked; preserve it
      absence proved                 -> acquire capability lock
                                          -> probe again
                                          -> provision once
                                          -> poll readiness
                                              ready      -> started
                                              child exit -> failed + cleanup result
                                              timeout    -> failed + cleanup result
```

The lock covers the second probe, provision, and readiness wait. A waiter always re-probes after acquiring the lock. Only evidence created for the current attempt can authorize its failure cleanup. Cleanup is reported as `completed`, `partial`, or `unknown`; no generic cross-session `stop`, `restart`, `killall`, or stale-PID termination exists in the first release.

## Output Contract

Machine output includes the effective config schema/profile, target, scope, worktree/instance identity, probe observation, outcome, declaration digest, and only relevant transient evidence. It never emits secret environment values.

Successful runtime outcomes are `healthy`, `reused`, or `started`. Non-success outcomes distinguish configuration invalidity, instance provenance failure, occupied-but-unhealthy conflict, manual action required, lock timeout, child exit, readiness timeout, and cleanup uncertainty. Human output leads with whether testing can proceed, its access URL, and the next actionable evidence such as a log path.

## Deliberate Exclusions

- No automatic framework, package-manager, command, port, proxy, container, browser, or IDE discovery.
- No bundled `portless`, HTTPS certificate authority, remote daemon, or machine-global process registry.
- No claim that a bind-mounted repository shares PID, network, lock, or loopback namespaces across host/WSL/container boundaries.
- No VS Code `launch.json`, debugger configuration, source-map, browser, compound, or `envFile` generation in the first setup adapter.
- No auto-removal of orphan generated Tasks/scripts and no takeover of conflicting Consumer-owned entries.
