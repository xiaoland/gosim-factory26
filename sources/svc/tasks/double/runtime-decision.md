# Double DSL and Runtime Decision Table

Status: superseded. The decision question and hard gates treated the Anana fake
servers as fidelity pressure cases, which Sir rejected as a requirements basis.
Use [`runtime-decision-v2.md`](runtime-decision-v2.md). This document authorizes
no syntax, dependency, or implementation.

## Decision Question

Which authoring/runtime shape can cover both simple contract doubles and the
behaviorally complex Anana pressure cases while keeping SVC's responsibility
small, trustworthy, portable, and maintainable?

## Alternatives

| ID | Alternative | Description |
| --- | --- | --- |
| A | SVC-native declarative behavior DSL | `*.double.yaml` contains the service behavior and SVC interprets it |
| B | Existing engine profile | SVC validates and runs a constrained Microcks/Imposter/WireMock-like configuration |
| C | Declarative DSL plus embedded scripts | Data model handles common cases; Python/JS/Groovy/Wasm hooks handle the rest inside the runtime |
| D | SVC-language SDK service | Consumer writes handler functions against an SVC-owned framework/runtime, initially Python |
| E | Opaque command | SVC starts an arbitrary command and checks readiness, with no double-specific conformance |
| F | Code-backed service driver | Consumer command/container implements provider behavior and a language-neutral double control contract; SVC supervises it |
| G | Layered driver model | One descriptor/conformance contract selects a simple declarative engine, code-backed service, official emulator, or real local service |

## Hard Gates

| Gate | A | B | C | D | E | F | G |
| --- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Represents both Anana cases without lying about semantics | Fail | Conditional on extensions/scripts | Pass | Pass | Pass | Pass | Pass |
| Stable reset/control/observation contract | Pass | Conditional | Pass | Pass | Fail | Pass | Pass |
| Does not make SVC own an arbitrary-code sandbox/runtime | Pass | Conditional | Fail | Fail | Pass | Pass | Pass |
| Keeps provider contract authority identifiable | Pass | Conditional | Pass | Pass | Fail | Pass | Pass |
| Language/runtime choice does not become an SVC-wide mandate | Pass | Conditional | Fail | Fail | Pass | Pass | Pass |

`A` fails the fidelity gate as a universal mechanism. `C` and `D` can express
the behavior but move general execution/runtime obligations into SVC. `E` is a
useful baseline but is almost indistinguishable from generic process lifecycle
and does not create the test-control value of `double`. `F` is the only focused
MVP boundary that passes every gate without assuming one service language.
`G` is the broader product topology, but brings more first-release scope.

## Weighted Criteria

Score meaning: `1` poor, `3` workable with material cost, `5` strong fit. Total
is `sum(weight * score / 5)`, out of 100.

| Criterion | Weight | Evidence confidence |
| --- | ---: | --- |
| Fidelity ceiling for real Consumer behavior | 16 | High: direct Anana source/tests |
| Human/Agent authoring and change locality | 12 | Medium: code/tool conventions; needs an Agent bake-off |
| Contract reuse and drift detection | 10 | High for tool capabilities; medium for proposed boundaries |
| Deterministic control and observation | 12 | High: direct tests and mature tool control APIs |
| Callback/event/fault/time/concurrency capacity | 10 | High: direct cases plus provider emulators |
| Runtime portability and dependency fit | 8 | Medium-high: published distributions and current SVC stack |
| Debuggability and double-self-testing | 8 | Medium-high: ordinary language/tool behavior |
| Clear trust and security model | 8 | High: arbitrary-code execution is an objective boundary |
| Containment of SVC scope and maintenance | 12 | Medium: architectural projection from current SVC owners |
| Migration and engine lock-in | 4 | Medium |

## Weighted Decision Matrix

| Alternative | Fidelity 16 | Authoring 12 | Contract 10 | Control 12 | Effects 10 | Runtime 8 | Debug 8 | Trust 8 | SVC scope 12 | Lock-in 4 | Total / 100 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A. Native declarative DSL | 2 | 3 | 5 | 5 | 2 | 5 | 4 | 5 | 2 | 2 | **68.4** |
| B. Existing engine profile | 3 | 4 | 4 | 4 | 4 | 3 | 4 | 3 | 4 | 3 | **72.8** |
| C. DSL plus embedded scripts | 5 | 3 | 4 | 5 | 5 | 3 | 3 | 1 | 1 | 2 | **68.4** |
| D. SVC-language SDK service | 5 | 4 | 4 | 5 | 5 | 2 | 4 | 4 | 2 | 2 | **78.0** |
| E. Opaque command | 5 | 3 | 1 | 1 | 5 | 5 | 4 | 5 | 5 | 5 | **76.0** |
| F. Code-backed service driver | 5 | 3 | 4 | 4 | 5 | 4 | 5 | 5 | 5 | 5 | **89.2** |
| G. Layered driver model from day one | 5 | 4 | 5 | 5 | 5 | 4 | 4 | 4 | 3 | 4 | **87.2** |

Scores are not measurements. They expose the judgments so they can be changed
without hiding the resulting decision. In particular, Agent authoring scores
remain lower-confidence until the same bounded behavior is authored and revised
under controlled prompts in ordinary code and candidate DSLs.

## Candidate-Specific Conclusions

### A. Native declarative behavior DSL

Useful as a later low-complexity driver, not a universal foundation. Supporting
Caocao geometry, idempotency races, callback acknowledgement and response-loss
commit points would either explode the language or create special cases.

### B. Existing engine profile

Microcks is now at least as important a candidate as Imposter: it is
contract-first, supports stateful scripts and OpenAPI callbacks. Its own design
also demonstrates the boundary problem—stateful behavior requires scripts, and
its useful inner-loop distribution is a substantial containerized runtime.

Imposter, WireMock, Hoverfly, Mockoon, and Mountebank remain valuable drivers or
adapters. None should become SVC's semantic foundation before a case proves a
net reduction in authoring and contract duplication.

### C. Declarative DSL plus embedded scripts

This looks flexible but has the worst ownership topology. Users still need to
learn the host DSL and its script API, while SVC inherits interpreter version,
module access, cancellation, stack traces, concurrency, resource limits, and a
security story. Calling it a “script hook” does not reduce those obligations.

### D. SVC-language SDK service

Better debugging than inline scripts and could generate useful protocol/control
plumbing. It still mandates SVC's language/runtime and makes the SDK a backend
framework surface. SDKs can be optional conveniences after a language-neutral
contract exists.

### E. Opaque command

Safely contains SVC scope but adds too little over current `svc dev`/`svc run`.
It cannot promise reset, arrangement, semantic observations, or contract
identity. It is the control baseline, not a sufficient double product.

### F. Code-backed service driver

This makes arbitrary behavior explicit Consumer test code. The project uses its
normal language, dependencies, debugger, type checker, and test framework. SVC
owns a small service conformance protocol plus lifecycle and identity, not a
service programming language. Existing Anana packages can conform incrementally
instead of being rewritten into an unproved DSL.

Its weakness is authoring cost: it does not make complex domain behavior free.
It reduces mechanical lifecycle/control/contract integration cost and gives
Agents familiar code rather than a novel DSL, but this claim needs a measured
spike.

### G. Layered driver model

This is the strongest long-term topology because it matches the fidelity tiers:

- OpenAPI examples/rules for simple contract responders;
- an existing engine adapter where it fits;
- code-backed services for provider-specific behavior;
- official emulators or real local services when available.

It scores slightly below `F` for an MVP because driver selection, normalized
capabilities, and conformance across heterogeneous runtimes increase SVC scope.
The conformance protocol should nevertheless be designed so `F` can grow into
`G` without migration.

## Sensitivity

- Increasing existing-engine Agent authoring from `4` to `5` adds only 2.4
  points; it does not close its fidelity and runtime-boundary gaps.
- Decreasing the service driver's authoring score from `3` to `2` removes 2.4
  points; it remains ahead of the single-runtime alternatives.
- Giving SVC maintenance less weight benefits embedded DSL/script approaches,
  but does not cure their hard-gate failure around arbitrary-code ownership.
- If future evidence shows almost all real doubles are simple request/response
  projections, `A` or `B` becomes a compelling first driver. It still does not
  replace the programmable escape boundary.

The result is robust to ordinary weight changes because it is driven mainly by
hard ownership gates, not small score differences.

## Research Recommendation

1. Do not select or design one universal behavior DSL.
2. Define a language-neutral **double conformance contract** first.
3. Treat `*.double.yaml` as a descriptor of boundary, contracts, driver,
   lifecycle, fixtures, and claimed capabilities—not necessarily service
   behavior.
4. Use a code-backed service driver as the pressure-case MVP candidate.
5. Keep the descriptor and conformance protocol compatible with a later layered
   driver model.
6. Evaluate Microcks/Imposter/other engines as optional drivers only after the
   exact simple tier and conformance protocol are known.
7. Do not embed an arbitrary script interpreter or promise a sandbox in the MVP.

This is a boundary decision, not yet a CLI or file-format decision. The next
evidence step is a no-source-mutation conformance spike using the two existing
Anana services, followed by an Agent authoring bake-off for one simple and one
complex slice.
