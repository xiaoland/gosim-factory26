# Field-Study Observations

Populate this only after the product owner reviews the sensitive archives. Keep
raw excerpts and identifying content in the external evidence store, not here.

## Corpus Coverage

| Host | Episodes | Coverage tags | Known sampling bias |
| --- | --- | --- | --- |
| macOS | 3 | framework protocol; cross-host diagnosis; observability | Two infrastructure episodes and the SVC episode come from the same operator and may overrepresent highly directed work. |
| WSL/Linux | 2 | methodology; refactor execution; regression recovery | Both retained episodes concern substantial refactor work and may not generalize to operations or release collaboration. |
| Windows | 3 | component architecture; platform diagnosis; telemetry planning | Two focused research episodes are much shorter and older than the long component-library episode. |

## Collection-Level Findings (Not Behavioral Analysis)

- The corpus contains eight exact-thread snapshots, selected after a bounded
  review of user-intent messages only. Assistant behavior, reasoning, and tool
  records remain unreviewed at this stage, so no human–Agent pattern is
  asserted here.
- macOS associated task-packet material only where the SVC repository was
  evidenced. Every other capture deliberately avoided guessed repository
  association.
- All eight captures passed source-consistency checks; remote-to-local archive
  transfers were verified by matching SHA-256 and byte size.
- Windows metadata listing exposed a fail-closed per-row isolation gap; its
  narrow, read-only selection workaround is documented in `diagnostics.md`.
- The current success JSON receipt is richer than the safe collection
  inventory. Future collection tooling should make a minimal integrity receipt
  easy to request without suppressing the full receipt for diagnostic users.

## Candidate Pattern Record

For each possible pattern, distinguish observation from inference:

1. **Observed episode boundary**: opaque archive reference and phase tags.
2. **Human move / Agent move**: concise, non-quoting description.
3. **Evidence of outcome**: what is directly observable.
4. **SVC support or gap**: existing surface, missing affordance, or unresolved
   question.
5. **Cross-episode support**: independent examples, contradiction, or not yet
   established.
6. **Next validation**: smallest additional evidence or product experiment.
