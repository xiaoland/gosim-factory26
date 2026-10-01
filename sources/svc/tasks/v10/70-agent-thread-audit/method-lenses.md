# Evidence-Informed Method Stack

No one discipline supplies a complete model of an Agent thread. The export is
simultaneously an event log, a record of interaction, and a trace of work
distributed across people, agents, documents, repositories, and runtime
systems. The audit will therefore use compatible lenses at the resolution where
each is informative, without forcing the corpus into a single academic model.

## Chosen Lenses and Their Boundaries

| Lens | Useful unit | Contribution to this audit | Misuse to avoid |
| --- | --- | --- | --- |
| Qualitative multi-case study | case and cross-case contrast | Treats each selected thread as a bounded analytic case; promotes a finding only through replication logic and counterexample search | Treating eight deliberately selected cases as prevalence statistics |
| Process tracing | episode and proposed mechanism | Connects a human move, Agent move, artifact/state transition, and observed outcome into an explicit causal *hypothesis* | Assuming temporal succession proves causation |
| Cognitive task analysis / distributed cognition | person–Agent–artifact–environment system | Locates control and working state in task packets, plans, tools, worktrees, services, and people—not only in prose | Inferring private cognition or reducing collaboration to message sentiment |
| Control-loop / systems lens | intent, authority, action, observation, correction | Tests whether collaboration has a legible goal, a rightful mutator, observable feedback, and a recovery/hand-off path | Treating people as interchangeable controllers or every deviation as a defect |
| Resilience / incident analysis | disruption, recovery, and handoff | Treats detection, containment, recovery, and learning as first-class coordination work, including successful but fragile control | Looking only for failure or assigning a single hindsight root cause |
| Event-log / process-mining lens | indexed micro-events and transitions | Uses timestamps, types, and turn structure to find candidate boundaries before semantic reading | Inferring work meaning or process quality from event frequency alone |
| Conversation-analysis-inspired repair reading | adjacent turns and repair sequences | Identifies local clarification, constraint, confirmation, correction, and closure moves | Treating injected context or synthetic events as ordinary human conversation |

## Operating Sequence

The audit follows a deliberate coarse-to-fine-to-coarse loop:

`corpus coverage → case trajectory → candidate episode → turn sequence → micro-event → case conclusion → cross-case contrast`

1. **Structural navigation.** Use `thread/index.json` and record classes to
   mark candidate context, turn, compaction, tool, and coordination boundaries
   without assigning semantic meaning.
2. **Within-case reconstruction.** For each candidate work episode, review the
   permitted dialogue and tool-outcome evidence to trace: intended objective,
   cue or constraint, human/Agent move, externalized state change, verification
   signal, and outcome/uncertainty.
3. **Distributed-state map.** Record which of Human, Agent, Artifact, and
   Environment held the relevant authority, knowledge, or mutable state. This
   distinguishes an SVC opportunity from project-local configuration or an
   unavailable platform capability.
4. **Recovery reading when needed.** For a deviation, trace trigger →
   detection → containment/response → verification or handoff. A smooth result
   can still reveal a fragile control boundary, but it is not labelled a defect
   without evidence of cost or risk.
5. **Cross-case comparison.** Compare completed case cards, actively seek a
   boundary/counterexample, and only then elevate a repeated causal shape to a
   corpus pattern.

## Collaboration Control Loop

For product diagnosis, read each work episode as this observable loop:

`intent and authority → action through Agent/artifacts/environment → observable evidence → acceptance, correction, or handoff`

The audit asks where the loop is broken, expensive, ambiguous, or robust. Its
diagnostic dimensions are not quality scores: they are prompts for locating a
mechanism and a possible owner.

| Dimension | Question for the evidence | Typical ownership boundary to test |
| --- | --- | --- |
| Intent and authority | Was the desired outcome and mutation/approval authority legible when action was taken? | Human instruction, task packet, or project protocol |
| Shared state | Could the relevant plan, environment, worktree, service, or release state be located and trusted? | SVC affordance, project configuration, or platform capability |
| Coordination | Could concurrent human/Agent actions avoid collision and retain an accountable owner? | Project workflow, tooling, or runtime behavior |
| Observability | Did an action yield evidence sufficient for the next decision? | Test/inspection/release evidence or SVC telemetry |
| Recovery and continuity | Could the system detect deviation, recover safely, and transfer work across turns/people/machines? | SVC protocol, local practice, or external dependency |

## Unit Discipline

The following units are related but never interchangeable:

| Unit | What it is | What it cannot establish alone |
| --- | --- | --- |
| Native event | One exported runtime record | A human request, completed task, or collaboration outcome |
| Turn | A linked request/response/execution cycle when the schema supports the link | A stable work objective or a causal mechanism |
| Work episode | Analyst-bounded sequence with one objective, checkpoint, recovery, or handoff | A whole thread or a generalizable pattern |
| Case | One selected exact-thread archive and its known context limitations | Population prevalence or a standard consumer journey |
| Corpus | The eight purposefully selected cases | A statistically representative sample |

Compaction, timestamp changes, and tool calls are candidate boundaries only.
They become an episode boundary only when the surrounding permitted evidence
supports a change in objective, control state, checkpoint, recovery, or
handoff.

## Evidence and Claim Discipline

- Label a statement as **observed fact**, **within-case inference**, or
  **candidate hypothesis** before considering it a recurring pattern.
- Process traces must name a competing explanation or a boundary condition.
  This protects against treating an attractive timeline as proof of causality.
- Agent reasoning remains outside the default evidence set. Dialogue and
  observable artifact/tool outcomes can show coordination moves; they cannot
  prove an internal mental state.
- Event-log analysis is an auxiliary navigation and consistency tool. The
  corpus is too small and purposefully selected for automated process discovery
  or statistical claims.
- A thread is an observation window, not a complete project history. “Not
  observed in this archive” is never recorded as “did not exist in the
  project”; unresolved packet association and omitted external state remain
  explicit limits.

## Why This Fits the Exported Corpus

The archive anatomy supports an event-level structural pass, then an episode
and case-level reading. It does not provide a canonical business-process model
or a naturalistic conversation recording. That makes the above sequence more
defensible than either transcript-only close reading or process-mining-led
conclusions.

## Research Basis

- Eisenhardt and Graebner, *Theory Building from Cases* — bounded cases,
  replication logic, and explicit comparison: <https://doi.org/10.5465/amj.2007.24160888>
- Langley, *Strategies for Theorizing from Process Data* — moving between event
  sequence and higher-level process explanation: <https://doi.org/10.5465/AMR.1999.2553248>
- Collier, *Understanding Process Tracing* — causal-process observations and
  disciplined inference: <https://polisci.berkeley.edu/sites/default/files/people/u3827/2011%20Collier-Understanding%20Process%20Tracing%20with%20Addendum.pdf>
- Hutchins, *Cognition in the Wild* — cognition distributed over people and
  representational artifacts: <https://mitpress.mit.edu/9780262082310/cognition-in-the-wild/>
- Hollnagel, Woods, and Leveson, *Resilience Engineering* — recovery and
  adaptive control as operational work: <https://www.routledge.com/Resilience-Engineering-Concepts-and-Precepts/Hollnagel-Woods-Leveson/p/book/9780754649045>
- Process Mining Manifesto — the event-log prerequisites and limits of
  process-mining interpretation: <https://www.tf-pm.org/resources/manifesto>
