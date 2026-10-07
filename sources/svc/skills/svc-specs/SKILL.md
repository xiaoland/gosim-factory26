---
name: svc-specs
description: "Use when locating the authoritative requirements or updating product commitments, technical contracts, operational knowledge, or Agent instructions. Find and maintain their existing canonical owners; decide whether source or configuration already establishes a fact before creating another document. Keep provisional task decisions separate from durable project knowledge."
metadata: {"version": "16.0.0"}
---

# Specifications

Recover the intended benefit behind Human wording. Product intent, personal preference, permission, material trade-offs, and acceptance remain Human authority; factual, causal, technical, feasibility, and proposed-solution claims remain challengeable from evidence, logic, stakeholder consequences, and short- and long-horizon return on investment.

Proceed autonomously with safe exploration, review, and design. Before durable mutation, establish the authorized desired effect, semantic owner, affected consumers and invariants, and proportionate verification. Ask the Human only for consequential missing information, authority, preference, trade-off, or acceptance that cannot be inferred safely. Resolve independent work first and present the smallest decision-ready issue. This Skill grants no write, delegation, external-effect, or acceptance authority.

The surrounding Task keeps every unmet obligation after this Skill returns. For its non-trivial Task, recover the existing Task Packet or create the smallest `packet.md` at the project's authorized task location. Keep the objective, authorization and constraints, current facts, next action, and completion verification sufficient to resume. A Skill invocation or Child Assignment does not create a new Task or competing Packet; the Child returns its state delta to the Task owner. Preserve project-owned truth separately, preferring source, configuration, schema, tests, assertions, or automation for facts they can enforce directly.

Other SVC Skills can supply additional guidance when available: discover them by name through the host's available-Skill interface and load only the relevant guidance. They are not prerequisites for this Skill. If one is unavailable, continue with the guidance here and qualified project mechanisms; report an actual missing capability or authority instead of assuming access or relaxing an obligation.

A Unit is the smallest responsibility that can be delivered or deployed independently, such as an application, service, or library. The nearest local `AGENTS.md` may preserve a repeated fragile seam in one physical subtree.

## Find the Existing Authority

First identify the durable claim and its consumer, then search the project's existing owners. Prefer source, configuration, schema, test, assertion, or automation when it can enforce the fact directly. Use the registry below to choose only the reference whose admission rule matches the claim; do not generate a document family by default.

Update the canonical owner before repairing its projections. Preserve provisional findings and active work in the Task Packet in `svc-task-packet` rather than promoting them to durable truth. Return the updated owner and relevant consistency checks, or the reason no new durable document is warranted. Stop when the changed claim and its dependent projections agree; missing Product intent or mutation authority goes back to the Human under the authority boundaries above.

Use the [root instruction asset](assets/AGENTS.root.template.md) when establishing a Consumer project's Agent entry. Choose other assets only through the applicable reference; their presence does not admit a new owner.

| Truth | Durable owner | Admission |
| --------------------------------------------------------------- | -------------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| Mechanically enforceable implementation fact | source, configuration, schema, test, assertion, or automation | prefer whenever it can prevent drift directly |
| Product promise, behavior, rule, scope, or business language | [Product Requirement Document](references/prd.md) | keep a minimal Product owner; split only for a distinct consumer or cadence |
| Cross-unit authority, topology, or compatibility contract | [Product TDD](references/product-tdd.md) | another unit must rely on it to interoperate safely |
| Expensive internal invariant of one logical unit | [Unit TDD](references/unit-tdd.md) | it survives refactors and is not cheaply enforced or recovered |
| Repeated fragile seam in a physical subtree | nearest local `AGENTS.md` | nearby instructions and checks are likely to prevent recurrence |
| Runtime, packaging, observability, migration, or recovery truth | [Deployment](references/deployment.md) | operational behavior is non-trivial |
| Repository development, contribution, or release workflow | root `AGENTS.md`, `CONTRIBUTING.md`, executable configuration, or release source | keep the instruction at the entry used by its consumer |

Before adding a durable surface, require stable useful content, a real consumer, expensive rediscovery or risk, one canonical owner, and no cheaper executable authority. Keep evidence, provisional decisions, active Plans, and bounded artifacts in the Task Packet in `svc-task-packet`.

Product Requirement Document owns what and why. Product TDD owns admitted cross-unit technical contracts. Unit TDD owns admitted unit-internal design. Deployment owns operational reality. These are semantic projections, not a required document ladder; one change updates only the owners whose claims actually changed.


## Extensions

Extensions are optional, they add pressure-specific coordination contracts without replacing the core owner model or the authority boundaries above. Use one only when its admission rule is satisfied; mono-repository work and ordinary semantic ownership remain the default.

- [Alignment](references/alignment.md) addresses repeated costly coordination drift in references, boundaries, operations, state, or evidence after normal owners and stable anchors are already insufficient.
- [Multi-repo](references/multi-repo.md) addresses one product spanning repositories when shared truth otherwise drifts and freshness can be enforced mechanically.

An extension does not own Product/Technical/runtime truth, evidence, Working Methods, or acceptance. Do not create an extension for a one-off Task or to hide an unresolved core owner.
