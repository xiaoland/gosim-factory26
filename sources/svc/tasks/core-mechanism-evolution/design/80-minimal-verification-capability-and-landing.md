# Minimal Verification Capability and Landing

- **State**: accepted at capability-model depth in `D-089`
- **Consumer**: `VF × P1`
- **Inputs**: `D-042..D-043`, `D-074`, `D-078`, verification/test gleanings,
  and the VF consumption audit

## Capability

Verification qualifies a consequential claim with evidence from an observation
that can distinguish the claim from a material alternative. It does not make
the claim, design the product by reverse inference, or authorize acceptance and
effects.

The minimum semantic chain is:

```text
owned Product/Technical claim
  -> relevant observation surface and discriminating oracle/relation
  -> evidence with scope, trusted base, and residual
  -> consumer-owned disposition: continue / reject / rework / accept / waive
```

The observation surface is claim-relative. Product behavior should normally be
observed through the product-visible consequence; an internal cell, fixture, or
implementation detail is sufficient only when the claim is actually owned at
that level or a qualified module contract makes the projection valid.

## Owner Seams

- **Product/Technical Design** owns the expected claims.
- **Test Design** selects consequential scenarios, observations, oracles,
  comparisons, invariants, Human criteria, and required independence. With no
  owned claim, it returns a specification gap or exploratory probe—not a
  normative test.
- **Implementation** builds automation, probes, fixtures, and observability.
- **Verification** executes/interprets the applicable verifier and returns
  qualification plus residual.
- **The consuming authority/effect gate** decides whether that qualification
  is sufficient for acceptance, waiver, integration, publication, or other
  consequence.

These concerns may interleave inside one Slice. They are semantic ownership
seams, not phases, documents, roles, or mandatory handoffs.

## Minimal Proof Economy

Choose the smallest credible mechanism for the loss at stake; there is no fixed
test pyramid or universal ladder.

- Prefer compiler, type/schema/constraint checks, or existing qualified module
  guarantees when they discriminate the claim.
- Add focused runtime, metamorphic/differential, integration, external readback,
  shadow/fuzz, statistical, or Human observation only when the claim and
  residual require them.
- Determinism is useful but not validity. The trusted base includes claim/
  owner, input integrity and representativeness, oracle/relation, environment/
  instrumentation, verdict interpretation, residual horizon, and effect gate.
- Treat AI-generated fixtures, implementation, oracle, and tests from one
  correlated context as candidate evidence. Strengthen only where worthwhile
  with owner-derived claims, real/historical inputs, independent mechanisms,
  mutations/relations, or external readback. Do not write a test when static
  enforcement or an existing guarantee already owns the failure mode.

Module proof reuse means: rely on a qualified deep module guarantee, check the
consumer connection and its assumptions, and retest composition only where the
composition creates new behavior. Changed assumptions, owner claims,
environment, oracle, or consumer connection invalidate the relevant reuse and
trigger requalification.

## Distributed State and Rough Landing

- Local proof remains with its Slice/Cell/realization surface.
- A Task-root `verification.md` remains optional and pressure-created. Use it
  only when claims/evidence/residuals span multiple returns or Cells, require a
  shared qualification horizon, or must be reopened/requalified together. It
  synthesizes; it is not a final Verification phase.
- Add one compact `src/sections/verification.md` owner for the chain, owner
  seams, proof economy, independence/trusted-base guidance, modular reuse, and
  acceptance boundary. The target Working Protocol only links the capability
  and preserves its authority/effect invariant.
- Do not add a Reviewer role, assurance schema, mandatory acceptance file,
  fixed test matrix, global evidence ledger, or CLI verification engine.

## Unknowns and Reopen Conditions

The exact non-deterministic/Human/statistical qualification vocabulary and
cross-Cell evidence merge form need real tasks. Reopen when local evidence is
repeatedly lost, module guarantees conceal composition failures, Human waiver
or external-state dispositions remain ambiguous, or the root synthesis costs
more than the coordination failure it prevents.
