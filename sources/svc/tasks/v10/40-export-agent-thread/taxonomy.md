# Observability Taxonomy

## Decision

The public command family is `svc telemetry`; the first resource/action pair is:

```text
svc telemetry agent-thread list
svc telemetry agent-thread export ...
```

The implementation namespace is `svc_cli.telemetry`. `o11y` is an architecture
and documentation umbrella, not a public CLI spelling. `diagnose` is reserved for
commands that interpret the present health or failure of a running/project system;
it can consume telemetry evidence later but does not own its collection.

## Why Not `svc export`

`export` describes an output-format operation but not the user's intent, authority,
or future family. It would also make unrelated exports compete at the CLI root.
The thread bundle is a deliberately captured observability artifact used for
debugging, audit, handoff, and improving SVC.

## Privacy Boundary

`telemetry` does **not** mean automatic analytics. Every capture is explicitly
requested, stays local, creates one private archive, has no network side effect,
and requires sensitive-content acknowledgement. Future upload/aggregation would
be a separate authority, command, and protocol review.

## Future Shape

```text
svc telemetry agent-thread list|export
svc telemetry <other evidence resource> ...
svc diagnose <live system or evidence bundle> ...
```

This keeps collection, interpretation, and any future transport separate.
