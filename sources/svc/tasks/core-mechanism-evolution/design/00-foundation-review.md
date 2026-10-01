# Foundation Review — Outcome and Inquiry Model

- **State**: accepted
- **Posture**: Explore
- **Authority**: Sir owns whether this model faithfully represents the intended
  product and task. The Lead Agent owns the correction analysis and must not
  request a downstream design ruling until this foundation is reviewed.
- **Inputs**: Sir's original three purposes, the clarified one-to-five-Human
  target, and Sir's correction of the first `D0.1` framing.
- **Exit condition**: Met through `D-008` on 2026-07-29. Reopen only through its
  recorded trigger.

## Why the First D0 Framing Failed

The first framing committed three category errors:

| User-stated outcome | Incorrect substitution | What was lost |
| --- | --- | --- |
| Agent obtains better results on long, ambiguous, numerous and interleaved work | “Long-task recoverability” | Framing, reasoning, decomposition, adaptive planning, dependency handling, integration, correction, completion quality, and total trajectory effectiveness |
| Human-Agent collaboration becomes more efficient, with fine control and product/technical taste alignment | “Human authority continuity” | Information bandwidth, decision quality, shared understanding, taste transfer, calibrated autonomy, interruption cost, correction cost, and rework |
| A very small team can drive a large complex system | “System changes remain coherent” | The economic outcome: lowering the total cost and risk of understanding, changing, verifying, operating, and evolving the system over time |

The resulting `H/E/C` choice then asked Sir to select among Agent-created
abstractions instead of first reviewing whether the task had been understood.
That choice is withdrawn.

## Corrected Outcome Interpretation

### `O-INTERACTION` — Human-Agent collaboration effectiveness

The desired outcome is not simply fewer messages or uninterrupted Human
authority. It is a better result per unit of Human attention and interaction:

- the Human can express intent, product taste, technical taste, constraints,
  uncertainty, and acceptance standards with adequate resolution
- the Agent asks or interrupts when Human judgment has high value, not whenever
  any uncertainty exists
- the Agent supplies enough context, alternatives, evidence, consequences, and
  recommendation for efficient Human review and decision
- low-risk work proceeds autonomously inside understood bounds
- misunderstanding, repeated explanation, avoidable correction, and rework
  decline without hiding material decisions from the Human

“Fine control” and “taste alignment” are parts of the efficiency model, not
synonyms for permission.

### `O-TASK` — Agent effectiveness on long work

The desired outcome is that the Agent more often produces a good terminal result
on work whose scope is initially incomplete, whose contents are numerous and
interdependent, and whose facts and plan evolve over a long trajectory.

Potential contributing abilities include:

- discovering and reframing the real problem
- constructing and revising a useful system/task model
- decomposing without losing cross-cutting relationships
- managing attention, context, state, dependencies, and several work lanes
- selecting tools, methods, and delegation deliberately
- testing assumptions and alternatives
- integrating partial results and repairing failed approaches
- preserving relevant knowledge across interruption, compaction, handoff, and
  changed evidence
- recognizing when the result is actually complete and adequately verified

Recoverability is one contributing ability. It is not the outcome definition.

### `O-SYSTEM` — Low-cost development and evolution of large software

The desired outcome is that one Human most commonly—and approximately three to
five Humans ordinarily—plus Coding Agents can develop and evolve a large,
complex, long-lived system at sustainable total change cost.

Relevant cost sources may include:

- locating intent, ownership, contracts, and implementation
- reconstructing system behavior and dependency impact
- making and integrating cross-cutting changes
- preserving product and technical quality while requirements evolve
- verification, migration, rollout, rollback, recovery, and operational
  consequences of change
- coordination and handoff among Humans and Agents
- architectural erosion, duplicated truth, obsolete decisions, and future
  change amplification

Coherence is a necessary quality and cost factor. It is not the complete
outcome.

## Relationship Among the Outcomes

The three outcomes may be different temporal and structural scales of one
software-development loop:

- one interaction episode exposes collaboration efficiency
- one extended trajectory exposes Agent long-task effectiveness
- repeated trajectories across topology and lifecycle expose large-system
  change economics

This relationship explains why the goals share mechanisms without assuming
that one is merely a means to another. No hierarchy is proposed for Human
approval at this point.

## Candidate Unifying Question

> How can SVC increase the complexity, duration, and system scale of software
> work that a very small Human-plus-Agent team can complete well, while reducing
> Human coordination, avoidable rework, and lifecycle change cost?

This is a working inquiry, not a product promise. “Complete well,” “cost,” and
the interaction among the three scales require concrete Consumer episodes and
later evaluation work.

## Corrected Discussion Method

The proposed map in [`design.md`](../design.md) uses a feedback loop:

```text
Consumer episode and desired result
  -> current path and competing failure causes
  -> required observable capabilities
  -> status quo plus candidate mechanism combinations
  -> vertical scenario rehearsal
  -> output quality, total cost, learning, and lifecycle evidence
  -> revise the affected outcome, cause, capability, or candidate
  -> only then project supported semantics into SVC and its DX
```

Task packets, sub-agents, reasoning modes, system models, templates, CLI,
validation, and telemetry enter as candidate mechanisms or projections. They no
longer define the top-level discussion categories in advance.

## Review Requested from Sir

Sir confirmed this foundation on 2026-07-29. The reviewed scope was:

1. the interpretation of each of `O-INTERACTION`, `O-TASK`, and `O-SYSTEM`
2. the claim that they are distinct observation scales of a coupled development
   loop, without an assumed hierarchy
3. the non-linear inquiry topology and vertical-slice method
4. the candidate unifying question

No architecture or implementation decision was included. The inquiry proceeds
through representative Consumer episodes rather than prewritten product
slogans.
