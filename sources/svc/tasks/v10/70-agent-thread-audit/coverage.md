# Case Coverage and Claim Status

This tracker records audit coverage, not outcome quality. “Accepted” means the
case card met privacy, pointer, and uncertainty requirements; it does not mean
the audited work was successful.

| Opaque case | Structural role | Audit state | Intended pressure test |
| --- | --- | --- | --- |
| `SVC-A` | long, attached-packet, coordination metadata | accepted pilot | packet association and terminal outcome coverage |
| `OPS-B` | long, no resolved attachment, coordination metadata | accepted pilot | long-cycle control state, recovery, and external evidence horizon |
| `REC-E` | long, no resolved attachment, coordination metadata | accepted | recovery-oriented long case |
| `NET-C` | medium, no coordination metadata | accepted | medium-scale non-coordination work |
| `WIN-G` | short, no compaction/coordination metadata | accepted | minimum viable episode and short-thread limits |
| `DIAG-D` | medium, no coordination metadata | accepted | alternate medium diagnostic case / negative-case search |
| `WIN-F` | long, no coordination metadata | accepted | long non-coordination and platform contrast |
| `WIN-H` | short, compaction but no coordination metadata | accepted | short-thread compaction contrast |

## Claim Discipline

- A case card can support observations and within-case inferences.
- A recurring pattern requires at least two independent supporting cases plus a
  recorded counterexample/boundary search.
- An SVC gap additionally requires a reusable owner, smallest intervention,
  and measurable validation. No accepted card has reached that status yet.
