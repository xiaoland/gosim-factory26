# Lead Proposal — Working Posture as SOP

- **State**: accepted in `D-047`; refined by the stateless-tool correction in
  `D-057`
- **Consumer**: `WP × P1 / 06-DS`
- **Correction**: replaces the over-modeled proposal in [`design/38`](38-working-posture-boundary.md)
- **Decision now**: the problem Working Posture exists to solve
- **Not decided now**: exact postures, SOP contents, file layout, roles, tools,
  or any larger mode ontology

## The Problem

The universal Working Protocol can tell an Agent to orient, act safely, observe,
integrate, and replan. It cannot contain the best procedure for every recurring
kind of work without becoming a large undifferentiated instruction manual.

At the same time, leaving the method implicit makes an LLM improvise it on each
occasion. In long or complex work, that can repeatedly produce shallow inquiry,
premature design or mutation, weak diagnosis, missed feedback, and inconsistent
stopping behavior. General imperatives such as “explore carefully” do not teach
a repeatable way of exploring carefully.

## Simplest Model

> A **Working Posture** gives the Agent a reusable SOP for a recurring work
> situation.

The posture is a recognizable name and handle for a useful method; its useful
content is the SOP. It is not an active runtime mode. The minimum SOP answers:

1. when this method is useful
2. how to carry it out well
3. how to judge continuation, satisfied/bounded-incomplete return, or the value
   of using another method

```text
current work situation -> pick up an applicable Working Posture / SOP
                       -> use and combine it only while useful
                       -> return results to the owning work/semantic state
```

Posture methods may recur, interleave, and use one another because real tasks
are mixed and non-linear. This creates no posture lifecycle, transition event,
Task stage, or Task type.

## Why Keep the Name “Working Posture” At All

SVC could publish a flat catalog of triggered SOPs without a posture concept.
That is the simpler baseline and remains a valid alternative.

The term earns its place only if a small number of recurring work situations
need stable, easily recognized methods that an Agent can select and combine—
for example, inquiry, diagnosis, design, or implementation work. In that case,
“posture” is only a compact routing and collaboration handle for the SOP, not a
second independent abstraction layered above it.

If a proposed posture has no distinct useful SOP, it is only a label and should
not exist. If many narrow SOPs do not form a useful family, they can remain
directly triggered specialist SOPs without being promoted to postures.

## Consequences

- Design Working Postures by writing and comparing their SOPs, not by first
  constructing a taxonomy of cognitive modes.
- Preserve the current non-linear rule: one Task or Slice can use several
  posture methods, and one method can recur without becoming an active state.
- Keep the universal Working Protocol small; load posture SOPs progressively
  when their guidance is useful.
- Human predictability is a secondary benefit: when useful, describing the
  current method lets Sir understand what the Agent will do and what information
  may help; it does not require posture status reporting.
- Later Sub-agent roles may specialize in a posture/SOP, but a posture does not
  imply delegation.
- Return-scope vocabulary, role/tool selection, quality policy, and persistent
  status need not be introduced to explain the basic purpose.
- Task/Plan, semantic owners, effects, and Human decisions may have state; the
  posture method itself does not. Universal mandatory rules must remain in the
  universal protocol or applicable authority/evidence owner.

## Cost Boundary

Working Posture fails to justify itself when the SOP is obvious from the
universal protocol, when selecting the posture costs more than directly doing
the work, when the named method does not improve behavior, or when the catalog
becomes a lifecycle/taxonomy that Agents must continually announce.

## Review Disposition

Sir accepted the posture-as-SOP purpose in `D-047` and later corrected its use
model in `D-057`: the posture is a stateless tool/method, not work ceremony with
activation or exit. [`design/49`](49-working-posture-as-tool-not-lifecycle.md)
owns the integrated correction.
