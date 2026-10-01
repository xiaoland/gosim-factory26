# Two-Case Pilot Retrospective

## Exit Criteria

| Criterion | Result | Evidence |
| --- | --- | --- |
| Non-quoting, reproducible evidence pointers | passed | Both case cards use opaque case/episode labels, native ordinal spans, and record classes only |
| Native event, turn, episode, and case remain distinct | passed with an added discipline | Long cases require objective/control/outcome rationale for each episode; timestamps and completion events alone were insufficient |
| Each case records outcome or uncertainty | passed | Both have bounded locally or externally evidenced episodes and explicitly unknown/blocked outcomes |
| Attached packet is not treated as proof of use | passed | One case has an attachment with unresolved association; the contrasting case has no resolved attachment but still shows control artifacts in its permitted evidence |
| No premature cross-corpus claim | passed | All product implications remain within-case hypotheses |

## What the Pilot Changed

### 1. Completion Is Not Outcome

A runtime completion record, task-complete marker, successful local check, and
external acceptance are different evidence states. A terminal action can also
have no captured outcome. The protocol now needs an explicit status vocabulary
instead of letting a generic “complete” label overstate convergence.

### 2. Packets Are Control Artifacts, Not Truth Oracles

The pilot makes two asymmetric inference risks visible:

- attached packet material can be unresolved and cannot by itself establish
  currentness or use; and
- no resolved attachment can coexist with active planning/control artifacts.

The audit must therefore ask what packet state was observable at a decision,
not merely whether the exporter carried a packet member.

### 3. Long-Running Work Has Distinct Evidence Horizons

Local test/build or scenario evidence and externally observable system evidence
answer different questions. No-signal probes, unavailable host conditions, and
later independent review must remain explicit rather than silently degrading to
“pass” or “fail.”

### 4. Product Ownership Produces Candidate Questions

The two pilot cases generate candidate questions about SVC ownership around:

- mutation authority and safe handoff;
- machine-readable planned/in-progress/evidenced/blocked state;
- evidence ladders and unknown-status preservation; and
- concurrency ownership in shared mutable workspaces.

These are **candidate hypotheses**, not recurring patterns or approved SVC
gaps. The pilot does not establish causal benefit, cost, or case independence.
Consumer
provisioner semantics, project acceptance criteria, external accounts, and
provider/platform behavior remain outside SVC ownership.

## Protocol Revisions Before Scaling

1. Add an explicit outcome-evidence status to every case-card episode.
2. Add a packet-relation field that distinguishes attached, mentioned,
   unresolved, and not observed—not “used” versus “unused.”
3. Require a terminal-coverage check: if the archive ends with an action but
   no outcome record, record `unknown` and prohibit a success/failure claim.
4. Continue maximum-variation sampling: next cases must pressure-test recovery,
   medium-length non-coordination work, and short threads rather than only
   seeking more long, successful examples.

## Scaling Result

The planned maximum-variation wave is complete. See [case coverage and claim
status](coverage.md) for accepted cards and the next cross-case synthesis step.
