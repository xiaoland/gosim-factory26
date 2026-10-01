# Provider Extension Contract

## Principle

The public resource is an `agent-thread`, not a Codex thread. Codex is merely the
first source adapter. The core must be able to archive a future agent's native
thread evidence honestly even when that agent has no hidden reasoning, no tool
records, no local persistence, or a fundamentally different event model.

## Small Static Boundary

```text
svc telemetry agent-thread
        |
        v
agent-thread core: selector, archive, task references, diagnostics
        |
        v
static provider registry
        |
        +-- provider `codex` / adapter `codex-rollout-v1`
        +-- future provider adapter
```

The first delivery uses a normal in-process registry, not Python entry points,
dynamic package loading, a provider SDK, or configuration-driven plugins. Adding a
provider is a reviewed code change plus fixtures; it does not let arbitrary local
code execute under `svc`.

## Lean Adapter Contract

An adapter has three narrow operations:

```text
list_metadata(context) -> ThreadDescriptor[]
resolve(context, exact_selector) -> ResolvedThread
stream_capture(resolved, raw_sink, index_sink) -> CaptureEvidence
```

`ThreadDescriptor` contains only non-sensitive selection metadata: provider ID,
opaque thread ID, source state, and safe timestamps. `ResolvedThread` binds an
exact native source to the selected opaque identity. `CaptureEvidence` contains:

- an opaque `{provider_id, thread_id}` identity;
- one native raw artifact with a logical path, media type, source-format version,
  byte count, and hash;
- an optional generated record index with provenance into that artifact;
- capability declarations such as `messages=present`,
  `reasoning=opaque|summary|absent`, `tool_calls=present|absent`, and
  `attachments=present|absent`;
- user/assistant message-like `TextOccurrence` values for lexical task-packet
  discovery; and
- non-sensitive warnings/diagnostics.

The core owns ZIP layout, atomicity, permissions, manifest validation, and packet
copying. An adapter never writes the archive directly and cannot cause packet
selection based on its own unreviewable interpretation.

## Archive Compatibility

`manifest.json` is provider-neutral and schema-versioned. It names the provider,
adapter, one raw artifact, capability states, and provenance. Native records live
under `providers/<provider-id>/`; SVC does not normalize them destructively into a
fictional universal transcript. `thread/index.json` is optional derived metadata,
not the authority for raw evidence. A multi-artifact manifest is a new archive
schema contract, not an implicit adapter extension.

Adding a backward-compatible provider adapter is a Behavioral MINOR capability.
Changing the manifest meaning, task-reference rules, or existing archive layout is
reviewed as a Behavioral MAJOR change. Every provider needs contract fixtures that
prove unknown-field retention and accurate absence/opacity declarations.

## CLI Evolution

The first release defaults to its single static provider and keeps the concise
commands in the packet. The selector and manifest already carry `provider_id`.
When a second provider exists, add an optional `--provider <id>` with `codex` as
the backward-compatible default, rather than making the first user's command pay
for an abstraction that has no present choice.
