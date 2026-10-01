# ROI Model

## Decision Rule

Migration is justified only when the retained benefit is larger than the
one-time conversion and recurring tool cost. The evaluation records evidence
rather than assigning invented point scores.

| Dimension | Benefit evidence | Cost / rejection signal |
| --- | --- | --- |
| Collection | pytest runs the current suite with no behavioral rewrite | collection differences, hidden test loss, or an unavoidable dual runner |
| Diagnostics | assertion output or fixture failure is materially easier to diagnose | only cosmetic output change for already-clear failures |
| Test support | a shared fixture, parametrisation, capture, or monkeypatch removes repeated setup/teardown or helper code | one-for-one syntax rewrite with no deleted support code |
| Async/TUI | native async support makes the real interaction test clearer without fragile event-loop plumbing | plugin/config complexity exceeds the one isolated async class's gain |
| Runtime | equal or lower median/full-suite runtime under the same environment | material slowdown or unstable collection/order |
| Operations | one PDM command and one CI lane remain simple | additional permanent tools, lock churn, or divergent local/CI behavior |
| Safety | the same negative filesystem/archive/redaction/wheel tests remain green | migration changes an oracle rather than its test framework |

## Selected Cut-Over Gate

1. **Reconciliation**: each original method has one historical migration
   ledger verdict; the later topology decision records retain, reshape,
   transfer, or delete by cost/value.
2. **Native surface**: every retained method becomes a pytest function; legacy
   framework imports and abstractions are absent.
3. **Behavior**: collection, full execution, static hard-cut gate, package,
   and installed-wheel evidence pass.

## Measured Ledger

| Option | Measured benefit | Measured cost / risk | ROI decision |
| --- | --- | --- | --- |
| Keep `unittest` | No new direct dependency or runner change. | Retains a non-standard runner surface and cannot use pytest selection and diagnostics as the project's single test interface. | Not preferred. |
| pytest runner, existing classes | `pytest 9.1.1` collected and passed all 208 methods without a source rewrite; it also reported 69 `subTest` cases. One standard command can serve local and CI use. | Add one bounded test dependency and update its lock/CI install sites. A paired probe was 14.84 s versus 12.78 s for `unittest`; later Textual-heavy samples varied, so no speed claim is justified. | Historical probe; superseded by the selected hard cut-over. |
| Full native hard cut-over | Removes the long-lived two-style test estate and makes native pytest fixtures, diagnostics, parametrisation, and async execution available everywhere. | 27 classes and 935 `self.assert*` calls require a careful semantic conversion; each case's expected defect-prevention value must clear its total cost. | **Selected by Sir; evaluate deletion ROI case by case.** |
| Add `pytest-asyncio` for the hard cut-over | Enables the existing native Textual async tests after `IsolatedAsyncioTestCase` is removed. | Adds an event-loop execution contract. Scope it to explicit marks and function-scoped tests. | **Required only for the existing TUI test family.** |

The timing column is deliberately not a gate requiring speed parity. The
dynamic suite includes actual Textual event-loop interaction, whose wall time
varies between runs. The evidence only rules out a claimed performance win.

## Simplification Boundary

The useful simplification is not `assert` spelling. It is removal of repeated
test support where a native facility replaces it:

- `tmp_path` may replace a local `TemporaryDirectory` scaffold when it removes
  cleanup and path conversion without hiding a filesystem boundary.
- `monkeypatch` or `caplog` may replace local patch/log cleanup only when the
  original failure mode remains visible.
- `@pytest.mark.parametrize` may replace a `subTest` matrix only when every
  row has the same setup, action, and oracle.

Black-box wheel, SQLite race, source-replacement, and real TUI tests retain
their lifecycle proof during conversion. Their implementation becomes native
pytest but their behavioral boundary is not simplified away.

## Non-Goals

- Treating fewer test methods as savings when subtests or parametrised cases
  still represent the same behavior.
- Replacing black-box installed-wheel evidence with fixture-heavy unit tests.
- Adding coverage percentages, plugins, or a second runner without a distinct
  consumer and verification path.
