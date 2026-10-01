# Deployment and Operation

Operating documentation preserves how to package, configure, start, change, observe, and recover the actual system.
It is useful when developers or operators need information that executable configuration or platform definitions do not expose clearly enough.
Its purpose is to make a response reproducible and its consequences understandable, including when an apparently successful action does not restore the intended service.

## Describe the Actual Operating Path

Record the supported environment, artifact and configuration sources, state and data locations, startup order, required external conditions, and useful observations.
Reference executable packaging, migration, and release definitions rather than copying commands or values that already have a maintained owner.
Explain non-obvious conditions, such as which state must survive a restart, when a migration is irreversible, or why two deployments cannot safely share a data directory.
Show how an operator obtains the relevant version and distinguishes configuration, process, readiness, and user-visible behavior.

Describe the observation that justifies an action, its affected boundary, and what success would look like afterward.
A process running does not establish that requests can reach it; a successful rollback does not establish that data is compatible or that external effects were undone.
Keep the response proportionate to the evidence and preserve useful error details before replacing the failing state.
Do not turn every possible failure into a speculative fallback.

## Make Recovery Usable

For a repeatable incident response, connect symptoms and affected users to relevant logs, metrics, traces, or state queries.
Identify immediate containment, a forward repair or rollback option, its conditions and effects, and how to verify recovery.
State which checkpoint or backup is sufficient, what other state must match it, and what valid progress or effects restoration can discard.
Unknown recovery prerequisites remain explicit; a code revision alone may not restore database or external state.
Permissions and release authority come from the consuming project, not from this documentation method.

For example, a failed migration leaves a service unable to open its database.
The task retains the exact error, attempted migration, artifact identity, and database state.
If a repeatable recovery route is established, the runbook explains how to identify the supported pre-migration backup, restore compatible application and data state, and observe normal reads and writes afterward.
It also states any writes lost by that choice and how they are handled.
“Restart the service” is insufficient if it neither restores compatibility nor observes the repaired behavior.

When an incident changes operational understanding, update the existing runbook with the supported condition and response.
Keep the original logs and failed attempts with the incident's task materials; retain durable procedures here.
Route a changed product promise to product documentation, a cross-unit failure agreement to technical design, and a diagnosed local hazard to nearby guidance.
Use the [operations template](../assets/templates/operations.template.md) when a reusable procedure needs its own entry.
