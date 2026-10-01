# Working Note — Inquiry Module and Diagnostic Method

- **State**: accepted task-local direction through `D-037`/`D-038`; stable
  entry refined to one `inquiry.md` through `D-043`
- **Sources**: `D-014..D-038`; `V-033`, `V-036..V-040`, `V-064..V-071`;
  current diagnostics template; SVC field-study, release-diagnostic, Workbench,
  InKCre, and current-task inquiry artifacts
- **Use**: Give long or consequential evidence work a stable epistemic owner
  without turning every lookup into a module, duplicating the Cell Plan, or
  confusing gathered evidence with verified task completion

## Semantic Job

The Inquiry module owns one task-local chain:

```text
question or observed mismatch
  -> bounded evidence acquisition
  -> observations separated from interpretation
  -> competing explanation / counterexample search when material
  -> current synthesis and residual unknowns
  -> return to the consuming Plan, design decision, or Human review
```

It does not own the Task outcome, work topology, implementation authority, or
final acceptance merely because it used tests or collected convincing data.

`Explore` and `Diagnose` remain working postures. They may create or update this
module, but a posture transition does not create/rename files. Conversely, a
design or implementation Slice may consume the same inquiry module while the
Agent posture changes several times.

## Diagnosis Is an Inquiry Method, Not an Entry Variant

Inquiry covers open research, evaluation, field study, model building, and
causal questions. Diagnosis is the case where an observed mismatch makes
causal discrimination the current Inquiry method. It changes the question and
probes, not the evidence/freshness/synthesis/return lifecycle.

Standardize one stable entry:

```text
inquiry.md
```

A diagnosis-dominant Task makes that meaning explicit in the title and current
question. A bounded question used by one Cell remains a Cell-owned artifact
instead of activating a task-wide module.

## Activation and Early Shape

Keep the work inside `packet.md` or the consuming Cell when one bounded lookup,
reproduction, or source read can answer it without meaningful provenance or
causal ambiguity.

Create the module entry at Task/Cell shape preflight—not after it becomes long—
when one or more of these are already credible:

- several evidence sources, environments, cases, or observation rounds
- sampling/selection/method choices can change the conclusion
- competing causes or alternatives require discriminating probes
- evidence has sensitive, immutable, external, or independently reviewable
  provenance
- several Cells or decisions consume the same synthesis
- delegated Explorers need a stable question/return owner
- Human review concerns the reasoning/evidence boundary, not only the final
  task result

Agent count, tool variety, and the word “research” alone do not activate it.

## Progressive Package Shapes

### Bounded inquiry, including diagnosis

```text
inquiry.md
```

The entry contains the current synthesis and all evidence needed to judge it.
The 29-line Windows list-isolation diagnosis from the field-study packet is a
good pressure example: one symptom, one bounded aggregate observation, one
supported boundary failure, one constrained workaround, and one future product
question need no directory.

### Expanded inquiry

```text
inquiry.md
inquiry/
  selection-policy.md
  macos-case.md
  wsl-case.md
  windows-case.md
  cross-case-synthesis.md
```

Files appear by method validity, independent case review, or return—not because
every tool/query needs a log. If cases form a large regular corpus, the module
may use deterministic shards under `D-035` while remaining one semantic owner.

### Diagnostic depth inside Inquiry

```text
inquiry.md
inquiry/
  reproduction.md
  cause-matrix.md
  stale-build-probe.md
  current-baseline-retest.md
```

Only artifacts with independent provenance, replay, review, or integration
value receive files. A matrix can stay inline. A probe file is not created for
each command or rejected guess.

The module entry remains stable and integrates these artifacts. A separate
`synthesis.md` is normally redundant because synthesis is the entry's central
job; create one only when the synthesis itself is an independently immutable or
externally reviewed return.

## Entry Content Contract

In simple, locally natural headings and language, the entry must let the next
Agent recover:

1. **Owned question/mismatch and consumer** — what must become knowable, why it
   matters, and which Plan/decision will use the return
2. **Evidence boundary** — relevant baseline/time/environment, examined and
   excluded sources, selection/sampling limits, unavailable evidence, and any
   sensitive/external storage boundary
3. **Direct observations** — what was actually read, reproduced, measured, or
   reported, with resolvable handles where useful
4. **Interpretations and alternatives** — inference distinguished from fact;
   competing causes/frames and evidence that would weaken them when the
   conclusion is consequential
5. **Current synthesis** — supported conclusion/diagnosis at its actual proof
   horizon, or an explicit unresolved/ambiguous result
6. **Next discriminator / return condition** — the smallest observation,
   Human information, or decision that would materially update the synthesis,
   plus when the consuming owner can proceed

These are semantic obligations, not mandatory headings or a universal claim-ID
schema. A simple diagnosis may express them in five short paragraphs. Tables
are useful only when several causes/cases/observations need exact comparison.

## Evidence Discipline

The minimum evidence ladder is:

```text
source observation
  -> within-boundary interpretation
  -> supported synthesis
  -> candidate generalization (only with additional cases)
```

Keep the following distinctions explicit when they change the conclusion:

- observed absence versus unavailable or unexamined evidence
- reproduction versus Agent/Human report
- correlation versus a probe that discriminates a cause
- source authority versus similarity/navigation result
- current baseline versus stale or candidate bytes/configuration
- local proof versus external/product observation

Do not require exhaustive falsification for every bounded conclusion. The cost
of alternatives/counterexamples should follow false-accept loss and correction
cost. A low-risk exact lookup may return directly; a diagnosis that authorizes
a broad migration needs stronger discrimination.

“Root cause” is not the default output. Return the supported causal boundary
needed to select the next correction, and preserve upstream/deeper unknowns.

## Freshness Interface

Inquiry conclusions are consumable only while their supporting evidence remains
valid for the claimed source/baseline/environment. Stale evidence can produce a
confident but incorrect design or implementation return.

The module therefore records freshness information when it is material:

- source identity/version, relevant observation time, baseline, environment,
  or candidate digest
- known invalidation event or condition, such as a dependency release, source
  mutation, deployment change, or superseding Human input
- `fresh`, `stale`, or `unknown` disposition only when the applicable semantic
  owner can support that judgment
- the smallest recheck needed before the synthesis can be consumed again

The task packet is a carrier, not the freshness authority. It does not invent a
universal TTL, infer validity from file mtime, or claim that a recent timestamp
makes evidence relevant. The source/domain owner and suitable verification
surface determine invalidation semantics. When material freshness is stale or
unknown, the entry must stop presenting the synthesis as current truth and
return to inquiry/recheck before downstream consumption.

## Search and Tool Use

Tool choice follows the information shape and proof need:

```text
claim/decision need
  -> smallest suitable text/AST/symbol/data-flow/runtime/document surface
  -> bounded query
  -> inspect query validity and scope
  -> cross-check weak/negative evidence when needed
  -> update inquiry or return compact evidence map
```

The module records a method only when query completeness, selection, sampling,
or reproducibility affects the result. It does not preserve routine `rg`, tree,
AST, browser, or command transcripts. Store the discriminating observation and
resolvable source, not the Agent's entire search path.

Explorer Assignments return compact findings, evidence handles, gaps,
conflicts, and remaining frontier. Raw sub-agent output is candidate evidence;
the Lead integrates it into the module before it changes Cell/task state.

## Plan Ownership and Return

The Inquiry module does not maintain a competing work Plan. The
Task/Track/Phase/Cell owner retains the linear Plan and may contain an
exploration/diagnosis Slice that links this module.

```text
Cell Plan: diagnose mismatch M
  -> inquiry module owns evidence state
  -> Explorer/probe returns
  -> Lead integrates synthesis
  -> Cell Plan accepts, rejects, parks, or opens design/implementation work
  -> consequential result rolls up through task-map.md to packet.md
```

The module's “next discriminator” is epistemic state, not another global/local
Plan. This separation prevents the same work from appearing as both a Cell Plan
and an inquiry plan.

## Seam with Verification

Inquiry asks **what is true, why, or which model is supported** under current
uncertainty. Verification asks **whether an explicit claim/candidate/change
satisfies its expected product or technical contract** on the right observation
surface.

The same command can serve either purpose:

- a test run used to distinguish two suspected causes belongs to diagnosis
- the same test after correction may support the verification claim

Reuse the observation by link and state its proof horizon; do not copy it into
two ledgers. Inquiry evidence does not silently become acceptance, and a
verification failure may reopen diagnosis without changing ownership of the
failed claim.

## Field Rehearsal

### Cross-host Agent-thread field study

The existing packet already separates selection policy, review protocol,
collection plan, diagnostics, and observations. Under this model, an
`inquiry.md` entry would integrate the question, method boundary, corpus state,
cross-case synthesis, and return; sensitive archives remain outside the repo.
Host/case files earn separation through provenance and independent review, not
file length.

### Release contract diagnostics

The long `diagnostics.md` combines reproduced mismatch, repository state,
failure matrix, dependency research, comparable-project correction, and
implementation consequences. A stable `inquiry.md` could keep current causal
synthesis and next discriminator while external-semantics/benchmark artifacts
move behind it. Accepted design consequences then return to the design/delivery
owner instead of extending the diagnostic history indefinitely.

### Workbench acceptance correction

Report, analysis, and solution files usefully distinguish observation,
diagnosis, and selected correction, but Phase/Iteration directories sometimes
turn every feedback round into lifecycle structure. Under the module contract,
a Cell-local Inquiry artifact can integrate several probes and return a supported
correction boundary to the same Cell Plan; a new Task packet is unnecessary.

### This design task

`01-current-task-episode.md` is a useful bounded inquiry artifact: it separates
observed sequence, evidence limits, causal hypotheses, and a counterfactual.
It is not another module because the current design inquiry consumes it through
the active design entry.

## Current Diagnostics Template

`task-diagnostics-matrix.template.md` is useful as a compact whole-Task packet
when diagnosis dominates. As a reusable module contract it has four problems:

- it repeats the full `packet.md` fields instead of returning to a parent Plan
- it assumes one supported “root cause” rather than a bounded causal result
- it makes the failure matrix structurally central even when one observation
  resolves the mismatch
- `Durable Follow-up` can encourage premature destination/promotion
  bookkeeping before a semantic correction is accepted

Do not remove or replace the template yet. Later landing should decide whether
to keep it as a diagnosis-dominant Task example, refine it, or add a separate
pressure-loaded module example after real use validates this contract.

## Retirement

When the question is resolved or deliberately parked:

1. integrate the supported return and residual unknowns into the consuming
   Cell/design/verification owner
2. update `packet.md` only if the result changes Human current truth, risk,
   decision, or next action
3. retain method/case evidence only while it supports review, reopening, or
   expensive recovery
4. stop maintaining rejected-query history and superseded intermediate
   synthesis

The Task packet remains volatile; useful project truth is promoted through its
normal owner during planned work, not because an inquiry module exists.

## Failure Modes and Falsifiers

- Every small lookup becomes `inquiry.md`, increasing navigation and update
  cost without improving a return.
- The module becomes a raw research notebook or transcript archive.
- A cause matrix creates hypothesis theatre after one explanation is already
  discriminated.
- “Current synthesis” drifts from evidence artifacts or masks missing evidence.
- The module duplicates the Cell Plan or verification ledger.
- Explorer returns are accepted by confidence/identity rather than integrated
  against the question and evidence boundary.
- A broad inquiry module becomes a new task monolith containing unrelated
  questions with different consumers.

Reopen the one-entry design if causal diagnosis repeatedly develops a distinct
consumer/cadence/lifecycle or Humans cannot predict where a causal result lives.
Reopen module activation if early entries are commonly retired without having
reduced search, recovery, delegation, or review cost.

## Lead Recommendation

1. Standardize one `inquiry.md` epistemic module; treat Diagnosis as the
   observed-mismatch question/method inside it.
2. Activate it early when evidence/method/causal/provenance pressure is already
   credible; keep one-step lookups in their consuming owner.
3. Make the entry own current integrated synthesis and next discriminator;
   expand through same-stem semantic artifacts, not query logs or a duplicate
   `synthesis.md` by default.
4. Keep facts, inference, supported conclusion, and generalization distinct in
   proportion to decision loss.
5. Carry material evidence freshness/baseline and invalidation/recheck
   information without making the task packet its oracle.
6. Keep the authoritative Plan in its Task/Track/Phase/Cell owner and return
   inquiry results to that Plan before any task-state change.
7. Keep inquiry evidence and verification acceptance distinct while reusing
   observations by reference.

This creates a deep module: a predictable small entry can hide complex search,
cases, probes, and delegated evidence work while returning one bounded synthesis
to the rest of the Task.
