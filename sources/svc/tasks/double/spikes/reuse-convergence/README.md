# Double Reuse and Convergence Spike

## Question

Can the implemented BSL v0 preserve its admitted behavior and all existing
test cases while replacing hand-maintained structural invariants with existing
library mechanisms, and while replacing the flat double-test layout with a
responsibility-shaped topology?

## Boundaries

- Do not mutate `src/`, `svc_cli/`, dependency declarations, locks, workflows,
  release notes, or generated projections.
- Treat the current 78 double-related pytest cases as characterization evidence,
  not deletion candidates.
- Prototype only the uncertain seams: Pydantic discriminated authoring/IR
  models, CEL binding availability, local immutable JSON Schema references, and
  pytest layout/fixture ownership.
- Distinguish library conformance from SVC product policy. Workspace containment,
  no remote retrieval, snapshot identity, claim scope, and fidelity non-claims
  remain SVC-owned even when a library performs parsing or resolution.
- Do not judge success by line count alone. Compare invalid-state
  representability, duplicate semantic authorities, diagnostics, dependency
  cost, Agent authoring consequences, and preservation of observable behavior.

## Required Evidence

1. A responsibility and duplication map for the current compiler and tests.
2. Runnable probes demonstrating which invalid IR states Pydantic unions remove.
3. A runnable CEL probe that either eliminates source scanning or proves why the
   selected CEL binding cannot expose the required checked representation.
4. A runnable local recursive-reference probe using one `referencing.Registry`
   authority without network retrieval.
5. A proposed test package tree with a collection-derived exact
   old-case-to-new-owner map showing that no current case is lost or assigned
   twice. Actual collection after moving files remains an implementation gate;
   the spike must not claim that unperformed source mutation as evidence.
6. A decision table with keep/replace/defer outcomes and an ordered migration
   plan suitable for a later Impact Handshake.

## Stop Conditions

Stop and report rather than broadening the spike if preserving stable CLI/error
contracts requires a public BSL grammar change, if the selected CEL package
cannot mechanically support the admitted restriction, if a proposed resolver
can retrieve remotely, or if test reorganization changes product behavior.

## Result

The completed evidence and decision table are in [`result.md`](result.md).
The separately authorized first implementation slice has now also completed
the test-topology gate while preserving the pre-migration 78-case identity
digest; its scope is recorded in
[`../../reuse-convergence-impact-handshake.md`](../../reuse-convergence-impact-handshake.md).
