# Minimal Sub-agent Capability and Landing

- **State**: accepted at capability-model depth in `D-088`
- **Consumer**: `SA × P1`
- **Inputs**: `D-083..D-087`, the corrected session dogfood, and the SA gleaning
  consumption audit

## Capability

Sub-agent use is a bounded work-placement decision: assign work to another
Agent only when attention partition, trajectory shaping, or capacity scaling
is expected to improve the Task enough to repay Assignment, Child-resource,
result-consumption/validation, integration, conflict, delay, and residual-error
cost against the best direct alternative.

The three levers are evaluation dimensions, not role categories. A useful
invocation states which scarce quantity is expected to improve; it does not
need a formula or mandatory form.

## Minimal Operating Model

1. Compare Primary direct work, progressive loading, a deterministic mechanism,
   another Agent, and Human-only judgment where applicable.
2. Bound one independently useful Assignment around a known consumer and
   effect surface; fit it to the Child's actual model/context/tool capacity.
3. Let the Child progressively load canonical shared guidance; pass only the
   Task delta, material handles, snapshot/freshness boundary, and non-obvious
   constraints.
4. Choose the result route from the consumer: report or candidate/effect.
5. Keep global Task, Human, cross-Assignment, conflict, and material residual
   authority with the Primary. Use one writer for a mutable target unless an
   explicit merge boundary exists.

## Two Preset Profiles

Only two profiles have a recurring boundary strong enough for the first
landing. They are reusable work contracts, not personalities, phases, or
exclusive Working Methods.

### Explorer

- **Use when**: a bounded, consumer-relevant information/owner/constraint
  question has non-obvious evidence paths or enough local noise that isolating
  its retrieval trajectory is cheaper than Primary direct Explore.
- **Method relation**: composes Explore and its embedded Model/Generate/
  Discriminate logic; profile text owns only delegation-specific scope,
  read-only default, report compression, freshness, and failure behavior.
- **Result**: a question-shaped report to the semantic consumer. No generic
  validator. Do not return a transcript, mutate Task/durable truth, or make the
  downstream decision.
- **Stop/escalate**: return bounded-incomplete when evidence is unavailable or
  not worth acquiring; request a smaller missing input when scope cannot be
  honored; stop when the question turns into global design, authority, or
  acceptance.

### Executor

- **Use when**: one bounded intended change has a clear effect surface and a
  low-latency, task-specific feedback mechanism, while the remaining work is
  not better expressed as a deterministic transform.
- **Method relation**: primarily composes the Implementation development loop;
  it may locally Explore or Design when feedback exposes a mismatch.
- **Result**: the actual patch/configuration/artifact plus support in the
  assigned carrier; an appropriate independent validator and effect gate
  qualify entry into shared state. Primary normally receives status, not a
  work report.
- **Stop/escalate**: repair locally within the budget; escalate a small design,
  authority, product-taste, or effect-boundary mismatch. Human-perceptual loops
  prepare replay/candidates but do not appropriate Human acceptance.

No default Reviewer, validator Agent, doc writer, rule resolver, Task Packet
manager, or generic QA profile is admitted. A validator is a trusted mechanism
for a bounded claim; an Agent can execute a verification plan without becoming
trusted by role.

## Rough Landing

- Add one compact `src/sections/sub-agents.md` owner containing the economic
  decision, authority/context rules, result-route distinction, and the two
  short profiles.
- Let the target Working Protocol link to that owner conditionally; do not copy
  profile detail into the kernel.
- Keep concrete `rg`, AST, graph, structured-data, runtime, remote-probe, and
  transformation instructions in project guidance or on-demand skills.
- Do not add CLI orchestration, a profile directory, Assignment schema,
  mandatory team topology, nested-agent protocol, or Task Packet module. Split
  profile files only after retrieval or maintenance pressure appears.

## Unknowns and Reopen Conditions

Real tasks have not yet demonstrated net trajectory-shaping or capacity-
scaling value. Reopen if report reading repeatedly recreates raw evidence load,
Executor validators dominate cost, shared-worktree conflicts recur, the two
profiles collapse into generic method guidance, or another work boundary shows
repeated consumer/return/qualification economics that these profiles cannot
express.
