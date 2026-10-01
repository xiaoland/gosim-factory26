# Working Note — Verification, Acceptance, and Test Routing

- **State**: provisional-note
- **Sources**: Sir's verification, acceptance, test, and AI-generated-test
  gleanings; two ChatGPT conversations; one bounded local Codex-task audit;
  software-test-oracle, assurance-case, assume-guarantee, and LLM test-generation
  research; bounded Lead synthesis
- **Use**: Explain what tests contribute, where a claim should be observed, how
  verification can be reused across modules, and why an Agent can produce a
  large green test suite with little acceptance value

## Evidence Boundary

The two conversations are useful theory generators, not authorities:

- [Engineering experience compilation](https://chatgpt.com/share/6a6f4d15-ca94-83ea-8b66-dca3aa895da5)
- [Testing strategy and continuous change assurance](https://chatgpt.com/share/6a6f4d2d-5db4-83ea-9e2c-49d7d5818523)

Relevant research supports narrower claims:

- [The Oracle Problem in Software Testing](https://discovery.ucl.ac.uk/id/eprint/1471263/)
  establishes that deciding whether observed behavior is correct is itself a
  central, costly problem. Specifications, contracts, metamorphic relations,
  models, and Human knowledge are possible oracle sources; none is universally
  sufficient.
- [Toward a Theory of Assurance Case Confidence](https://insights.sei.cmu.edu/documents/1222/2012_005_001_28161.pdf)
  distinguishes evidence from the argument that explains why the evidence
  supports a claim, and treats reasons for doubt as material.
- [Assume-guarantee testing](https://doi.org/10.1145/1118537.1123060)
  supports compositional verification only under explicit component
  assumptions and system-level composition rules. Local correctness does not
  automatically imply system correctness.
- Recent LLM test-generation work shows that coverage can coexist with weak
  fault detection, and that mutation feedback can improve generated tests:
  [MUTGEN](https://arxiv.org/abs/2506.02954). A later replication also reports
  that coverage and mutation signals depend strongly on whether the code given
  to the LLM is already trustworthy:
  [Zhao, Zhou, and Cohen](https://arxiv.org/abs/2607.22880).

The local Codex task is one episode, not prevalence evidence. It provides
concrete examples of synthetic fixtures, a test helper that reused production
bundle constructors, an acceptance harness that copied part of the production
schema, six pytest cases whose real owner was a static policy check, and larger
product protocols whose tests shrank only after the protocols were simplified.
It supports a causal warning, not the universal statement that AI-written tests
have low value.

## Core Correction

Tests do not guarantee that software meets product and technical expectations.
They are instruments that produce bounded evidence. Acceptance is the decision
made from that evidence, its scope, remaining uncertainty, and the consequence
of being wrong.

The smallest useful reasoning chain is:

```text
product or technical claim
  -> semantic owner and relevant context
  -> observation surface and discriminating oracle
  -> evidence plus unverified boundary
  -> accept, reject, continue observing, or escalate
```

This is a reasoning aid, not a required packet schema or an assurance-case
artifact. Routine work should normally express it through existing product
truth, code, types, tests, commands, and a concise result report.

Three questions do most of the work:

1. **What exactly must be true?** Product behavior, technical contract,
   invariant, quality boundary, or Human taste must not be inferred solely from
   the current implementation.
2. **Where does that claim become observably true or false?** Choose the stable
   surface that directly owns or manifests the claimed property, not simply the
   outermost or easiest surface.
3. **What is the cheapest credible mechanism that would discriminate a wrong
   result?** Prefer an existing construction rule, compiler, type, schema,
   linter, canonical validator, focused experiment, real boundary, or Human
   judgment over a new test or verifier.

Risk does not define correctness. Positive claims and invariants define the
acceptable region; failure models decide which possible counterexamples deserve
scarce verification effort.

## Authoritative Observation Is Claim-Relative

“Test product expectations on the product observation surface” contains a
strong principle but is not an absolute rule. The suitable surface is the one
that can authoritatively and discriminatingly observe the particular claim.

- User-visible behavior belongs at a stable user journey or public contract.
- A third-party side effect may belong at the provider or an authoritative
  ledger.
- Data persistence may require a restart followed by a public read.
- A migration invariant may be most directly observed in canonical domain data
  or the database.
- A database uniqueness guarantee may be owned by the constraint plus a
  concurrent experiment.
- Product and technical taste may require Human review because no mechanical
  oracle captures the desired distinction.

Authority identifies provenance, not measurement quality. The surface may
still be stale, noisy, partial, confounded, or unable to distinguish competing
causes.

For example, “click subscribe, then send a notification, and observe provider
success” is stronger than inspecting a database cell, but it can still pass if
the account already had quota or if a different path grants it. A more
discriminating experiment controls the precondition:

```text
send before subscription -> rejected for insufficient quota
click subscribe
send after subscription -> accepted by the provider
```

The before/after relation supplies information that the final success alone
does not.

## Verification Can Be Modular Without Creating a New Module System

Sir's `PuButton` example exposes a valuable form of complexity compression:
verify a reusable component's loading contract once, then verify at the
consumer that the intended component and relevant inputs are connected.

This works only while the component's assumptions and guarantee match the use:

```text
qualified component contract
  + consumer satisfies its assumptions and uses the intended seam
  + composition does not add a new interaction failure
  -> reuse component evidence; verify only the connection and residual risk
```

Asserting only that “Subscribe is a `PuButton`” is sufficient when the loading
behavior cannot be bypassed or materially altered at that use site. If props,
slots, styling, asynchronous ownership, or surrounding state can violate the
contract, the composition needs its own evidence. A small product-journey check
may still be useful because modules that are correct separately can fail when
combined.

SVC does not need an `AssuranceModule` artifact by default. Existing deep code
modules, types, schemas, public contracts, focused tests, and canonical owner
documents can already carry the reusable guarantee. A separate qualification
record earns its cost only for expensive, high-risk, or widely reused
mechanisms whose assumptions or requalification triggers are otherwise easy to
lose.

## Route Verification to the Earliest Sufficient Owner

The useful rule is not a fixed test pyramid or a mandatory linear ladder. It is
to avoid duplicating the same proof while combining genuinely different
evidence where one mechanism is insufficient.

```text
make the wrong state unconstructable when possible
  -> use compiler, types, schemas, constraints, or static analysis
  -> use a focused runtime/property/component check for remaining behavior
  -> exercise an integration or external boundary when the claim lives there
  -> use Human judgment or controlled production observation for distinctions
     unavailable below
```

If a compiler, type checker, linter, or schema reliably owns a property and is
enforced, business tests should not repeat it. If SVC owns a custom checker,
test the checker's decision boundary once and apply it mechanically; do not
restate the checked rule in every consumer test.

Likewise, an acceptance harness should consume the installed product through a
stable boundary. If it reimplements the production parser, archive protocol,
or validator, it becomes another product that requires its own compatibility
tests and can disagree with the authority it was meant to check.

The first reference adds a related work-system insight: a costly verification
episode can expose an avoidable pattern in how an Agent verifies work, but it
should produce a candidate behavioral intervention rather than automatically
create a test or rule. The intervention challenge is roughly:

```text
remove the unnecessary source of difficulty
  -> make the wrong state unconstructable
  -> detect the remaining fault mechanically
  -> automate a repeated correct action
  -> guide the Agent only when judgment remains
  -> retain memory only when weaker forms are all that pay back
```

One green or painful episode does not prove long-term value. Before promoting a
new test, lint rule, script, Skill, or instruction, compare it with deleting the
underlying product promise, simplifying the architecture, or using an existing
owner. The local task was especially instructive here: reorganizing tests
improved their local shape, but much larger savings appeared only after
unnecessary evidence and release protocols were reduced or replaced.

## Why Agent-Written Tests Can Produce False Confidence

The distinctive failure is not “AI writes bad syntax.” It is endogenous proof:

```text
same implementation context
  -> Agent infers an intended behavior from the implementation
  -> Agent invents a fixture and oracle consistent with that inference
  -> implementation and test agree
  -> green result is mistaken for independent acceptance evidence
```

A synthetic fixture is not inherently bad. It is bad when it constructs a
world in which the intended failure cannot occur, omits the real distribution
or boundary, or shares the same implementation mechanism as the code it is
meant to challenge. The local task showed this risk but also contained useful
negative cases and an installed-wheel check, so “the tests can only pass” was
not proven.

Useful ways to add independent information include:

- derive the claim and oracle from the product or technical owner before
  accepting the implementation's behavior
- replay a historical defect or representative real input
- inject a targeted wrong implementation and confirm the evidence changes
- use metamorphic, differential, property, compiler, type, schema, or external
  provider evidence
- separate the implementation context from a bounded verifier when that
  independence repays its briefing and review cost
- ask the Human only for product or taste distinctions that machinery cannot
  decide

Mutation testing is one possible sensitivity probe, not a universal gate. A
test can kill artificial mutants yet still protect the wrong product claim.

Another failure is requirement inflation. An Agent may add atomicity,
portability, hostile-process, recovery, privacy, or compatibility guarantees
because defensive engineering is locally legible, then generate tests that
turn those invented guarantees into permanent commitments. The test suite is
not merely measuring the product at that point; it is silently expanding the
product. Product scope must be challenged before optimizing the test shape.

## Binding to the Three Outcomes

- **`O-INTERACTION`**: the Human reviews consequential claims, examples,
  counterexamples, taste, and acceptance boundaries instead of generated test
  volume. The Agent reports what was observed, what the evidence can establish,
  and what remains a judgment. Extra assurance vocabulary or forms would undo
  this gain.
- **`O-TASK`**: claim-relative evidence reduces the chance that a long task
  terminates on locally green but irrelevant checks. Modular verification
  avoids repeatedly reconstructing already established behavior, while changed
  scope or assumptions identify which evidence must be revisited. It does not
  replace Lead integration or final product acceptance.
- **`O-SYSTEM`**: executable constraints and qualified deep modules compress
  the amount a tiny team must re-understand and reverify. Tests attached to
  stable semantic boundaries survive internal refactoring; simplifying an
  unnecessary product protocol removes its verification burden entirely. The
  counter-risk is assurance debt: copied validators, stale oracles, traceability
  machinery, and unnecessary guarantees can make every later change costlier.

For `S-SIMPLE`, a familiar low-risk edit should normally need no new claim
card, assurance module, risk register, acceptance envelope, or verification
plan. Existing owner truth and its normal check are enough.

## Current Boundary

Do not adopt `Continuous Change Assurance` as a new SVC subsystem, a universal
claim-argument-evidence schema, an acceptance envelope, a failure-model file,
or a fixed test-routing ladder.

Retain the smaller provisional claims:

- tests are bounded evidence, not acceptance or proof by themselves
- choose an observation surface relative to the exact claim and control enough
  context for the result to discriminate competing explanations
- reuse verified module guarantees only while their assumptions and
  composition remain valid
- prefer the earliest existing mechanism that can faithfully establish the
  property; do not duplicate it in pytest or a copied verifier
- treat same-context Agent-generated fixture, oracle, implementation, and
  acceptance as correlated evidence and seek independent information in
  proportion to risk
- challenge unnecessary product and technical guarantees before investing in
  tests that would make them permanent
