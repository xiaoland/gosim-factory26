# Coding Agent Evidence and Analysis Contract

Use this [Product TDD](index.md) depth when telemetry, bundle validation, analysis, provider adapters, and Agent callers must share one evidence identity and compatibility boundary. Product meaning remains in Product Truth; runtime capture and recovery remain in Deployment.

Evidence bundle v4 contains a minimal manifest, required `trajectory.jsonl`, and one or more declared `native/` or `blob/` materials. Its identity binds provider/source identity, selected roots, exact trajectory bytes, and every material byte. The manifest records only material location, format, integrity, collection gaps, and the information required to interpret the trajectory; it is not a second event inventory.

Trajectory v2 is an ordered JSONL contract with one header, execution declarations, and typed semantic events. Event order is deterministic export order, not inferred causality. Each event has a stable ID, execution ownership when known, non-empty source references, mapping confidence, actual normalized payload, optional timestamp/turn/predecessors, and versioned extensions. The common event kinds are message, reasoning, tool call, tool result, lifecycle, context change, relation, usage, and provider event. Public payloads are discriminated models; provider-specific JSON cannot redefine common fields.

Relations distinguish `delegation` from `history_inheritance`. Coverage separately reports relation mapping and descendant closure, so a known parent/child edge can be complete while missing child material leaves closure and usage partial. Pi `parentSession` is history inheritance, not delegation.

Usage events preserve owner, scope, temporality, measurements, sample/counter identity, reset/baseline facts, and reported/estimated source. Aggregation sums only compatible independent deltas; cumulative counters are differenced by counter identity, gauges are not summed, duplicate conflicts are ambiguous, self and subtree are not added, and currency/source groups remain separate. Missing metrics remain missing.

Analysis API v3 uses generated JSON Schema 2020-12 models. Query is the closed union `overview | trace | profile | match`; read is exact-ref or native-forward with opaque continuation. Cursors bind evidence, version, intent, selector/order, and position. Pagination never changes coverage, and byte budgets apply to the complete encoded response. Validation errors identify bounded field paths; success is one JSON value on stdout and errors are one structured JSON value on stderr.

Compatibility is explicit: versionless and explicit v3 requests both use
analysis v3 with evidence v4. Analysis v1/v2 requests and evidence v1-v3 are
rejected. Analysis never imports a provider normalizer to repair an old bundle.
