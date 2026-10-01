# Bounded User-Message Review Protocol

## Authority and Purpose

The product owner explicitly authorized the collector to personally review
enough user-authored message text to decide whether a candidate thread is worth
preserving. This is a selection aid, not behavioral analysis and not a new SVC
CLI feature.

## Hard Boundary

- Resolve every exact candidate through the Codex provider's normal
  `CODEX_HOME` containment and regular-file checks before reading its rollout.
- Read only records classified as user-role messages. Do not inspect assistant,
  system, developer, reasoning, tool-call/result, attachment, title, CWD, or
  rollout-path content. Exclude provider-injected runtime context and synthetic
  subagent-notification envelopes from the human-intent review.
- First pass: inspect the first and latest non-empty *human-intent* message,
  each capped at 1,200 characters. When an initial envelope bundles execution
  context with the request, inspect only its trailing request portion. Escalate
  only an ambiguous candidate to its remaining human-intent messages, still
  without reading non-user records.
- Do not write review output to a file or include message content in source,
  task packets, the external inventory, commentary, or the final response.
  The collector may view the bounded output transiently in its protected review
  session.
- Do not export a new candidate until its review says `retain`. Any already
  exported provisional archive is reviewed under the same rule before it is
  admitted to the final corpus.

## Candidate Funnel

1. Build a maximum five-candidate shortlist per host from safe metadata,
   deliberately varying time window, lifecycle state, and duration where those
   descriptors exist. Include already-exported provisional samples.
2. Personally perform the bounded first pass for each candidate.
3. Classify each as `retain`, `exclude`, or `needs-review`, with compact tags
   such as product framing, implementation, diagnosis, release, or handoff.
4. Review only the ambiguous candidates further; then select at most eight
   retained threads across all hosts.
5. Export accepted uncollected threads through `svc telemetry agent-thread
   export`; retain existing accepted archives. Do not delete rejected
   provisional archives until the product owner confirms the cleanup scope.

## Collection Record

The external inventory may contain only host, opaque ID, timestamps/state,
classification tags, a non-quoting decision rationale, archive hash/size, and
the final decision. It must never contain an excerpt or a derived detailed
summary of a user message.
