# Selection Policy

## Unit of Analysis

A selected item is one complete, exact Codex thread that represents a bounded
human–Agent collaboration episode. The archive is evidence, not an automatic
claim about the episode's quality or outcome.

## Staged Selection Rule

Start with safe selection metadata exposed by `svc telemetry agent-thread list`:
thread identifier, source state, timestamps, workspace/repository hints, and
any provider-supplied non-sensitive label. Use it to create a small,
cross-host candidate pool rather than to make the final choice.

An explicit episode identity supplied by the product owner, or already visible
in the active collaboration, may supplement those descriptors. It does not
authorize a raw rollout preview or a broader database query.

The product owner has now explicitly authorized a second, bounded triage stage:
the collector may inspect user-role message text from an exact, source-validated
candidate to determine whether it merits preservation. That review follows
[`review-protocol.md`](review-protocol.md). It must not inspect assistant,
system, developer, reasoning, tool, or attachment content; retain excerpts; or
use message text to fill a host quota.

If a confirmed SVC list-isolation defect prevents every descriptor because one
state row fails the path-containment guard, a read-only diagnostic may emit only
the same descriptor fields for rows independently proven to resolve inside
`CODEX_HOME`. It must not reveal paths, titles, CWDs, previews, message fields,
or any other DB column. This is a documented collection workaround; actual
capture still goes through `svc export` and never weakens containment.

## Coverage Matrix

Choose a minimal set that spans as many of these dimensions as the inventories
actually support:

| Dimension | Preferred contrast |
| --- | --- |
| Work phase | framing/decision, implementation, diagnosis/verification, release/retrospective |
| Human–Agent move | constraint or correction, proposal/review, delegated execution, evidence-based recovery |
| SVC surface | task packet, `dev ensure`, telemetry export, release/adoption, or an observed absence of useful support |
| Operating context | macOS, WSL/Linux, Windows; repository and worktree context where safely evidenced |
| Outcome signal | converged result, recovered failure, unresolved ambiguity, or handoff |

Priority episodes are SVC v10 design and release work, cross-platform dev-server
coordination, telemetry/export development, and real consumer-project work such
as the Anana environment when metadata proves the association.

## Exclusions and Caps

- Exclude an item whose provenance, workspace association, sensitivity risk, or
  reviewed user-message purpose cannot be understood well enough to justify
  retention.
- Exclude duplicate continuation snapshots unless they supply a distinct phase
  or host contrast.
- Prefer four to eight archives total; do not exceed three per host in this
  first corpus.
- Do not select merely because a thread is recent, long, or convenient.

## Selection Record

For each chosen archive, record outside the repository:

1. host and provider source state;
2. opaque thread identifier and safe timestamp/label;
3. repository association decision (`attached`, `omitted`, or reason);
4. two short coverage tags from the matrix;
5. a one-sentence non-quoting rationale derived from metadata and the permitted
   user-message review; and
6. a final decision: `retain`, `exclude`, or `needs-review`.
