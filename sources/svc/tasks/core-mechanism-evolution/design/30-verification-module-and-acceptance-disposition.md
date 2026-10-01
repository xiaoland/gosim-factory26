# Working Note — Verification Module and Acceptance Disposition

- **State**: accepted task-packet design input (`D-042`)
- **Sources**: `D-013..D-041`; `V-004`, `V-009`, `V-015`,
  `V-037..V-043`, `V-070..V-077`; Sir's verification/test gleanings; current
  Working Protocol and Implementation Taste; twelve historical/current
  `verification*.md` and `acceptance*.md` task artifacts
- **Use**: Determine which verification information deserves a semantic module,
  where acceptance authority lives, and how tests, certificates, Human judgment,
  and external observations return into Task control without another Plan or
  assurance bureaucracy

## The Boundary to Resolve

Verification and acceptance are often written as one phrase, but they perform
different operations:

```text
expected claim + candidate/baseline
              ↓
observation and oracle produce bounded evidence
              ↓
verification synthesis says what the evidence supports
              ↓
an authorized consumer decides what may happen next
```

- **Verification** is epistemic: what claim is supported, refuted, blocked,
  stale, or still unknown, at which observation horizon.
- **Acceptance** is a control disposition: which consumer accepts which
  residual risk for which purpose, and what integration, progression, rework,
  waiver, or external effect follows.

A green test is neither operation by itself. It is one observation produced by
one mechanism. An Agent report, local check, installed-product observation,
external readback, and Human taste judgment also have different evidence
horizons.

## Field Evidence

The current corpus has 12 verification/acceptance artifacts ranging from 24 to
222 lines. Their useful content and ownership are inconsistent:

| Shape | Useful content | Structural signal |
| --- | --- | --- |
| small `verification.md` result | implemented surface, checks run, exact result, deliberate unverified boundary | bounded evidence can remain one concise return |
| verification matrix | stable claim IDs, required proofs, proof owner, executed result | several Slices need one integrated claim/evidence owner |
| 178–189 line verification dossier | planned claim matrix, private study, local/static result, cross-platform and live evidence | planning and accumulated evidence legitimately cross several Slices and horizons, but execution routing remains elsewhere |
| real-project `acceptance.md` | preconditions, isolation, product-observation sequence, cleanup, pass criteria | it is an expanded `VR` work contract/protocol before execution, not yet an acceptance disposition |
| installed-wheel `acceptance.md` | exact candidate identity, host matrix, result, staging exception | it is a verification run record and evidence artifact |
| first-tag `v11.0.1-acceptance.md` | immutable identity, timeline, hashes, external readback, idempotence | it is an attempt-specific external evidence certificate consumed by release completion |
| `acceptance-environments.md` | host facts, preconditions, ownership and safety boundaries | it is a verification supporting dossier whose freshness matters, not acceptance authority |

The word `acceptance` currently names protocol, environment, evidence run, and
final result. That does not establish a coherent peer semantic module. By
contrast, a cross-Slice verification claim/evidence map does have a stable job
not owned by the Plan, Design, implementation Slice, raw tests, or Human
decision record.

## Alternatives

| Alternative | Benefit | Cost/failure |
| --- | --- | --- |
| no verification module; keep everything in each `VR` Slice | cheapest for bounded Tasks; strongest local ownership | repeated claims, proof horizons, and evidence drift when several Slices/Cells consume them |
| one `verification.md` containing plans, evidence, and acceptance | one place to inspect | collapses epistemic status, authority, and Task progression; easily becomes a second Plan |
| separate `verification.md` and `acceptance.md` modules | visually clear nouns | creates a mostly empty peer module for routine work and preserves the current ambiguity of “acceptance” |
| **pressure-created Verification module + acceptance dispositions at consuming control owners** | one integrated evidence owner; authority remains where consequences are controlled | requires clear routing between claim ledger, `VR` Slice, Plan/barrier, Decision, and Human projection |

The fourth alternative has the lowest current total cost.

## Owner Decomposition

| Information or action | Owner |
| --- | --- |
| product promise, technical contract, invariant, or taste expectation | its normal durable owner, or task-local Design/Decision while provisional |
| order and status of verification work | applicable Task/Cell Plan and its `VR` Slice |
| integrated current mapping from material claims to proof obligations and evidence | pressure-created `verification.md` semantic module |
| executable checking mechanism | compiler, type, schema, constraint, test, linter, runtime check, provider, or Human observation surface |
| expanded protocol, environment dossier, command output, run record, or certificate | verification supporting artifact or external evidence store |
| candidate acceptance/rejection for one Assignment | parent Slice/Lead integration gate |
| Cell/Phase progression or reopening | applicable Plan/Phase barrier owner |
| material Human waiver, product/taste acceptance, or durable task-local disposition | `decisions.md`, with the consequential current request/result projected in `packet.md` |
| Task terminal state | Task owner represented in `packet.md`; evidence is referenced, not copied |
| live migration/release/rollout state | its named domain Track/Cell and external system authority |

Acceptance therefore has no single content lifecycle independent of its
consumer and consequence. It is a **typed disposition at an effect gate**, not
a default task-packet module.

## The Verification Module Contract

`verification.md` is activated when verification state must survive or be
shared across more than one local return. Its entry owns an integrated current
synthesis, not a command log. Expand in proportion to risk:

- **subject and baseline**: exact candidate, source/config identity,
  environment, representative inputs, and assumptions to which results apply
- **material claim set**: positive product/technical/taste expectations derived
  from an authority other than the candidate implementation
- **proof obligation**: observation surface, discriminating oracle or relation,
  required horizon, and relevant independence
- **current result**: supported/refuted/inconclusive/blocked/stale/unknown with
  evidence reference and explicit unverified boundary
- **composition**: reused qualified guarantees, assumptions at the current use
  site, connection proof, and residual interaction risk
- **invalidation/requalification**: which candidate, dependency, environment,
  source, assumption, or verifier change makes the result unsafe to reuse
- **requested disposition or next discriminator**: who consumes the synthesis,
  what consequence is proposed, or what smallest observation is still needed

These are semantic responsibilities, not a mandatory seven-section form. A
compact table often serves better:

```text
claim | authority | surface/oracle | horizon | result/evidence | residual/invalidation
```

The module may contain planned obligations and observed results because both
belong to one claim/evidence lifecycle. It must not contain the work sequence;
the `VR` Slice owns that.

## Progressive Activation and File Shape

### Keep verification local

For one bounded claim with a familiar check, the Plan/Slice records the expected
return and observed result inline. No `verification.md` is created.

An expanded one-Slice protocol may live beside its Plan owner:

```text
cells/<track>-<phase>.md
cells/<track>-<phase>/
  04-VR.md
```

It remains a Slice-owned artifact when no other consumer needs an independently
maintained evidence synthesis.

### Activate `verification.md`

Create the stable module entry early when one or more of these pressures are
material:

- several changed claims, semantic owners, or proof horizons must stay aligned
- several Slices/Cells produce or consume the same verification state
- verification is designed before implementation and accumulated afterward
- delegated candidates require certificates and a common verifier/gate
- expensive Human, external, cross-platform, privacy-sensitive, or destructive
  observations must be planned and reused carefully
- partial/conditional results, residual unknowns, or selective requalification
  affect later work
- a proof dependency or qualified module guarantee prevents repeated testing

Only then grow same-stem depth:

```text
verification.md
verification/
  <semantic-concern-or-run-artifact>.md
```

Split by an independently useful concern, claim family, environment contract,
or attempt certificate—not by tool invocation or an arbitrary number of green
checks. Large raw logs, private inputs, screenshots, and telemetry remain in an
appropriate evidence store; the module keeps bounded references and synthesis.

## Claim-Relative Observation and Test Routing

The suitable observation surface is the earliest existing surface that can
faithfully distinguish the exact claim, not automatically the database, unit
test, UI, or outermost end-to-end path.

```text
make invalid state unconstructable
  -> compiler/type/schema/constraint/static rule
  -> focused property/component/runtime check for remaining behavior
  -> integration, installed product, or external boundary where the claim lives
  -> controlled production observation or Human judgment when machinery cannot decide
```

Tests provide evidence; they do not author the product promise. Do not repeat a
property already reliably enforced by a lower-cost owner. Reuse a module's
qualified guarantee only when the consumer satisfies its assumptions and the
composition does not introduce a new failure; verify the connection and
residual risk instead of replaying all internal tests.

For Agent-written tests, assess evidence correlation:

```text
same context invents implementation + fixture + oracle + acceptance
  -> agreement may contain little independent information
```

Add independence in proportion to false-accept loss: owner-derived claims,
historical or representative real inputs, mutation/sensitivity probes,
metamorphic or differential relations, compiler/type/schema checks, external
readback, a bounded independent verifier, or Human judgment. Independence is
not free and is never added merely because another Agent is available.

## Acceptance Disposition Contract

When evidence changes what work may proceed, the consuming owner records a
small disposition containing only what prevents ambiguity:

- claim/candidate and declared verification horizon
- evidence synthesis being consumed
- accepting/rejecting authority and intended purpose
- material residual unknown or consciously accepted risk
- consequence: integrate, advance barrier, rework, waive, observe longer,
  escalate, or perform a separately authorized external effect
- invalidation/reopen condition when later consumers might otherwise treat the
  disposition as timeless

Routine mechanical success can update its Slice/Plan without a Decision entry.
A consequential Human acceptance, waiver, or scope interpretation belongs in
`decisions.md`. An external system becoming published or deployed is observed
state owned by that system/Track, not proof that Human accepted every product
quality claim.

This preserves a critical asymmetry: verification can fail to settle a claim,
while an authorized Human may still accept bounded residual risk; conversely,
all declared checks may pass while the Human rejects the product or taste.

## Inquiry, Implementation, and Verification Returns

- If the expected behavior or oracle is uncertain, return to `IQ`/`DS`; do not
  rewrite the expected result until the candidate passes.
- If the claim is clear but the candidate fails, return to `IM` with the
  counterexample and bounded evidence.
- If the mechanism cannot discriminate the claim, remain in `VR` or redesign
  the proof; green output is inconclusive.
- If new evidence invalidates an already exited proposition on the same
  baseline/horizon, apply the accepted Phase reopen contract.
- If a verification episode reveals a recurring Agent-work bottleneck, the
  later `RT` return may propose a work-system intervention; verification does
  not automatically create a linter, script, Skill, or rule.

## Human Projection

`packet.md` should expose only the consequential current verification brief:

- which outcome claim/candidate is under judgment
- the strongest observed horizon and material contradictory/unknown evidence
- what decision or effect is requested, from whom
- what residual risk changes the decision

It should not project command inventories, test counts, every claim ID, or a
generic percentage/status bar. “224 tests passed” is not a Human-ready brief
unless the decision actually depends on what those tests establish.

## Failure Modes and Falsifiers

- `verification.md` becomes a second Plan, test checklist, or append-only log.
- tests derive requirements from current implementation and silently expand
  product scope.
- a fixture or verifier copies the production mechanism it is supposed to
  challenge.
- local proof is reported as product, external, or Human acceptance.
- every implementation change invalidates every proof because claims and
  assumptions were not modularized.
- stale environment or candidate evidence remains presented as current.
- a Human is asked to review raw output instead of a claim/evidence/residual
  synthesis.
- an `acceptance.md` file claims authority merely because it is named
  acceptance.
- certificate production and verification cost exceed direct Lead review.

Reopen the module-negative acceptance conclusion if real Tasks repeatedly need
one independently maintained, cross-consumer acceptance state with its own
authority, lifecycle, invalidation, and return that cannot be owned by the
Plan/barrier, Decision module, Verification synthesis, domain Track, or external
system without costly duplication.

## Lead Recommendation

1. Admit `verification.md` as a pressure-created semantic module with optional
   same-stem depth; keep bounded verification inline or Slice-owned.
2. Let the module own integrated claim-to-evidence state, horizons, residuals,
   and requalification—not work sequence or raw logs.
3. Do not admit a default `acceptance.md` module. Treat acceptance as an
   authority-bearing disposition at the consuming integration/effect gate.
4. Record routine dispositions in the Plan/barrier, consequential Human
   dispositions in `decisions.md`, and external delivery state in its named
   Track/system owner.
5. Keep tests subordinate to claim-relative observation, composition, and
   evidence independence; prefer the cheapest credible existing verifier.
