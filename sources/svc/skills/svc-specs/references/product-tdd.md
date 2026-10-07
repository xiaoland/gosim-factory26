# Product TDD

Product technical design document is an optional owner for cross-unit technical contracts. Admit a contract only when two or more logical units must agree on authority, topology, wire shape, lifecycle, sequencing, compatibility, or failure behavior to interoperate safely, and code or schemas alone cannot preserve the expensive meaning clearly enough.

It consumes accepted Product and Technical claims and returns the minimum shared contract each participating unit must implement and verify. It does not own Product rationale, one unit's private design, or runtime operations.

Prefer executable schemas and tests for field-level enforcement.

If the [multi-repo extension](multi-repo.md) is active, keep shared Product TDD in the Hub authority and consume it read-only from Spokes. Do not copy the contract into independently drifting owners.

Start with `docs/product-tdd/index.md`; use the [Product TDD template](../assets/product-tdd-index.template.md) when a cross-unit contract is admitted.
