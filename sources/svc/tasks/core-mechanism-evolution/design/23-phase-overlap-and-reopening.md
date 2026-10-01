# Working Note — Phase Overlap and Reopening

- **State**: accepted task-local direction through `D-033`; later execution
  evidence may reopen the bounded overlap/invalidation distinctions
- **Sources**: `D-028..D-032`; `V-055..V-060`; Workbench Iteration 01
  Phase 06/07/08 and Surface Camera receiver/publication repair-audit chains
- **Use**: Keep Phase a truthful shared barrier without turning it into a global
  lifecycle, a nested state machine, or a reason to serialize independent work

## The Ambiguity

Two apparently simple expressions currently hide different events:

- “Phase scopes overlap” may mean only that two declared scope sets share a
  Track, or that the Track is actually serving two active barriers at once.
- “Phase reopened” may mean an attempt failed before exit, exit evidence was
  later invalidated, or a new obligation appeared after a valid exit.

These distinctions change work ownership, history, downstream impact, and what
the Human needs to review. One generic `reopened` state cannot carry them.

## Field Derivation

### Workbench Phase 06 — Failed Exit, Not Reopening

Iteration 01 Phase 06 was the combined real-App acceptance boundary. Its first
physical run exposed zero-byte App documents; after that repair, the resumed
run exposed reconnect and rename authority defects.

Under the candidate Phase semantics, the shared acceptance barrier never
exited. Automated proof and partial physical lanes were Cell contributions, not
the Phase exit. A failed acceptance attempt updates evidence and replans the
affected Cell; it does not reopen a completed Phase.

The existing “Phase 07” correction folder is useful local organization, but it
does not need to become a peer Phase in the Task axes model. The correction is
Plan work inside the still-unsatisfied acceptance horizon unless it introduces
another real shared barrier.

### Workbench Phase 08 — Invalid Candidate Evidence

The first Phase 08 physical run used a current iPad against a stale macOS Host
build. The observation truthfully showed `Review Unavailable`, but it did not
test the declared current baseline. Rebuilding the Host and rerunning the same
boundary produced the valid result.

This invalidated one candidate exit certificate; it did not invalidate a
previously exited Phase. The Phase remained active until evidence matched the
declared baseline and predicate.

### Workbench Phase 01 and Later Corruption — New Claim Boundary

Phase 01 accepted the evidence-backed file-pair selection/relaunch behavior.
The later combined sequence exposed a zero-byte corruption during a broader
mutation path. That observation did not make the earlier selection evidence
false; it introduced a stronger product obligation and correction boundary.

The right response is a new Slice or, under real cross-Track barrier pressure,
a new Phase—not silently widening and reopening the meaning of Phase 01.

### Surface Camera — One Admission Barrier, Many Attempts

Receiver/publication work passed through V2/V3/V4 repair and independent audit
attempts. Until both bounded child audits and the aggregate verdict passed, the
host-only consumption authorization remained `FAIL`.

The useful Phase is the receiver-consumption admission barrier. Each repair,
audit, recovery audit, and publisher dependency is Plan/Slice/Assignment work
inside Cells contributing to that barrier. Treating each failed candidate as a
closed and reopened Phase would manufacture lifecycle churn and hide the one
unchanged authorization proposition.

## Phase Contract

A Phase instance is a scoped shared barrier. It minimally establishes:

- the outcome/evidence/authority proposition that later work must wait for
- participating Tracks and therefore required Cells
- the relevant baseline or proof horizon when the predicate is version-sensitive
- the semantic exit predicate
- only material dependencies or concurrent-barrier relations

The proposal does not require a universal Phase schema or event log. These
meanings may stay inline until recovery or coordination pressure justifies a
dedicated section/file.

### Failure Before Exit

An unsuccessful attempt does not reopen the Phase. The Phase is still active;
the affected Cell loses or never gains satisfaction, records the
discriminating evidence, and revises its partial Plan.

This rule prevents tests, implementation completion, or an Agent report from
being mistaken for the shared barrier exit.

### Exact Exit Invalidation

Use `reopened` only when all of the following hold:

1. the Phase previously exited
2. new evidence directly defeats that same exit predicate on its claimed
   baseline/proof horizon
3. the Phase scope and meaning remain materially the same

Reopening preserves rather than erases the former exit: record the defeating
evidence and any downstream fronts that consumed the claim. Required Cells
become unsatisfied only where the counterexample reaches them; their Plans
resume or are replaced at the new knowledge horizon.

If the predicate, baseline, authority boundary, or required Track set changes
materially, create a new/successor Phase. Calling that change “reopening” would
rewrite the old contract after observing its result.

### New Obligation After a Valid Exit

If the former predicate remains true but the product expectation, threat
model, acceptance surface, or scope expands, the previous Phase stays exited.
Represent the new obligation as Plan work or a new Phase when it creates a real
shared barrier. A later defect is not automatically proof that every earlier
claim was false.

## Scope Overlap Is Not Active Overlap

Two Phase declarations may name overlapping Track sets without both being
active for the shared Track. A downstream Phase can be visible but pending its
entry condition. The normal rule is:

> one active Phase Cell per Track; declared future scope does not count as
> active overlap.

Before allowing one Track to serve two active Phases, test in order:

1. **Same barrier?** Merge or rescope the Phase.
2. **Failure/correction inside one barrier?** Keep it in the affected Cell Plan.
3. **One item is only an observation or review point?** Use a Gate/Milestone or
   Slice disposition rather than a Phase.
4. **Different continuing obligations?** Refine the Track.
5. **One barrier depends on the other?** Keep the downstream Cell pending.
6. **Two genuinely independent shared barriers remain?** Admit active overlap
   only when concurrency has positive net management value.

The final case is a bounded exception, not an invalid topology. It creates a
partial order between Phases and therefore must expose:

- which Cell Plan owns each piece of work
- whether either return constrains or invalidates the other
- how a shared return contributes without duplicating the Slice
- which barrier, if any, blocks integration or external effect

A work item has one Plan owner. Another Cell may consume or reference its
return; it does not copy the work or evidence into a second Plan.

## Compact Representation

Default:

```text
Phase P1 · active
  barrier: current receiver candidate is safe for host-only consumption
  scope: Receiver, Evidence
  cells: Receiver-P1 active; Evidence-P1 waiting on candidate
  exit: both current-candidate contributions pass aggregate admission
```

Exact reopening:

```text
Phase P1 · reopened
  prior exit: evidence E on baseline B
  defeated by: counterexample F against the same predicate/baseline
  affected fronts: P2/Receiver consumption
  resumed cells: Receiver-P1, Evidence-P1
```

Active overlap exception:

```text
Track B
  Cell B-P1 -> Plan owns return R1
  Cell B-P2 -> consumes R1; Plan owns only P2-specific return R2
  relation: P1 and P2 independent until integration Gate G
```

Root `packet.md` exposes this only when the overlap, invalidation, or affected
front changes a Human decision or the next coordination action.

## Failure Modes and Falsifiers

- Calling every failed attempt a reopening creates status churn and destroys
  the meaning of Phase exit.
- Silently widening the old exit predicate rewrites history and makes earlier
  Human acceptance impossible to interpret.
- Treating all later defects as invalidation causes unbounded rollback of
  still-valid claims.
- Forbidding every active overlap serializes truly independent barriers.
- Allowing overlap without single work ownership duplicates Plans and evidence.
- A mandatory Phase state machine or complete matrix would cost ordinary tasks
  more than this distinction returns.

Reopen the default single-active-Phase rule when real tasks repeatedly need the
bounded overlap exception and Track refinement produces artificial ownership.
Reopen the invalidation rule when Humans cannot distinguish “still not passed,”
“previous pass disproved,” and “new requirement” from the compact record.

## Accepted Contract

1. Keep one active Phase per Track as the default, while allowing declared
   future Phase scopes to overlap.
2. Treat failed or invalid candidate evidence before Phase exit as Cell
   replanning inside the still-active Phase—not reopening.
3. Reserve Phase reopening for direct invalidation of the exact previously
   exited proposition on its claimed baseline; retain the former exit and name
   affected consumers.
4. Use new Plan work or a new Phase when scope, predicate, baseline, or
   obligation changes materially.
5. Admit simultaneous Phase Cells on one Track only as a bounded independent-
   barrier exception after reclassification, Track refinement, and dependency
   checks; keep one owner for each work return.

Sir accepted this contract as `D-033`. It keeps the ordinary model small: most
Tasks see one active horizon and no reopening machinery. Extra relations appear
only when reality actually creates concurrent barriers or defeats a previously
consumed exit claim.
