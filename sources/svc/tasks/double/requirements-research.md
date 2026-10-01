# Real Double Requirements Research

Status: superseded. Its evidence standard admitted the Anana implementations as
requirements sources; Sir explicitly rejected that premise. Use
[`application-practice-research.md`](application-practice-research.md) and
[`double-requirements-v2.md`](double-requirements-v2.md). No source mutation is
authorized by this historical document.

Current outputs:

- [`real-double-requirements.md`](real-double-requirements.md) derives the
  capability taxonomy from Anana and wider primary-source samples.
- [`service-boundary.md`](service-boundary.md) defines the trusted-code and
  service/SVC ownership boundary.
- [`runtime-decision.md`](runtime-decision.md) contains hard gates, weighted
  criteria, a decision matrix, sensitivity, and the current recommendation.

## Research Question

What does a real external-system double need to own so that it can verify
Consumer-observable product behavior, and what must SVC own—or deliberately
leave to Consumer code—to make that capability sustainable without becoming a
general backend platform?

The research must answer this before evaluating syntax:

```text
real verification need
  -> required double capability
  -> authority and lifecycle owner
  -> declarative / code / generated boundary
  -> runtime constraints
  -> DSL/runtime alternatives
  -> explicit decision table
```

## Evidence Standard

A proposed requirement needs at least one of:

- direct use by an Anana black-box or integration scenario;
- behavior implemented and tested in one of the two Anana fake servers;
- a repeated pattern in a mature external-system emulator, sandbox, service-
  virtualization tool, or contract-testing system;
- a concrete failure mode that affects determinism, safety, fidelity, or Agent
  authoring.

For every admitted requirement, record:

- the product behavior it makes testable;
- whether it is protocol mechanics, domain behavior, test control,
  observation, lifecycle, or governance;
- whether data alone can express it honestly;
- whether arbitrary computation, I/O, time, concurrency, or persistence is
  needed;
- which artifact is authoritative and how drift is detected;
- whether SVC implements, hosts, validates, generates, or merely orchestrates
  it.

## Workstreams

### A. Anana responsibility audit

For WeChat Pay and Caocao, inventory:

- provider routes and protocols;
- domain entities, correlations, state transitions, invariants, and derived
  values;
- authentication, signing, encryption, clocks, randomness, and identifiers;
- callbacks, retries, acknowledgement, delivery failure, and ordering;
- failure injection, including accepted-write/lost-response ambiguity;
- control and observation operations actually used by tests and local UI;
- external dependencies and fallback behavior;
- local-development versus CI lifecycle and fixture differences;
- maintenance history: what changed when Consumer product behavior changed.

### B. Wider real-double sample

Select representative systems that stress different dimensions:

- payment/webhook lifecycle;
- booking or fulfillment lifecycle;
- message/event delivery;
- object store or cloud API semantics;
- identity/OAuth or signed protocol;
- clock-driven expiration/retry;
- record/replay or proxy-based virtualization.

The goal is not a catalog. It is to test whether the Anana-derived capability
model generalizes and to discover missing dimensions.

### C. Boundary model

Compare at least these ownership shapes:

1. fully declarative SVC double;
2. declarative core plus bounded script hooks;
3. Consumer-authored service implementing an SVC double contract/SDK;
4. arbitrary Consumer command wrapped only by SVC lifecycle and observation;
5. adapter to an existing service-virtualization runtime;
6. hybrid/generated scaffold where code is explicit authority.

The boundary must address:

- what makes an artifact a `double` rather than a general backend;
- whether that distinction is semantic, operational, trust-based, or merely
  product positioning;
- script sandboxing versus trusted local code;
- network egress, filesystem, subprocess, secret, and resource policies;
- how control and observation remain stable when behavior is arbitrary code;
- whether SVC promises portability across implementation languages;
- how Agent-authored code is reviewed, validated, and debugged;
- how much runtime/distribution responsibility SVC can sustainably own.

### D. DSL/runtime decision table

No candidate can be scored until workstreams A–C produce stable criteria. The
final table must include at least:

- fidelity ceiling;
- authoring cost for Human and Agent;
- ability to reuse provider contracts;
- state/entity/callback/fault/concurrency/time support;
- deterministic control and observation;
- language/runtime portability;
- debugging quality;
- security and trust model;
- local/CI isolation;
- dependency/distribution/supply-chain cost;
- SVC implementation and long-term maintenance cost;
- migration and lock-in cost;
- risk of turning SVC into a backend framework.

Weights, score meanings, evidence confidence, hard disqualifiers, and
sensitivity to weight changes must be explicit.

## Early Evidence: Anana Invalidates a Scalar Scenario Model

The first deeper pass establishes that Caocao is not faithfully modeled by one
scenario string plus captured values. Its executable behavior includes:

- multiple entity-keyed orders and estimates;
- create idempotency by external order id;
- state-transition timestamp invariants and reversible test transitions;
- price composition, final settlement, cancellation fee, and fee confirmation;
- signed form protocols and provider-shaped error envelopes;
- callback routing derived from callback metadata, signed callback bodies,
  acknowledgement parsing, and delivery-failure reporting;
- accepted-write/lost-response behavior and provider call counts;
- phase-dependent driver/route projections, geometry, query-driven movement,
  optional real route planning, fallback geometry, and route caching.

WeChat Pay includes:

- transaction and refund entities with idempotent creation and correlation;
- RSA request verification and response signing;
- AES-GCM certificate and notification payloads;
- dynamic identifiers, nonces, timestamps, and stable development
  certificates;
- JSAPI/H5 protocol differences and a fake browser bridge;
- explicit success/failure/close actions and provider query convergence;
- synchronous notification delivery from selected actions.

These are not all required for every double. They prove that arbitrary
computation is a normal fidelity need, not automatically an exceptional escape
hatch. The open question is whether SVC should execute that computation,
provide a constrained host for it, or define a stable contract around
Consumer-owned service code.

## Remaining Validation Questions

1. What is the smallest language-neutral conformance protocol that both Anana
   services can expose without moving their domain behavior into SVC?
2. Which observations can be normalized across a declarative engine, ordinary
   service, official emulator, and real local dependency without erasing useful
   engine-specific evidence?
3. Can SVC validate provider traffic at a gateway boundary without breaking
   signing, streaming, callbacks, or non-HTTP protocols?
4. What exact startup/discovery handshake works for local development reuse and
   fresh CI instances without duplicating current `svc dev` policy?
5. Does an Agent author and revise the same bounded behavior more reliably in
   ordinary project code, a mature engine configuration, or a minimal custom
   notation? This needs a controlled bake-off, not intuition.
6. Is declared callback egress sufficient for trusted project code, or does an
   initial Consumer require enforceable container/proxy isolation?
7. Which low-complexity driver earns first-class MVP support in addition to the
   code-backed pressure-case driver, if any?
