# `svc double` MVP Final Design Review

Status: completed pre-implementation review on 2026-08-10. This is task
evidence; [`design-v2.md`](design-v2.md) and
[`impact-handshake-v2.md`](impact-handshake-v2.md) contain the amended review
candidate. [`bsl-v0-contract.md`](bsl-v0-contract.md) fixes the corresponding
concrete authoring surface.

## Verdict

The product direction and accepted command family remain sound:

```text
svc double validate MODULE
svc double start MODULE
svc double emit RUN_ID EVENT
svc double observe RUN_ID
svc double stop RUN_ID
```

The V2 draft was not safe to implement unchanged. Final review found seven
material inconsistencies. Each has a bounded resolution; none requires a
different product or a service DSL.

## Findings and Resolutions

| Finding | Why it matters | Resolution |
| --- | --- | --- |
| The CLI could mark an unreachable carrier `lost` even though the carrier was the stated semantic authority. | A transient control failure could create two incompatible run truths while a responder remained live. | Remove client-authored `lost`. The carrier alone mutates active run state. A control failure is an operation result, `control-unavailable`, with the last unsealed snapshot and no PID action. A graceful stop seals the final snapshot, which then becomes the immutable observation authority. |
| The concrete `$bsl` example referenced a project DVLA generator while MVP explicitly has no project generator/plugin registry. | The proposed user example could not compile under the proposed product. | Admit only the closed SVC generator set in BSL v0. Domain-specific values use managed examples/captures or the whole-envelope external materializer. Replace the example with supported RFC UUID/opaque-token nodes. |
| Product assertions were described as a BSL role even though the Consumer test is the sole product oracle. | This invites the descriptor to encode its own answer. | Product assertions are outside the BSL grammar. Request matchers, output validators, and Consumer product assertions are three different authorities. A product-assertion field is a compile error. |
| The example bound a callback target URL containing a path while the event also declared a request path. | URL joining and signing bytes would be ambiguous. | A target binding is an origin only; the event owns the exact path/query. Default targets must be numeric loopback origins. Remote delivery requires module declaration plus CLI opt-in, follows no redirects, and never lets materializer output select the target. |
| Active files were called projections, but `observe` after `stop` had no final authority. | Either observation disappeared with the process or files silently became a second mutable owner. | Make the authority transition explicit: active carrier memory is authoritative; carrier-written files are unsealed projections; graceful stop closes the responder and atomically seals the final facts/journal before exit; only the sealed snapshot is authoritative afterward. Truncation is always reported. |
| `validate` and immutable-run wording did not bound arbitrary materializer code. | Validation could unexpectedly execute code, and edited scripts could change an active run despite the IR snapshot claim. | `validate` never invokes a materializer. A materializer runs only for a matched response or explicit event emission. SVC snapshots all BSL-owned assets/contracts, but reports materializer code identity, determinism, network access, and fidelity as unenforced. |
| Mandatory CEL native wheels would broaden the base install and have no inspected source-distribution fallback. | A user who never uses `double` could lose installability on an unsupported platform. | Ship the three double-only libraries as a `double` optional dependency extra. The command grammar remains present in the base CLI and returns a precise install continuation when the runtime extra is absent. CI tests both base-install isolation and the extra-installed feature. |

## Additional Contract Tightening

- Module location selects its workspace; later commands use the exact UUIDv4
  run ID and self-validating run record, not the caller's current directory.
  Local assets resolve relative to the module but may not escape the selected
  workspace.
- Scenario digest and run-context digest are different. The latter also binds
  target origins, seed, fixed clock, generator/runtime versions, and snapshot
  hashes.
- Execution is deterministic for the complete reported replay tuple. Omitted
  seed/clock values are selected once and returned; exact replay supplies the
  reported values explicitly.
- BSL-owned regex matchers use the restricted CEL profile. OpenAPI/JSON Schema
  validation remains a separate pinned contract-validator fact and does not
  silently become a BSL semantic matcher.
- The initial OpenAPI profile admits static operation paths only. Path-template
  matching, OpenAPI 3.0, remote references, custom dialects, full-document
  conformance, and provider behavior remain explicit non-capabilities.
- Runtime HTTP failures are distinguishable: no match, ambiguous match,
  malformed/oversized request, request-contract failure, capture conflict,
  response/materializer failure, and event transport/acknowledgement are
  separate facts and exit/result categories.
- Reusing `_execution` remains justified only for the owned carrier launch
  attempt. The double run record/control capability owns semantic lifecycle;
  import boundaries and existing run/dev compatibility are part of the impact.

## Go/No-Go

With the amendments above, the plan is **ready for an explicit implementation
authorization**. Implementation is not yet authorized. Any source work must use
the amended Impact Handshake and return to review if it needs project config,
automatic events, stateful scenarios, a foreign engine, a new protocol, or a
broader code execution boundary.
