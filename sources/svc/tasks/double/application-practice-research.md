# Application-Layer Double Practice Research

Status: renewed evidence base, observed 2026-08-09. This document deliberately
does not use the two Anana fake servers to derive requirements. They may later
be used as adversarial examples, but not as proof that SVC should reproduce
their architecture or semantics.

## Research Question

What do mature application teams actually need from external-system doubles to
verify product behavior, especially when the real system performs unsafe or
costly writes or sends asynchronous callbacks?

The question is intentionally narrower than “how can we implement a fake
service?” A fake service can contain almost arbitrary behavior. The product
question is which behavior provides trustworthy evidence about the Consumer,
and which behavior merely creates a second, fictional backend.

## Method and Evidence Rules

The sample prioritizes primary sources from:

1. empirical software-engineering research;
2. mature application repositories with substantial real integration code;
3. application-platform test doubles maintained by the platform owner;
4. provider-owned testing tools that clearly state their fidelity limits.

General-purpose mocking tools are not treated as evidence of application need.
They are implementation candidates only after the need is established.

A behavior is admitted as a requirement only when it supports a specific test
claim and has a traceable source. Absence from this finite sample is not proof
that a behavior is never useful. Conversely, one elaborate fake is not proof
that its capabilities should become a product-wide DSL.

## Research Evidence

### 1. Empirical and conceptual evidence

| Source | Direct observation | Implication for SVC |
| --- | --- | --- |
| [Spadini et al., Empirical Software Engineering](https://research.tudelft.nl/en/publications/mock-objects-for-testing-java-systems-why-and-how-developers-use-/) | The study manually analyzed more than 2,000 mock usages in three open-source systems and one industrial system, then surveyed more than 100 practitioners. Developers frequently mocked hard-to-test dependencies, generally avoided mocking controlled domain concepts and rules, and reported compatibility maintenance and coupling as major problems. | A double should replace an uncontrollable boundary, not reimplement Consumer-owned domain logic. Every extra semantic rule creates drift and coupling cost. |
| [Are Coding Agents Generating Over-Mocked Tests?](https://arxiv.org/abs/2602.00409) | Across 1.2 million 2025 commits in 2,168 repositories, coding-agent commits added mocks more often than non-agent commits: 36% versus 26%. The authors warn that mocks may be easier to generate while being less effective at validating real interactions. This is a recent MSR 2026 paper, so its causal conclusions should be treated cautiously. | Agent authorability alone is an unsafe objective. SVC must make unsupported semantics visible and difficult to mistake for verification evidence. |
| [Fowler, Contract Test](https://martinfowler.com/bliki/ContractTest.html) | Fast tests can continue to use a double while a separate contract suite periodically checks the external test instance on the external provider's change rhythm, not necessarily every code change. | Fast deterministic doubles and provider-drift detection are separate lanes. SVC must not claim that one substitutes for the other. |
| [Google, Fake Your Way to Better Tests](https://testing.googleblog.com/2013/06/testing-on-toilet-fake-your-way-to.html) | The guidance favors owner-maintained fakes, testing the fake and real implementation against the same public interface, faking at the lowest practical layer, and retaining a small real-integration suite. | A Consumer-owned wrapper or boundary fixture is preferable to a broad provider clone. A conformance path matters more than a large behavior language. |
| [AST 2026 mapping study](https://conf.researchr.org/details/ast-2026/ast-2026-papers/10/Exploring-Mocking-Techniques-for-Managing-External-Dependencies-in-Service-Based-Syst) | The mapping study organizes external-dependency techniques around contracts, specifications, execution simulation, generation, instrumentation, and related methods, while identifying fidelity, maintenance, scalability, and limited industrial validation as continuing problems. | No mature universal semantics can be assumed. Candidate runtimes need evidence from application use, not feature-list completeness. |

### 2. Mature application practice

| Application | Boundary under test | What the tests actually do | What they do not require |
| --- | --- | --- | --- |
| [pretix](https://github.com/pretix/pretix) ticketing and payments | Stripe and PayPal checkout, payment confirmation, refund, and webhook paths | [Checkout tests](https://github.com/pretix/pretix/blob/master/src/tests/plugins/stripe/test_checkout.py) drive the real Django application and replace only a narrow SDK call with a local function that asserts essential request values and returns a small provider-shaped object. [Webhook tests](https://github.com/pretix/pretix/blob/master/src/tests/plugins/stripe/test_webhook.py) POST provider-shaped event JSON to the real application endpoint, stub a follow-up provider lookup where needed, and assert pretix order/payment/refund state. The [payment-plugin quality checklist](https://docs.pretix.eu/dev/development/api/quality.html) requires signed webhooks or treating their content as untrusted and refetching provider data. | A persistent Stripe or PayPal world model; automatic reproduction of the provider's payment lifecycle; an all-purpose service DSL. |
| [Zulip](https://zulip.readthedocs.io/en/9.4/testing/philosophy.html) | Outgoing HTTP integrations and incoming provider webhooks | The main suites forbid outgoing Internet traffic and use fixed fixtures for external responses. The [incoming-webhook guide](https://zulip.readthedocs.io/en/12.0/webhooks/incoming-webhooks-overview.html) tells contributors to capture real provider payloads, store one fixture per meaningful event type, POST them to the real webhook handler, and assert the resulting Zulip message. Live forwarding is a separate debugging aid. | One fake provider that initiates all callbacks; shared fake-provider state between outgoing and incoming paths. |
| [GOV.UK Pay](https://docs.payments.service.gov.uk/testing_govuk_pay/) | Payment API clients and full payment journeys | Consumer teams are told to use a local stub such as WireMock for automated integration tests that run on code changes, while sandbox modes are used for test payments and automated smoke tests. The replacement mock runtime [pay-run-amock](https://github.com/alphagov/pay-run-amock) is tested both for Mountebank equivalence and against Cypress suites in three consuming applications. | Using the sandbox for every change; assuming a compatible runtime is correct without consumer-application acceptance tests. |
| [GitLab CustomersDot / Fulfillment](https://handbook.gitlab.com/handbook/engineering/development/fulfillment/) | Zuora and other billing services | Regular integration specs replay VCR interactions, while a separate scheduled pipeline disables replay and calls the Zuora sandbox to detect API drift. | Treating recorded responses as permanently authoritative; making provider access part of every fast CI run. |
| [Home Assistant](https://github.com/home-assistant/core/blob/dev/tests/conftest.py) | Hundreds of application integrations with external devices and cloud APIs | Core fixtures block or detect unexpected socket use and provide protocol-specific HTTP mock fixtures. Test teardown checks that registered routes, tasks, threads, and global state do not leak between tests. | A universal provider simulator shared by all integrations; permissive fall-through to the network. |

The common topology is “real application plus the smallest controlled boundary
substitution,” not “real application plus a miniature copy of the provider.”
pretix and Zulip are especially important for callback requirements: inbound
events are commonly tested as direct stimuli into the Consumer, independently
of outbound response substitution.

### 3. Provider- and platform-owned reference doubles

These examples reveal useful design limits, but do not by themselves prove that
SVC should implement the same mechanism.

| Reference | Deliberate scope | Lesson |
| --- | --- | --- |
| [stripe-mock](https://github.com/stripe/stripe-mock) | Uses Stripe's OpenAPI description to keep URLs, parameters, resources, and fields current. Stripe explicitly says responses are hard-coded, may be unrealistic, and the tool does not reproduce Stripe behavior. It is for SDK sanity checks, with test mode or other techniques required for sophisticated integration tests. | OpenAPI supports protocol/schema fidelity, not business fidelity. A generated responder must publish that limitation as part of its contract. |
| [Twilio test credentials](https://www.twilio.com/docs/iam/test-credentials) | Avoid charges and account mutations. Documented “magic” inputs yield a finite set of deterministic success/error outcomes. Unsupported resources fail, and some production effects such as status callbacks are explicitly absent. | High-value control can be a small vocabulary of Consumer-visible outcomes. Completeness is neither necessary nor implied. |
| [Kill Bill payment test plugin](https://github.com/killbill/killbill-payment-test-plugin) | Exposes narrow per-request or global controls such as success status, error, pending, exception, nil, delay, and amount, with an explicit clear action. | Test control should correspond to branches the Consumer must handle; a general payment-gateway lifecycle is not required. |
| [Saleor Dummy Payment App](https://github.com/saleor/apps/tree/main/apps/dummy-payment-app) | A bare-bones app for Saleor's Transactions API. Request data directly selects documented transaction outcomes such as charge success or authorization failure; payment webhooks are part of the application contract. | Scenario choice can be explicit test input, and its vocabulary can stay at the Consumer-visible contract rather than provider internals. |
| [Dropbox webhook helper](https://dropbox.tech/developers/dropbox_hook-py-a-tool-for-testing-your-webhooks) and [Probot webhook simulation](https://probot.github.io/docs/simulating-webhooks/) | Small tools inject webhook verification or captured event payloads into a local application. Probot explicitly notes that its receiver does not include headers. | Event injection is an independent role. Payload-only injection is insufficient when headers or signatures are part of the product claim, so claimed transport fidelity must be explicit. |

## High-Confidence Cross-Case Findings

### F1. Start from the test claim, not the provider surface

The recurring unit of design is a Consumer-visible claim:

- the application sent an essential request;
- the application rendered or persisted the correct result;
- the application handled a documented provider outcome;
- the application processed an inbound event correctly;
- the application remained safe under a timeout or duplicate delivery.

An operation or state is justified only if it is needed to arrange or observe
one of those claims.

### F2. Fidelity is a vector, not a scalar

A double can be faithful in one dimension and intentionally weak in another:

- transport: method, path, headers, encoding, connection behavior;
- schema: accepted fields, types, and response shape;
- selected semantics: documented outcome and error meaning;
- temporal behavior: duplicate, retry, delay, ordering, and timeout;
- provenance: evidence that behavior matches a real provider version.

`stripe-mock` is a concrete example of strong protocol/schema maintenance with
an explicit refusal to claim behavioral realism. Calling any double “high
fidelity” without naming dimensions is therefore misleading.

### F3. Callbacks are inputs to the Consumer before they are provider behavior

Mature application tests often inject a captured event directly into the real
Consumer endpoint. They do not need the outbound stub to own an internal state
transition and autonomously schedule the callback. Correlation, signatures,
duplicates, and ordering are conditional capabilities, driven by the exact
product claim.

### F4. The product oracle stays outside the double

The strongest examples assert application state, rendered output, or a public
application API. Interaction assertions at the external boundary are useful
for the Consumer-owned contract—method, endpoint, and essential values—but
overspecifying every field and call order couples the test to implementation.

### F5. Strict failure semantics are part of correctness

GOV.UK Pay's `pay-run-amock` documents two concrete distortion risks inherited
from a general mock runtime:

- a case-insensitive query matcher hides request bugs;
- response arrays can alternate under an unexpected background retry;
- an unmatched endpoint returning an empty `200` hides missing setup.

The safe default is exact/declared matching, explicit sequence semantics, and a
failing unmatched request. Convenience behavior is not neutral.

### F6. Fast deterministic verification and real-provider drift detection are
different jobs

Zulip blocks Internet access in the normal suite. GOV.UK Pay separates local
stubs from sandbox smoke tests. GitLab separates VCR-backed specs from a
scheduled sandbox lane. Fowler gives the same rationale. SVC may coordinate
both eventually, but must not let a deterministic double imply current provider
compatibility.

### F7. Code is common, but broad service simulation is not

Application teams frequently write small functions in their native test
language and store provider data in fixtures. Provider/platform doubles expose
small outcome controls. The sample does not supply evidence for a universal,
stateful provider-service DSL. It also does not justify prohibiting code when a
specific protocol transformation or cryptographic materializer genuinely needs
it.

## Distortion Risks to Treat as Product Requirements

| Risk | Failure produced | Required countermeasure |
| --- | --- | --- |
| Invented provider rule | A green test proves behavior the provider never had | Every semantic rule has provenance and a fidelity claim |
| Excessive provider state | Consumer tests become coupled to a second backend | State is opt-in and justified by a named test claim |
| Permissive matching/defaults | Malformed or unexpected Consumer traffic passes | Fail closed on unmatched requests and undeclared egress |
| Implicit response sequencing | Retries or concurrency silently select a different outcome | Sequence/ordering is explicit, observable, and isolated |
| Double-owned product oracle | The system grading itself reports a false pass | Product assertions stay in the Consumer test |
| Stale fixture or spec | Deterministic CI diverges from the provider | Record origin/version/date and provide a separate refresh/probe lane |
| Coupled callback orchestration | Tests reproduce a fake provider lifecycle instead of Consumer event handling | Make event injection independent; add correlation only when claimed |
| Hidden global state | Parallel or retried tests influence each other | Per-test identity, reset/ephemeral lifecycle, and leak detection |
| Agent-generated semantic bulk | Plausible-looking DSL becomes unreviewed business fiction | Prefer explicit fixtures/outcomes; flag unsupported semantics mechanically |

## Evidence Limits

- This is a purposive sample, not a statistical survey of all application
  testing.
- Most mature applications use in-process seams because they are cheap. SVC's
  black-box goal requires translating the same boundary discipline to an
  over-wire harness; it does not justify reproducing in-process implementation
  details.
- Provider-owned tools can have privileged knowledge and maintenance resources
  that SVC cannot assume.
- The 2026 coding-agent study is recent and observational. It motivates a
  guardrail, not a numeric product target.
- Complex temporal or cryptographic cases remain possible. They are conditional
  requirements and need explicit provenance, not universal runtime features.

## Derived Work

- Requirements and anti-requirements:
  [`double-requirements-v2.md`](double-requirements-v2.md)
- DSL/runtime alternatives and decision table:
  [`runtime-decision-v2.md`](runtime-decision-v2.md)
