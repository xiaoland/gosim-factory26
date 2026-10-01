# Working Note — Slice Scope and Human Effect Language

- **State**: accepted task-packet model; vocabulary remains subject to real-task evidence
- **Sources**: `D-015..D-017`, `D-026..D-027`, `D-032`, `D-036..D-039`;
  `V-039`, `V-042`, `V-053..V-059`, `V-067..V-070`; Sir's `IQ-slice` /
  `IM-slice` proposal; real SVC packets using unqualified `Slice 0..5`
- **Use**: Make a Slice's expected return and effect authority predictable to
  Human and Agent without splitting one linear Plan by posture or binding a
  mixed recursive work unit to one cognitive mode

## The Actual Ambiguity

The phrase “execute Slice 1” carries two incompatible readings:

- Agent: advance the next bounded management unit, which may only investigate
  or design
- Human: begin implementation and mutate the product/system

The problem is not Slice granularity. It is that the Slice identifier omits the
kind of return and effect/authority boundary that matters to collaboration.

Real packets show this drift. “Slice 0” can mean product/contract projection,
external research, or design freeze; later numbered Slices in the same Plan can
mean source changes, external repository controls, migration, and acceptance.
The number provides order but no Human-predictable effect.

## Do Not Split the Plan by Posture

Separate `explore-plan.md`, `design-plan.md`, and `implementation-plan.md` files
would make the common Human expectation visually obvious, but would distort the
accepted model:

- a long-task Plan is one current linear route owned by Task/Track/Phase/Cell
- inquiry, design, implementation, and verification recur and call one another
- a plan-file boundary would duplicate dependencies, TBC state, and integration
  while making the transitions look like a fixed lifecycle

One Plan can therefore contain differently scoped Slices:

```text
01-IQ -> 02-DS -> 03-IQ -> 04-IM -> 05-VR -> TBC
```

Human preference for “understand, decide, then implement” is valuable as an
effect-escalation expectation, not a claim that real work always follows one
pass through those stages.

## Scope Is Not Working Posture

A Slice needs a stable **primary return scope**. Working posture describes the
move currently used to obtain that return.

Example:

```text
01-IQ · explain stale receiver result
  Explore: inspect current source and prior evidence
  Execute: run a reversible task-local probe
  Diagnose: discriminate candidate causes
  Verify: cross-check the supported boundary
  return: bounded diagnosis + evidence horizon
```

The Slice remains `IQ` because its independently integrated result is
epistemic. It is not bound to one posture.

Likewise, an `IM` Slice may temporarily Explore an unfamiliar owner, Diagnose a
failed build, or Verify intermediate invariants; its return remains an approved
system-state transition with proof/recovery obligations.

If supporting work develops an independently accept/reject/park/integrate
return, it becomes another Slice. Otherwise it remains a Step, Assignment, or
local posture inside the original Slice.

## One Plan-Local Index, Then the Scope Tag

The number belongs to the Plan's single Slice sequence. Scope tags do not own
separate counters:

```text
01-IQ -> 02-DS -> 03-IQ -> 04-IM -> 05-VR -> TBC
```

Index-first notation makes the semantic relation visible: `03` identifies the
third Slice in this Plan; `IQ` qualifies what that Slice returns. `IQ-03` would
visually suggest an Inquiry-specific namespace and makes a mixed Plan's order
harder to scan. Slice handles are Plan-local unless a higher-level address is
needed, in which case the Plan owner/Cell qualifies the handle.

## Accepted Slice Scope Tags

The smallest coherent set follows return contracts already present in the
task-packet module families:

| Tag | Primary return | Default effect implication |
| --- | --- | --- |
| `IQ` | inquiry/diagnosis synthesis and evidence boundary | no durable product/system mutation; task-local probe only if stated |
| `DS` | design model, alternative disposition, or Human decision | no implementation authority; task-local design artifacts only |
| `IM` | approved product/system state transition plus integration/proof/recovery | durable mutation is intended, but still requires applicable authorization |
| `VR` | explicit claim disposition at the relevant proof/acceptance horizon | observation/acceptance work; no hidden corrective mutation |
| `RT` | work-system retrospective diagnosis and candidate intervention | no durable intervention until separately planned under its normal owner |

`IQ` includes both Inquiry and Diagnosis because their Human-visible effect
boundary and epistemic return are the same; the semantic title states whether
the Slice is open research or causal diagnosis.

These tags are not file types, postures, Agents, or lifecycle stages. A Plan
expands them once in a local legend. The title always carries the real semantic
result:

```text
01-IQ · establish current release-authority failure
02-DS · select one tag-authoritative release contract
03-IM · implement dark release model
04-VR · accept the exact published artifact chain
```

An unexplained `01-IQ` is no better than an unexplained `V-01`; Human should not
have to guess the abbreviation.

## Why Not Only `IQ` and `IM`

Two tags are enough to distinguish “learn” from “mutate,” but they collapse two
material Human boundaries:

- Design asks the Human/authority to select meaning or trade-offs; Inquiry asks
  for evidence/reframing review.
- Verification may run substantial commands or external acceptance without
  authorizing an implementation correction.

The five-tag set aligns with independently useful return contracts rather than
every working posture. It should remain optional for a simple one-Slice Task;
once a Plan contains several scoped Slices or Human effect ambiguity is
plausible, use it consistently.

## Effect and Authority Still Need Plain Language

A tag cannot encode every side effect. Each material Slice must expose its
effect/authority boundary in the Plan entry, especially for project writes,
external systems, destructive actions, or Human acceptance:

```text
| Slice | Return | Effect / authority | State |
| 01-IQ · current behavior | supported evidence map | read-only repository/runtime inspection | active |
| 02-DS · contract choice | selected design | task-packet edits; Human decision required | pending |
| 03-IM · owner migration | changed system + proof | durable source mutation; Start required | not authorized |
```

`IM` means implementation is the intended return; it does not itself grant
permission. Conversely, a durable source/config/external mutation cannot be
hidden inside `IQ`, `DS`, or `VR`. Close/return the current Slice and create or
activate an `IM` Slice with the applicable Impact Handshake/Start boundary.

Task-local inquiry artifacts or reversible probes may remain in `IQ` when their
scope and cleanup are explicit and they do not mutate durable project/system
truth.

## Human-Agent Language Contract

Avoid the generic verb “execute” for all Slice kinds. Use a verb that predicts
the effect:

- `开展 / 调查 / 推进 01-IQ`
- `讨论 / 复审 / 决定 02-DS`
- `实施 03-IM`
- `验证 / 验收 04-VR`
- `复盘 / 评估 05-RT`

An update or request names the tag, semantic title, and relevant effect:

```text
现在开展 01-IQ：只读确认当前失败边界，不修改 durable state。
下一候选是 02-IM，但尚未获得开始实施的授权。
```

`packet.md` Task-map projection uses the same language so Human task switching
does not require opening the Plan to learn whether the current front mutates the
system.

## Scope Transition Rules

The primary return scope of an active Slice does not silently change:

- inquiry reveals a design choice -> return `IQ`, then activate `DS`
- design exposes missing evidence -> park/retain `DS`, run `IQ`, then return
- design is accepted -> activate `IM` only under mutation authority
- implementation failure needs causal isolation -> open `IQ`, then resume or
  replace `IM`
- verification fails -> return `VR` disposition; corrective work uses `IQ`,
  `DS`, or `IM` according to the uncertainty/effect
- retrospective selects an intervention -> return `RT`; implementation occurs
  later through the intervention's normal `IM`/owner path

This may produce several small Slices, but only when there is a real return,
authority, or integration boundary. Do not split every posture change.

## Relation to Plans, Modules, and Files

- Plan remains one partial linear route at its Task/Track/Phase/Cell owner.
- Slice scope tag lives in that Plan; it does not select another Plan file.
- Inquiry/design/verification modules own deep information state, not work
  sequencing. An `IQ` Slice may link `inquiry.md`; an `IM` Slice may link an
  implementation dossier.
- A Slice earns a supporting file only under module/Cell artifact pressure; no
  universal `slices/` or `iq-slices/` directory follows from the tag.
- Assignment associates an Agent/tool with work inside the Slice; Agent role
  does not determine Slice scope.

## Alternatives and Cost

| Alternative | Benefit | Failure/cost |
| --- | --- | --- |
| posture-coded `EX/DI/EXEC` | shows the current cognitive move | changes during recursive work; incorrectly grants working mode ownership over the Slice |
| separate per-scope Plans | visually obvious lifecycle/effect | breaks one route into competing Plans and duplicates integration/TBC state |
| untyped `S1` plus descriptive title | minimal vocabulary | repeated conversational references drop the title; effect/authority ambiguity returns |
| return-scope tags + plain effect | stable compact common ground | adds a five-tag legend and requires discipline at scope transitions |

The recommended model pays a small naming cost to reduce Human review,
correction, and accidental-mutation cost. It remains progressive: one obvious
Slice does not need a tag table.

## Failure Modes and Falsifiers

- Tags become unexplained bureaucracy or replace semantic titles.
- `IM` is mistaken for mutation authorization.
- Agents relabel an active Slice instead of closing one return and opening the
  next authority boundary.
- Every internal posture call becomes a new typed Slice.
- Mixed end-to-end results are forced into artificial micro-Slices with no
  independent integration value.
- The five tags drift from module/verification/retrospective semantics.

Reopen the five-tag set if Humans still cannot predict effects from real Plan
updates, or if `DS`/`VR` rarely change collaboration compared with a simpler
`IQ` versus `IM` distinction. Reopen tag optionality if inconsistent adoption
costs more than always tagging multi-slice Plans.

## Lead Recommendation

1. Do not split Plan files by inquiry/design/implementation posture.
2. Give every material Slice one stable primary return scope, not one bound
   working posture.
3. Use one Plan-local index followed by `IQ`, `DS`, `IM`, `VR`, or `RT`, plus
   semantic titles and a local legend in multi-scope Plans; keep simple
   one-Slice Tasks untagged when unambiguous.
4. State effect/authority in plain language; tag never grants mutation.
5. Do not hide durable mutation under non-`IM` work; cross the gate through a
   distinct implementation Slice.
6. Use scope-appropriate collaboration verbs instead of generic “execute
   Slice.”

This keeps Slice as the management unit while making the Human-visible return
and effect boundary stable across recursive Agent work.
