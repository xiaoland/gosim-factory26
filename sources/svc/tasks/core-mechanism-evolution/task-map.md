# Task Map — SVC Core Collaboration Mechanism Evolution

## Role

This file owns the current Task-space projection: admitted axes, real Cells,
the active barrier, Plan fronts, and material integration relations. Cell files
own their partial linear Plans. [`packet.md`](packet.md) projects only the
consequential Human view; Inquiry, Design, Decision, and Verification modules
own their respective information concerns.

## Admitted Topology

For this Task, the five functional clusters are continuing obligations with
different current states and later realization work, so they are admitted as
Tracks. This is a task-local management choice, not a rule that every SVC
functional cluster is always a Track.

| Handle | Track and continuing obligation |
| --- | --- |
| `TP` | **Task Packet** — preserve useful Human control and Agent continuity through a progressively shaped volatile package |
| `WP` | **Working Protocol** — make Agent work selection, authority, feedback, integration, and Human pause behavior predictable |
| `SA` | **Sub-agents** — gain context isolation and specialization only when delegation, verification, and integration total cost is favorable |
| `VF` | **Verification** — construct claim-relative product/technical evidence, acceptance dispositions, and bounded residual risk |
| `TD` | **Tastes & Design Ability** — align with Sir's substantive taste while improving product, UI/UX, architecture, and implementation judgment |

`P1 — Capability Model` turned the completed reference intake into a reviewable
capability model and rough SVC landing boundary for each required Track.

- **Entry**: target consumer/outcomes and the five-cluster topology are accepted;
  reference intake is sufficient to begin capability modeling.
- **Exit**: every required Cell has a reviewed capability/non-goal boundary,
  contribution to the three outcomes, operating decisions, current SVC
  footholds, progressive landing direction, failure/simple-task pressure, and
  material unknowns. Cross-Track conflicts must be explicit.
- **Barrier state**: closed. All five Cell returns are accepted-satisfied and
  remain reopenable by later evidence.
- **Continuation horizon**: completed by admitting `P2` below.

The current Phase is `P2 — Source Landing`. All five Tracks participate
because the Working Protocol kernel cannot shed its current umbrella content
until every routed owner exists, and all five source surfaces must follow one
repository and corpus-writing contract.

- **Entry**: `P1` is closed; all five accepted capability models and their
  rough landing pressures are available.
- **Exit**: the source owner/layout map, corpus-writing contract, per-Track
  content/move boundaries, public-path dispositions, templates and bounded CLI
  projections are landed and mechanically verified.
- **Barrier state**: satisfied; reopenable by real Consumer evidence. The first `sections/`-based
  projection was rejected; all five Cell returns are now integrated through the
  browse-first layout, local authoring owner, and Task CLI seam in
  [`design/85`](design/85-browse-first-layout-and-task-cli.md), plus the
  pressure-proven source depth in
  [`design/86`](design/86-progressive-source-depth.md), corrected to one
  symmetric directory-entry grammar by
  [`design/87`](design/87-symmetric-corpus-navigation.md) and reconciled into
  the implementation entry and approximate Plan in
  [`design/88`](design/88-p2-review-and-realization-outline.md), then realized under
  Sir's explicit start. The source, templates, CLI and release projections pass
  the complete repository suite and an installed-wheel smoke test.
- **Mutation boundary**: the authorized Source Landing mutation is complete.
  Commit, release and external effects remain unauthorized.

## P1 Cell Map

| Cell | P1 state | Current Plan front / return | Integration or attention |
| --- | --- | --- | --- |
| [`TP × P1`](cells/task-packet-capability-model.md) | satisfied; reopenable | `06-VR` returned the full topology dogfood and its structural findings | Reopen only if another Cell cannot be represented without violating the accepted packet model |
| [`WP × P1`](cells/working-protocol-capability-model.md) | satisfied; reopenable | `39-VR` confirms complete capability coverage and a rough landing boundary | Reopen only if later interfaces or real tasks falsify the accepted kernel/seams |
| [`SA × P1`](cells/sub-agents-capability-model.md) | satisfied; reopenable | `D-087` corrects result routing; `D-088` accepts only Explorer and Executor contracts | Reopen on unfavorable real delegation economics or a missing recurring boundary |
| [`VF × P1`](cells/verification-capability-model.md) | satisfied; reopenable | `D-089` accepts claim-relative qualification and consumer-owned disposition | Reopen on proof-routing, modular-reuse, or disposition failures |
| [`TD × P1`](cells/tastes-design-capability-model.md) | satisfied; reopenable | `D-090` accepts use-case-routed progressive taste and typed authority | Reopen on retrieval, authority, or design-quality failures |

## Current P2 Cell Map

| Cell | P2 state | Current Plan front / return | Integration or attention |
| --- | --- | --- | --- |
| [`TP × P2`](cells/task-packet-source-landing.md) | satisfied; reopenable | symmetric Task Packet source, template family, and bounded `task init/grow` landed | Reopen if real packets expose shape or Human-surface cost |
| [`WP × P2`](cells/working-protocol-source-landing.md) | satisfied; reopenable | compact kernel, symmetric `methods/`, and local authoring owner landed | Reopen if navigation or integration loses obligations |
| [`SA × P2`](cells/sub-agents-source-landing.md) | satisfied; reopenable | Explorer and Executor consumer-relative contracts landed | Reopen on unfavorable delegation economics or a missing recurring boundary |
| [`VF × P2`](cells/verification-source-landing.md) | satisfied; reopenable | compact qualification owner and distributed-proof seam landed | Reopen on evidence routing, reuse, or disposition failures |
| [`TD × P2`](cells/tastes-design-source-landing.md) | satisfied; reopenable | Design projections and implementation-taste depth landed | Reopen on retrieval, authority, or design-quality failures |

## Material Relations

- One Human question is foregrounded at a time. Backgrounding a Cell is not a
  dependency or blocked state.
- This task packet is the current state carrier for every Track. `TP` owns the
  model of that carrier; if another Track produces state the accepted package
  cannot represent economically, it returns a falsifier to `TP` rather than
  inventing local packet grammar.
- `WP` defines the return/authority/feedback/integration seam consumed by
  specialized `SA`, `VF`, and `TD` methods. Those Tracks may still challenge
  the seam; this is not a one-way dependency.
- `SA` owns result routing and delegation economics. Explorer reports have no
  generic validator; Executor candidates may reuse `VF` mechanisms for bounded
  qualification. `TD` supplies judgment whose observation surface must remain
  compatible with `VF` and Human authority in `WP`.
- A Cell return updates its Cell owner first, this map only when the Phase/front
  changes, and `packet.md` only when the Human consequential picture changes.
  Cross-Cell Inquiry, Design, Decision, and Verification information stays in
  its semantic module rather than being copied into every Cell.

## Current Front

`P1` is closed. `D-087` corrects the overgeneral Sub-agent transport model;
`D-088..D-090` accept the minimum SA, VF, and TD returns. [`design/82`](design/82-p1-capability-reconciliation.md)
owns the accepted cross-Track synthesis.

`P2` is satisfied and reopenable with all five real Cells. [`design/85`](design/85-browse-first-layout-and-task-cli.md)
corrects the former `sections/`/`work/` umbrellas, gives Corpus writing a local
unpublished owner, and integrates the Task Packet CLI projection.
[`design/86`](design/86-progressive-source-depth.md) prevents those semantic
entries from becoming new monofiles;
[`design/87`](design/87-symmetric-corpus-navigation.md) corrects its asymmetric
file/directory grammar. [`design/88`](design/88-p2-review-and-realization-outline.md)
closes the review gaps, admits the opt-in template family, and gives the
four-return realization outline. `design/83..84` remain historical evidence.
The authorized realization is complete and mechanically verified. The current
front is a concise handoff to Sir; real Consumer Tasks provide the next evidence.
