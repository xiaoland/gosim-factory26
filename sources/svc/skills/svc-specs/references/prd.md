# Product Requirement Document

Product requirement document owns what the product is for, what users or external systems can observe, which rules and scope apply, and why those commitments exist. It does not own implementation topology, internal sequencing, wire details, or local code contracts.

Keep one concise Product owner containing, as applicable:

- purpose and pressure
- claims and how stakeholders judge them
- capabilities and user or external workflows
- rules, non-goals, and scope
- stable business language

Derive technical contracts and work from owned Product claims; do not infer Product truth from current implementation, fixtures, or passing tests. Use Product Design in `svc-workflow` to shape a proposed Product solution and update this owner only when that solution is accepted as durable truth.

Create further depth only when a Product capability has enough stable content and an independent consumer. Do not use Product depth to duplicate cross-unit wire contracts or runtime implementation; route those to Product TDD or Deployment.

Start with `docs/prd/index.md`; use the [PRD template](../assets/prd-index.template.md).
