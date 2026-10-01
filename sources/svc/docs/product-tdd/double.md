# Double Boundary Harness Contract

Use this [Product TDD](index.md) depth when Double compiler, carrier, CLI, and
Consumer tests must interoperate. It returns the module, IR, authority,
lifecycle, and compatibility contract; Product rationale and runtime storage
remain with Product Truth and Deployment.

The Consumer-owned `svc.double/v0` module is the authored authority for one
claim-scoped HTTP boundary scenario. The double compiler strictly parses that
surface, resolves only workspace-contained local assets and an optional local
OpenAPI 3.1 static operation, then produces an immutable runtime-independent IR
and scenario digest. YAML, JSON Schema, and CEL runtime objects never cross the
IR boundary. Provider references record provenance but are not fetched or
promoted into provider-currentness claims.

One start creates one run context over the scenario snapshot, target origins,
seed, fixed clock, generator/runtime versions, and asset/contract hashes. Its
run-context digest is distinct from the scenario digest. Request typed nodes
may match or capture; response/event nodes may use examples, immutable derived
values, the closed SVC generator registry, or managed content. Matchers select
boundary traffic and validators reject materialized output. Neither is a
Consumer product assertion. Restricted CEL exposes only bounded `request`,
`bindings`, `run`, and `scenario` values, with no project functions, I/O,
randomness, mutable state, or iterative macros.

Interaction requests may match structured JSON, byte-exact managed raw bodies,
or strict `application/x-www-form-urlencoded` field maps. Form matching uses
the same string matcher/capture algebra as query fields, preserves repeated
values as arrays, rejects malformed percent encoding, and does not add provider
state or a general content-decoding framework.

The native carrier owns the active responder, immutable bindings, event
delivery, and bounded journal. Exactly one interaction must match; no match,
ambiguity, malformed or oversized traffic, contract failure, capture conflict,
and materialization failure remain distinct fail-closed facts. The responder
never proxies or falls through. A named event is delivered only after explicit
`emit`, to a start-bound origin plus its authored path/query, without redirect
or retry. Remote targets require both module policy and command opt-in. A whole-
envelope external materializer cannot register routes or select a target, but
its process behavior remains outside SVC's sandbox and fidelity claims.

Authority changes once: carrier memory is authoritative while active, and
carrier-written files are unsealed projections; graceful stop closes the
responder and atomically seals the final facts/journal before exit, after which
the sealed snapshot is authoritative. `emit`, active `observe`, and first
`stop` authenticate to the carrier with a private capability. An unavailable
control endpoint yields `control-unavailable` plus the last labeled unsealed
projection; a client never writes terminal state or acts on a recorded PID.
The shared execution mechanism may own only the detached carrier launch
attempt. It has no double run, recovery, or product-verdict authority.

Public compatibility is the five-command family
`validate|start|emit|observe|stop`, its strict standalone module grammar,
structured result/error schemas, and exit classes: `0` objective met, `2`
grammar misuse, `3` resolved boundary non-success, and `4` infrastructure or
internal failure. `svc.json` remains unchanged, and the base CLI grammar/schema
surface remains importable without the optional double runtime libraries.
