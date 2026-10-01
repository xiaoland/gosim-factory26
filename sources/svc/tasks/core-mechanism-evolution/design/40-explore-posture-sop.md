# Lead Proposal — Explore Posture SOP

- **State**: coarse purpose preserved; six-step backbone superseded by [`design/42`](42-explore-sop-rederivation.md)
- **Consumer**: `WP × P1 / 07-DS`
- **Why first**: Explore is already canonical SVC vocabulary, directly serves
  ambiguous long work, and has the strongest reference/gleaning base
- **Decision now**: the problem, useful return, and smallest general method
- **Not decided now**: complete posture catalog, detailed search-tool matrix,
  Explorer sub-agent contract, or durable source layout

## Problem It Solves

Use Explore when a material unknown makes the next useful Task return—such as a
decision, design, change, or verification direction—unreliable. Without a
method, an Agent tends either to act on an assumption or to search broadly
without a return-relative stopping rule.

Explore should not maximize understanding. It should reduce the uncertainty
that matters to the intended useful return at proportionate cost.

## Useful Return

An Explore episode returns an evidence-backed current answer or problem model,
the material uncertainty that remains, and the next discriminator or downstream
move that can consume the result. A search transcript, file list, or large
context dump is not the return.

## Minimal SOP

### 1. Frame the inquiry

Identify the next return or decision that depends on exploration. State the
material unknown, current assumption or competing explanations when available,
and what kind of observation could change the route. Do not plan a complete
investigation when later evidence will determine the next question.

### 2. Start from the most relevant authority and neighborhood

Locate the applicable instructions, semantic owner, current task truth, and
the smallest relevant system/document/code neighborhood. Load broader context
only when the question or evidence path requires it.

### 3. Seek the next discriminating observation

Choose the question whose answer most usefully changes the current model or
separates plausible routes. Select the retrieval, structural search, dependency
inspection, execution probe, experiment, or external source that fits that
question. Bound and filter results before they enter the working context.

### 4. Test the evidence

Check provenance, scope, freshness, and whether the observation supports the
claim being made. Separate observation from inference. Look for a competing
explanation, boundary, counterexample, or an independent evidence path when a
false conclusion would be consequential. A failed search is not proof of
absence unless its coverage is credible.

### 5. Update and choose again

Integrate the observation into the current problem model. Revise assumptions,
unknowns, and the next discriminator; repeat only while another observation is
likely to change the consuming decision or return. An observed mismatch may
invoke a diagnosis-focused loop without turning diagnosis into a Task phase.

### 6. Return a synthesis

Return the current answer/model, decisive evidence and its horizon, material
unknowns or disagreements, and the recommended next move. Update the semantic
owner before changing work-control or Human projections when the finding is
consequential.

```text
return-relevant unknown
  -> smallest relevant context
  -> discriminating observation
  -> evidence challenge
  -> update model and next question
  -> sufficient synthesis, honest unknown, or escalation
```

## Stop or Switch

Stop or leave Explore when:

- the consumer can use the intended return with bounded residual uncertainty
- another observation is unlikely to change the consuming return enough to
  repay its cost
- the next discriminator requires Human-only intent/information or effect
  authority
- evidence shows that design, implementation, verification, or another SOP is
  now the useful next move
- no credible evidence path remains; return the limitation instead of filling
  it with inference

## Boundaries

- Explore is available to the Lead or any Agent; it does not imply an Explorer
  sub-agent.
- An Explorer role may later package advanced query/tool routing and context
  isolation, but it must implement rather than redefine the core Explore SOP.
- Explore is non-effectful by default, but a prototype or runtime probe still
  follows its actual mutation/external-effect authority.
- Inquiry may own the resulting evidence state in a Task Packet; Explore is the
  method used to obtain or revise it.
- Familiar fact lookup or a cheap obvious inspection should remain one direct
  move, not instantiate the full visible SOP.

## Failure Pressure

- exhaustive repository reading before naming the question
- choosing a familiar tool instead of the evidence path the query needs
- collecting matches without filtering or synthesis
- treating stale owners, snippets, search absence, or Agent statements as
  conclusive evidence
- continuing research after the intended return is already supportable
- asking the Human to approve safe investigation or transferring raw evidence
  review to the Human

## Requested Review

First review the backbone rather than wording details: should Explore be the
first posture SOP, with the job of reducing return-relevant uncertainty
through an adaptive discriminator/evidence loop and returning a compact
synthesis rather than exhaustive understanding?
