# Deployment

Deployment is an optional owner for non-trivial runtime and operational truth:
packaging, environment configuration, migration, rollout, telemetry,
mitigation, rollback, recovery, and runtime data locations. Create it only
when operators or developers need stable information that executable
configuration, automation, or platform definitions do not expose clearly
enough.

Reality work may use logs, metrics, traces, and runbooks as evidence, but the
diagnosed cause selects the durable owner. Keep Product promises in Product
Truth, cross-unit wire rules in Product TDD, and repeated code-local tripwires
in the nearest local `AGENTS.md`.

Current operational projections are:

- [local shared execution](execution.md)
- [Double runtime](double.md)
- [Agent evidence runtime](agent-analysis.md)

Keep an operational runbook in this documentation only when a response needs
repeatable observation, mitigation, rollback, and recovery steps.
