# Working Note — Working Mode and Transformation Routing

- **State**: provisional-note
- **Sources**: Sir's Executor and deterministic-transformation gleanings,
  Patrick Dubroy's Five Coding Hats, official GritQL documentation, and bounded
  Lead synthesis
- **Use**: Explain when work belongs to deterministic machinery, an
  LLM-assisted transformation, or an Executor-shaped development loop without
  creating a fixed tool router or role catalog

## Source Anchors and Evidence Boundary

- [Five Coding Hats](https://dubroy.com/blog/five-coding-hats/)
- [GritQL overview](https://docs.grit.io/)
- [GritQL tutorial](https://docs.grit.io/tutorials/gritql)
- [Testing GritQL](https://docs.grit.io/guides/testing)

Five Coding Hats is a practitioner's reflective model, not an experiment or an
Agent orchestration specification. Its five labels are neither exhaustive nor
proven to improve software outcomes.

Grit's official documentation establishes a concrete capability boundary:
GritQL provides declarative structural matching, conditions, and rewrites over
syntax trees, with reusable patterns and before/after test cases including
multi-file samples. Grit's broader product also describes optional AI-powered
transformations. Classify the action by its execution semantics, not by the
brand: a GritQL rewrite can be a deterministic transform, while an AI migration
is LLM-assisted.

Deterministic execution does not prove semantic completeness. A structural rule
can consistently miss reflection, generated code, configuration, external
contracts, or a product distinction absent from the syntax. It can also apply
the wrong rule consistently at enormous scale.

## What Five Coding Hats Adds

Dubroy's main claim is that code and process quality are contextual. The five
hats illustrate different optimization policies:

| Hat | Primary optimization | Deliberately different treatment of cost or quality |
| --- | --- | --- |
| Captain | Safety and controlled production change | Small reversible commits, tests, review, procedure |
| Scrappy | Fast concrete learning or minimum viable result | Minimal ceremony and only the proof needed now |
| MacGyver | Feasibility or result discovery | Disposable, quick experiments before clean implementation |
| Chef | Presentation and internal elegance | Time-bounded refinement beyond functional adequacy |
| Teacher | Communication and understanding | Clarity may outrank robustness or efficiency in example code |

The useful SVC insight is not to adopt these five names. It is that a Human
cannot predict or judge Agent behavior from `Explore` or `Execute` alone.
Working mode also needs an understandable quality-risk policy: what is being
optimized, what debt is acceptable, what proof is required, whether the result
is disposable or durable, and what causes a mode change.

Keep these concepts distinct:

- **working posture** describes the kind of cognitive move: Explore, Solidify,
  Execute, or Diagnose
- **operating policy** describes the current quality, risk, speed, durability,
  and evidence trade-off
- **role** provides a reusable specialized work contract
- **assignment** binds one objective, scope, authority, input, and return

One Executor could perform a disposable feasibility probe and later a careful
production implementation. Those should not silently share the same quality
and verification expectations merely because the role name is unchanged.

## Route by Uncertainty, Not Edit Volume

The number of files is a poor routing signal. Hundreds of edits may be one
known transformation; one line may require unresolved product judgment.

A stronger first question is:

> What part of the desired change remains uncertain, and which execution
> surface can express the known part most deterministically without hiding a
> material semantic distinction?

Use three provisional action shapes:

### Deterministic transformation

Use when the match, mapping, exclusions, and intended invariant are sufficiently
known and can be expressed as a compiler-assisted rename, codemod, GritQL or
other structural rewrite, generator, formatter, or script.

The valuable artifacts are the rule, positive and negative examples, bounded
match set, resulting diff, and appropriate compiler/test/runtime checks. The
review burden shifts from reading every independently generated edit toward
checking the rule, its coverage boundary, exceptions, and effects.

This normally does not justify a writer sub-agent. The Lead or Executor can
invoke the deterministic mechanism directly.

### LLM-assisted transformation

Use when a mostly regular migration still requires local semantic inference,
rule synthesis, or exception classification, while scope and acceptance remain
bounded.

The LLM should help infer a candidate mapping, author or refine the executable
rule, identify residual cases, or repair explicit exceptions. Apply the regular
core deterministically when possible. Enclose the work in an Executor-shaped
loop:

```text
representative examples and invariants
  -> candidate rule or mapping
  -> bounded application
  -> inspect matches, misses, and diff
  -> compiler, tests, or other evidence
  -> refine, handle explicit exceptions, stop, or escalate
```

The LLM earns its cost by resolving uncertainty and using feedback, not by
typing the same causal edit repeatedly.

### Bounded Executor development loop

Use when each observation can change the next hypothesis or action: runtime
behavior, performance, UI, data interaction, incomplete system understanding,
or Human product and technical taste.

The stable boundary is an observable seam and a credible local oracle, not a
known rewrite. The Executor owns repeated inspect, hypothesis, minimal change,
replay, comparison, and escalation. It may still use deterministic transforms
inside the loop when one iteration exposes regular scale.

If the work lacks a bounded seam, feedback path, or stop condition, calling it
Executor does not make the delegation safe or valuable.

## Consequence for Sub-Agent Admission

Repetitive volume is a machine-automation opportunity, not an Agent-team
topology. Agent count should grow with independent uncertainties or specialized
judgment that can be isolated behind compact interfaces, not with the number of
files or edit sites.

This adds a direct-tool baseline to the delegation cost model:

```text
Lead applies existing deterministic tool
versus
Lead/Executor designs and validates a new deterministic rule
versus
LLM-assisted Executor loop
versus
delegated specialized Executor plus integration
```

A delegated Executor must save enough focused reasoning, feedback history, or
specialized method to repay briefing, waiting, state collision, validation, and
integration. It need not be a child Agent; the Lead can execute a small loop
locally when context isolation brings no benefit.

The durable-document integrator remains a meaningful role because it resolves
semantic ownership and conflicting claims. A generic writer that merely edits
many files does not have the same deep method or return advantage.

## Binding to the Three Outcomes

This routing contributes differently to each original purpose:

- **`O-INTERACTION`**: Human attention moves from reviewing repetitive output
  toward declaring examples, invariants, exceptions, quality-risk policy, and
  taste judgments. Visible working mode lets the Human know how to help and
  what proof to expect.
- **`O-TASK`**: deterministic scale reduces inconsistent edits and context
  consumption; an Executor loop preserves local feedback and adapts when
  evidence changes. Neither guarantees a good terminal result without Lead
  framing, integration, and honest proof boundaries.
- **`O-SYSTEM`**: executable and tested transformations can make large
  migrations repeatable and auditable, while production-oriented operating
  policies can bound rollout and recovery risk. Semantic gaps, external
  consumers, and future maintenance still determine total change cost.

The simple counter-pressure is equally important: a familiar local edit should
not require a role dispatch, custom codemod, mode taxonomy, or new evidence
ceremony.

## Current Boundary

The current synthesis does not authorize Five Coding Hats as SVC vocabulary, a
new operating-policy schema, Grit adoption, deterministic-first as an absolute
rule, an Executor Agent for every feedback loop, or a fixed three-route
workflow.

Retain the smaller claims:

- make the current quality-risk policy legible when it materially changes how
  Human and Agent should work
- prefer the most deterministic action surface that faithfully expresses the
  known transformation
- spend LLM context on bounded uncertainty and feedback, not reproducible
  repetition
- keep Human and Lead authority over intent, architecture, taste, integration,
  and acceptance regardless of the execution mechanism
