# Managed External Boundaries

Use this [Product Truth](index.md) projection when a Consumer needs a
claim-scoped substitute for an external HTTP boundary. It owns the observable
Double workflow, safety promise, and non-goals; module wire rules and runtime
authority remain with Product TDD and Deployment.

`svc double` is experimental. It lets a Consumer verify one named product claim
against its real application when an external HTTP system is unavailable,
unsafe, costly, or unsuitable for deterministic writes. A versioned
boundary-scenario module can declare strict outbound request matching and
deterministic responses, plus named inbound events that a test emits explicitly.
Examples, matchers, captures, derived values, closed semantic generators,
managed assets, and provenance remain separate roles so protocol-shaped data
does not invent provider business truth.

The observable workflow is `svc double validate|start|emit|observe|stop`. Each
start creates a fresh isolated loopback responder and reports its replay facts,
fidelity boundary, and explicit non-claims. Observe returns bounded interaction
evidence, not a test verdict. The Consumer test drives the real product and is
the sole product oracle; SVC neither runs that test nor adds a combined
`double check` result. Events never follow automatically from a response.

The deterministic lane never proxies, falls through, or retrieves remote
contracts/assets. SVC constrains its responder, built-in materialization, and
event target delivery, but does not launch or sandbox the Consumer. Consumer
egress is therefore not enforced. A declared external materializer is also
Consumer-owned arbitrary code: SVC bounds its envelope and execution resources
without claiming its egress, determinism, immutability, or provider fidelity.
OpenAPI may verify one selected local static 3.1 operation's schema mechanics;
it does not define provider behavior or prove provider currentness.

An Agent must not introduce or reshape a double merely to make a test pass. If
an invented fixture or event, a permissive matcher, materializer state or
nondeterminism, or missing independent provider evidence could reduce test
credibility or validity, the Agent reports that concern and obtains the user's
confirmation before proceeding.
