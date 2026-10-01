# Double Semantics and Runtime Decision, V2

Status: evidence-backed product recommendation, amended by
[`mock-data-governance.md`](mock-data-governance.md) and
[`language-decision.md`](language-decision.md), not source authorization. This
supersedes the Anana-pressure-case decision in [`runtime-decision.md`](runtime-decision.md).

## Decision Question

What is the smallest authoring model and runtime boundary that can support
black-box Consumer verification, including callbacks, without encouraging SVC
or an Agent to invent a second backend?

The previous question—“what can represent every behavior found in two complex
fake servers?”—was malformed. Expressiveness made those implementations the
target. This decision instead optimizes for trustworthy test claims and makes
unsupported complexity visible.

## Alternatives

| ID | Alternative | Semantic owner |
| --- | --- | --- |
| A | OpenAPI-derived auto-responder | Provider schema plus generated examples; no selected business semantics |
| B | Universal scenario/service DSL | SVC owns state, transitions, transforms, callbacks, and effects |
| C | Profile of an existing mock runtime | WireMock/Mountebank/Imposter/MockServer-like engine owns execution semantics; SVC constrains it |
| D | Native in-process test library | Consumer test language owns handler functions and fixtures |
| E | Managed boundary interaction harness | SVC owns strict responder, explicit event injection, matcher/generator/capture semantics, and journal |
| F | Code-backed fake service | Consumer owns arbitrary service behavior; SVC owns descriptor/lifecycle and optional observations |
| G | Official sandbox, provider test mode, or record/replay only | Provider or recorded traffic owns semantics |
| H | Layered multi-driver platform from day one | SVC normalizes A/C/E/F/G under a common capability model |

## Hard Gates

Weighted scores are considered only after hard gates. `Conditional` means the
candidate is not a safe product default without an additional profile or
conformance mechanism.

| Gate | A | B | C | D | E | F | G | H |
| --- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Drives a real black-box Consumer over the wire | Pass | Pass | Pass | **Fail** | Pass | Pass | Pass | Pass |
| Supports callbacks as direct Consumer stimuli | **Fail** | Pass | Conditional | Pass | Pass | Pass | Conditional | Pass |
| Does not invent provider semantics by default | Pass | **Fail** | Conditional | Conditional | Pass | Conditional | Pass | Pass |
| Fails closed, isolates tests, and never needs real egress in the fast lane | Conditional | Pass | Conditional | Pass | Pass | Conditional | **Fail** | Pass |
| Does not make SVC own an arbitrary-code runtime or application framework | Pass | Pass | Pass | **Fail** | Pass | Pass | Pass | Pass |
| Can identify contract/data provenance and unsupported fidelity | Pass | Conditional | Conditional | Conditional | Pass | Conditional | Pass | Pass |

Consequences:

- `A` remains a valuable schema/protocol sub-capability but cannot satisfy the
  callback requirement or selected outcome behavior alone.
- `B` is rejected as the product foundation. Its central affordance is exactly
  the unbounded semantic invention that the renewed evidence warns against.
- `D` reflects common application practice but does not satisfy SVC's
  process-level black-box goal and would turn an SVC SDK into a test framework.
- `G` remains necessary evidence for drift where available, but cannot be the
  deterministic, safe CI lane.
- `C` and `F` are useful adapters only with additional restrictions.
- `E` is the only focused first-slice alternative that passes all gates.
- `H` is a plausible long-term topology but is broader than the first product
  proof.

## Weighted Decision Table

Score meaning: `1` poor, `3` workable with material cost, `5` strong. Total is
`sum(weight * score / 5)`, out of 100. These are traceable judgments, not
measurements.

| Criterion | Weight | Evidence confidence |
| --- | ---: | --- |
| Verifies the named claim without invented semantics | 18 | High: research plus application/provider samples |
| Black-box, over-wire Consumer fit | 12 | High: SVC objective and application topology |
| Callback/event coverage | 10 | High: pretix, Zulip, provider tools |
| Deterministic isolation and fail-closed behavior | 12 | High: Zulip, Home Assistant, GOV.UK Pay |
| Human/Agent authoring and reviewability | 12 | Medium: Agent study plus conventions; needs bake-off |
| Provenance and provider-drift path | 10 | High: Stripe, GitLab, Fowler |
| Debuggability and interaction evidence | 8 | Medium-high |
| Runtime/distribution cost | 8 | Medium: depends on the chosen engine/package |
| Containment of SVC scope and maintenance | 10 | Medium-high: architectural projection |

| Alternative | Claim 18 | Wire 12 | Events 10 | Isolation 12 | Author 12 | Drift 10 | Debug 8 | Runtime 8 | Scope 10 | Total |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A. OpenAPI auto-responder | 3 | 5 | 1 | 4 | 5 | 4 | 4 | 4 | 4 | **75.2** |
| B. Universal service DSL | 2 | 5 | 4 | 4 | 2 | 3 | 3 | 3 | 1 | **59.2** |
| C. Existing-runtime profile | 3 | 5 | 3 | 4 | 4 | 3 | 4 | 2 | 4 | **71.6** |
| D. In-process test library | 4 | 1 | 4 | 5 | 5 | 2 | 5 | 5 | 5 | **78.8** |
| E. Managed boundary interaction harness | 4 | 5 | 5 | 5 | 5 | 4 | 5 | 4 | 4 | **90.8** |
| F. Code-backed fake service | 4 | 5 | 5 | 3 | 3 | 3 | 4 | 3 | 4 | **76.0** |
| G. Provider/sandbox/replay only | 5 | 5 | 3 | 2 | 4 | 5 | 3 | 2 | 5 | **78.4** |
| H. Layered platform day one | 5 | 5 | 5 | 5 | 4 | 5 | 4 | 2 | 2 | **85.2** |

The hard gates explain why `A`, `D`, and `G` do not become MVP despite higher
raw totals than some alternatives. `E` wins both the gates and the weighted
comparison.

## Recommended Semantic Boundary

Adopt `E`, a **managed boundary interaction harness**, as the research recommendation
for the first slice.

The host scenario language is not a service DSL and YAML is only a possible
surface syntax. It is a closed interaction language with these responsibilities:

1. identify the Consumer claim and provider boundary;
2. bind a provider contract or raw operation shape where available;
3. distinguish exact examples, matchers, semantic generators, captures, and
   derived values with provenance;
4. declare named inbound event material and explicit emission;
5. declare isolation, egress policy, redaction, and observation.

It may support captures and typed bounded expressions for correlation. It does
not include user-defined provider-domain functions, loops, unbounded control
flow, background jobs, general persistence, or automatic callback workflows.

This reframes `*.double.yaml` from “declarative service” to one serialized
module in a Boundary Scenario Language. Managed captured/example bodies remain
separate assets when nontrivial. The exact grammar is developed in
[`language-decision.md`](language-decision.md), but is not yet admitted.

## Code Escape Boundary

Code is allowed, but not smuggled into the interaction language.

- A **materializer command** is a narrow extension: deterministic input on
  stdin, one response/event envelope on stdout, no SVC SDK required. It is
  suitable for signatures, encryption, or provider-specific transformations.
- A **code-backed fake service** is a separate driver for cases that genuinely
  require broad state or concurrency. The Consumer owns, tests, versions, and
  reviews it as application test code.
- SVC does not claim semantic fidelity for either. It records declared
  provenance/capabilities and controls lifecycle/egress only to the extent the
  driver contract can enforce.

This keeps an escape hatch without making ordinary `*.double.yaml` Turing
complete or making SVC a backend framework.

## Runtime Decision: Semantic Ownership Now, Engine After a Bake-Off

The evidence is sufficient to decide the semantic boundary, but not yet the
concrete execution engine. Choosing an engine from feature lists would repeat
the earlier error. The runtime has two implementation shapes worth proving:

| Runtime shape | Advantages | Risks | Required proof |
| --- | --- | --- | --- |
| SVC-native narrow harness | Exact strict semantics; one install; first-class event injection and reports; no foreign runtime | SVC owns an HTTP server, match semantics, concurrency, shutdown, and security maintenance | Small implementation/maintenance estimate; HTTP conformance fixtures; parallel isolation; malformed input and shutdown tests |
| Pinned existing-engine adapter plus SVC event injector | Mature HTTP behavior and request journal; lower initial protocol implementation | Java/Node/container distribution; engine defaults may contradict SVC semantics; callback and provenance model split across tools | Exact-version reproducibility; fail-closed profile; no implicit sequencing; consumer acceptance; normalized diagnostics |

The first existing-engine comparator should be WireMock standalone because
GOV.UK Pay explicitly recommends it to application consumers and it covers the
strict HTTP responder/journal shape without requiring its stateful features.
`pay-run-amock` is a valuable conformance corpus and warning source, not an
obvious dependency. Imposter/Microcks remain comparators only if the narrow
profile exposes a missing requirement.

Therefore the runtime decision is intentionally two-stage:

1. **Decided**: SVC owns a small, engine-independent interaction model; no
   existing engine becomes the semantic authority and no service DSL is built.
2. **Not yet decided**: whether the first executor is native or a pinned
   WireMock adapter. A bounded, no-source bake-off chooses by observable
   conformance and distribution cost.

## Runtime Bake-Off Matrix

The bake-off uses the same artifacts and does not involve the rejected Anana
implementations.

| Case | Native harness | WireMock profile | Pass condition |
| --- | --- | --- | --- |
| Strict match | Run same request fixture | Run same request fixture | Exact match succeeds; near miss fails with useful diagnostic |
| Unexpected route | No route | No route | Failing non-2xx result; never empty `200`, never real egress |
| Response selection | One named outcome | One named outcome | No implicit cycling after retry |
| Capture/correlation | Capture one response/request value | Equivalent transformer/helper | Explicit binding into later event material |
| Semantic generation | Generate and validate one domain-meaningful field | Pinned semantic-generator extension | Same semantic intent, seed/clock, implementation version, matcher, and replay report |
| Event injection | SVC event emitter | Same SVC event emitter | Headers/raw body delivered; acknowledgement recorded |
| Isolation | Two parallel run IDs | Two isolated engine instances/namespaces | No route/journal/capture leakage |
| Provenance report | Native report | Adapter-normalized report | Same claim/fidelity/provenance fields |
| Distribution | Installed SVC environment | Pinned Java artifact/container | Offline CI startup, version identity, shutdown, size/time recorded |

Decision rule:

- both shapes must pass every semantic case;
- prefer the existing adapter only if its installed/distribution burden is
  acceptable and the normalization layer remains materially smaller than a
  native executor;
- otherwise prefer the native harness;
- do not add engine features to make it win a case not present in the V2
  requirements.

## Authoring/Runtime Spike Evidence

The no-source spike under
[`spikes/bsl-authoring-conformance/`](spikes/bsl-authoring-conformance/)
materialized one normalized BSL interaction and ran it through both a toy
native Python responder and pinned WireMock standalone `3.13.2`.

| Case | Native probe | WireMock `3.13.2` | Finding |
| --- | --- | --- | --- |
| Strict valid match | `201` | `201` | Same response bytes and SHA-256 |
| Invalid UUID | `404` | `404` | Both fail closed |
| Undeclared route | `404` | `404` | Both fail closed; no proxy enabled |
| Retry | Same body | Same body | No response cycling |
| Journal | Four local entries | Two matched, two unmatched | Both observable; WireMock journal is mature |
| Near-miss diagnostic | Empty response | 1,327-byte closest-stub explanation | Native design must explicitly fund diagnostics |
| Semantic generation | BSL-owned | Pre-materialized by BSL | WireMock did not reduce this responsibility |
| Capture/correlation | BSL-owned | Read from normalized WireMock journal | Adapter still needs normalization |
| Callback | Shared explicit BSL event injector | Shared explicit BSL event injector | No engine webhook/scenario feature required |
| Parallel isolation | Two concurrent probes passed | Separate ports, roots, processes, journals | Feasible, not a production stress result |
| Local distribution | Existing Python process | 19,530,671-byte JAR plus Java 17 | Material default-install burden |
| Local startup/RSS | Not isolated from probe process | 0.648 s / about 108,688 KiB | One-machine observation, not a benchmark |

WireMock provided clear value in HTTP matching, journal behavior, and near-miss
diagnostics. It did not own or eliminate semantic generation/validation,
replay, capture identities, callbacks, egress policy, or the BSL report. The
projection deliberately used none of WireMock's Handlebars/random helpers,
scenarios, webhooks, proxying, or response sequencing.

The default SVC CLI is currently Python-only; the spike host had Java but no
Docker. Requiring a JVM and a separately pinned 19.5 MB artifact for the first
slice is therefore not justified by the normalization work saved. The toy
native server is not itself an implementation proposal: its empty mismatch
response demonstrates that a production native executor must still implement
useful mismatch trees, journals, protocol limits, concurrency, and shutdown.

**Provisional executor decision**: use WireMock as a pinned conformance/reference
executor and preserve it as a possible opt-in adapter; do not make it the
default MVP dependency. Continue the implementation design toward a narrow
native executor contract. The concrete Python HTTP foundation remains
undecided and requires source-level Impact Handshake before mutation.

## Sensitivity

- Raising `F`'s expressiveness score does not address its isolation, provenance,
  or over-simulation risk. Code-backed service remains an escape driver.
- Raising `C`'s authoring score does not remove engine-semantic and distribution
  costs. It can still win the executor bake-off under a strict profile.
- If callback injection is removed, `A` becomes more attractive, but that would
  contradict repeated application evidence rather than simplify the same
  requirement.
- If future Consumers demonstrably need many independent protocols, `H` may
  become justified. Its normalized-driver platform cost is premature today.
- If the Agent authoring bake-off shows the closed descriptor is harder to
  revise than ordinary code, the remedy is a better authoring surface or a
  deliberate code-backed driver—not a universal embedded script language.

## Result

The renewed recommendation is materially different from the prior one:

- do not start with a code-backed fake service;
- do not design a service DSL;
- start with strict, managed boundary interactions using separate examples,
  matchers, semantic generators, captures, and independent event injection;
- preserve Consumer code only as an explicit narrow materializer or separate
  escape driver;
- choose native versus WireMock execution by a bounded conformance bake-off.
