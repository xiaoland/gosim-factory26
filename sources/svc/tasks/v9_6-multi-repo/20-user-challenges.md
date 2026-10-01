# User Challenges To Resolve

## Challenge 1: Spoke Interruption Without Losing Code Pain

Problem statement:

- An agent is usually writing code in a Spoke when it discovers that a PRD rule or shared contract is incomplete.
- A naive "stop and go edit the Hub now" rule protects source-first mutation, but it risks losing the exact code-local pain that exposed the gap.

Why this matters:

- The shared-doc change may become abstract and forget the concrete failure seam that justified it.
- The agent may resume local coding with a weaker memory of the exact invariant it was about to violate.

Current direction to explore:

- Add a spoke-side capture step before any Hub mutation.
- That capture stays in the local task container, not in durable shared docs yet.
- The capture should preserve:
  - the exact code path or local seam
  - the missing shared rule or ambiguity
  - the local consequence if the rule remains unclear
  - the verification pressure that the shared rule must satisfy when the agent returns

Open question:

- Is this capture a required pre-step inside the shared-doc mutation protocol, or only a recommended pattern when execution is interrupted mid-slice?

## Challenge 2: Product TDD vs Unit TDD Becomes Physically Sharp

Problem statement:

- In one repo, the line between `20-product-tdd` and `30-unit-tdd` can sometimes remain fuzzy because the docs live near each other.
- In multi-repo, the physical split forces a decision. Agents may still write cross-service payload contracts into spoke-local `30-unit-tdd`, or move one service's internal table naming into Hub `20-product-tdd`.

Why this matters:

- Misplacing truth here causes either shared-doc bloat or spoke-local drift.
- Once repo boundaries harden, wrong placement becomes harder to notice and more expensive to unwind.

Current direction to explore:

- Add explicit admission tests and examples:
  - "How two services communicate a payload" belongs in Product TDD.
  - "How one service names its internal tables" belongs in Unit TDD or local AGENTS.
- Define the deciding question as authority scope, not just number of repos touched.

Open question:

- Do we need a short comparison table in v9.6 that contrasts Product TDD and Unit TDD with multi-repo examples, or is a smaller admission checklist enough?

## Immediate Implication For v9.6

The next framework draft should not only describe Hub/Spoke topology. It must also answer:

1. how an interrupted spoke execution preserves local evidence before shared promotion
2. how agents decide whether a technical truth belongs in Hub `20-product-tdd` or spoke `30-unit-tdd`
