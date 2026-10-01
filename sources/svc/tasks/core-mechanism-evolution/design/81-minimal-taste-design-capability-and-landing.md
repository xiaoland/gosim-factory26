# Minimal Taste and Design Capability and Landing

- **State**: accepted at capability-model depth in `D-090`
- **Consumer**: `TD × P1`
- **Inputs**: `D-068..D-071`, `D-078`, `D-081..D-082`, ECCA and implementation-
  taste gleanings, and the TD consumption audit

## Capability

Taste is compressed consequence knowledge that helps Design choose among
multiple plausible solutions. SVC may be deliberately opinionated for Sir's
development experience, while still distinguishing four sources of guidance:

- project Product/Technical truth, owned by its canonical project surface;
- Sir's product, aesthetic, workflow, and implementation preference, which is
  a legitimate personal default;
- general design judgment or heuristic, which is rebuttable and pressure-
  dependent;
- Task-local hypothesis or exploration, which has no durable authority yet.

This distinction need not become a metadata schema. Apply an aligned default
directly. A local, reversible departure with no material consequence can stay
bounded. Compress one decision-ready question when a departure changes product
experience, explicit preference, authority/boundaries, acceptance, or long-
term cost. Facts, causes, and proposed solutions remain challengeable regardless
of speaker.

## Progressive Design Depth

Design remains the foundational method that integrates typed forces into one
coherent proposed solution and challenges representative consequences. Taste
is method-owned progressive depth, retrieved from the recurring design pressure
rather than a global pile of maxims.

```text
owned claims + current reality + stakeholders/resources
  -> Product / Technical / Test Design projection
  -> local recurring design pressure
  -> relevant method and taste, with counter-pressure
  -> representative consequence/challenge
  -> coherent solution + material residual
```

Product, Technical, and Test Design are independent projections of one solution,
not phases or required documents. Test Design remains claim-dependent. General
methods such as first-principles reasoning, ROI/lifecycle analysis, topology and
sequence modeling, deep modules, precise naming, removal forces, and semantic
locality are loaded only when they change the current design judgment.

A useful taste entry should make retrievable, in ordinary prose rather than a
fixed schema:

- the quality or consequence it tries to improve;
- the recurring pressure/use case;
- the preferred default and causal reason;
- cost, counter-pressure, and conditions that weaken it;
- an observable projection, example, or counterexample when useful.

Sir's preference does not need external evidence to be legitimate for his own
experience. Evidence calibrates applicability and cost. One correction should
not silently become a universal law; repeated use, rejection, or system
consequence can refine or retire a default.

## Domain-specific Carriers

- Product/UI/UX judgment uses user consequences, references, rendered
  alternatives, interaction replay, prototype, and Human perception where
  appropriate.
- Architecture/System judgment uses authority and dependency topology,
  lifecycle, change scenarios, propagation obligations, deployment/migration,
  and representative failure consequences.
- Implementation judgment uses code/data/API shapes, naming, contracts, tests,
  assertions, observability, and future-change cost.

ECCA is not adopted as a branded universal architecture. Its useful motives—
semantic locality, clear ownership/contracts, vertical coherence, explicit
boundary propagation, and local instructions—remain available as rebuttable
defaults. Ordinary change should stay near its semantic owner; intrinsically
cross-boundary change must expose propagation and composition obligations.
This does not require bounded-context directories, ports/adapters, ADRs, or a
modular monolith everywhere.

## Rough Landing

- Add one compact Design/taste router under `src/sections/` that explains the
  authority distinction, use-case/pressure retrieval, Product/Technical/Test
  projections, and routes to deeper domain guidance.
- Retain `src/sections/implementation-taste.md` as the existing Technical/
  Implementation depth and revise its trigger/links rather than duplicating it.
- Do not initially create mandatory UI/UX and Architecture files. Add one only
  when recurring guidance with distinct consumers and enough content proves
  retrieval value; until then the router can hold a few high-leverage examples.
- The target Working Protocol links to Design and its progressive depth; it
  does not own or repeat the catalog. No CLI or Task Packet schema is needed.

## Unknowns and Reopen Conditions

Real tasks must show that guidance is found at the right moment and improves a
solution enough to repay reading, routing, reconciliation, and maintenance.
Reopen when guidance becomes an inert shelf, personal preference is mistaken
for project/universal truth, Product/Technical/Test projections fragment one
solution, or a domain repeatedly needs a deeper owner.
