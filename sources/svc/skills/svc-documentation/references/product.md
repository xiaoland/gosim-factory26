# Product Purpose and Behavior

Product documentation owns what the product is for and why its commitments matter.
It describes the users or external systems served, the problem and pressure, observable capabilities and workflows, product rules, scope, and stable business language.
Without this basis, current implementation choices can silently become requirements and technical success can be mistaken for user value.
Keep a minimal product basis even during first development; use the supplied requirements as the source and identify the project's interpretation rather than creating a competing requirement.

## Build a Usable Basis

Start with the intended beneficiary, the problem, and how success would be recognized.
Follow the meaningful user or external-system path, including its initial conditions, actions, visible results, important failures, and explicit limits.
State rules and exceptions together so a consumer need not infer precedence from unrelated examples.
Define a business term when its meaning changes a decision; reuse the term across design, implementation, and acceptance.

For example, “a draft can be resumed” may mean the same user can return after signing in again and see the last saved content.
That promise needs its scope and reason: whether drafts expire, whether another device is included, and what unsaved edits mean.
A storage mechanism is a proposed means; a successful database write alone does not establish the promised return journey.
Derive technical work and acceptance judgments from the promise and its conditions.

Preserve why a rule was chosen and which assumption would reopen it.
An unresolved interpretation remains visible as an assumption or open question until the responsible decision is made.
Do not infer the product rule from existing code, seed data, screenshots, or passing checks.
An observation can challenge the rule or its interpretation, but cannot silently replace it.

## Maintain the Current Meaning

When a product decision changes, update the existing product owner and explain the replaced behavior, new behavior, conditions, and affected consumers.
Carry that change to relevant technical decisions, work plans, and acceptance expectations.
Distinguish an agreed promise from a proposal and from what is actually available to users.
Retain useful historical rationale without leaving superseded instructions in the current path.

Create separate depth for a capability only when its stable content, readers, or update cadence justify it.
Keep wire details and component authority in [technical design](technical-design.md), internal sequencing in [internal design](internal-and-local.md), and packaging or recovery in [operation](operations.md).
These subjects may support the product promise without belonging in its definition.
Use the [product template](../assets/templates/product.template.md) only when a short existing requirement or README does not already provide the needed basis.
