# Baseline Evidence and Test-Family Classification

> Historical baseline. Its 213/208 case counts and non-subsumption decisions
> are superseded for ROI purposes by [`roi-reassessment.md`](roi-reassessment.md).

## Measurement Boundary

The authority for the current suite is `pdm run test`, which completed 213
tests in the project environment. The method count comes from `test_*` method
declarations; it is a navigation metric, not coverage or quality evidence.

| Scope | Test lines | Test methods | Observation |
| --- | ---: | ---: | --- |
| all `tests/test_*.py` | 7,409 | 213 | Current repository suite |
| telemetry tests | 3,944 | 105 | Provider, trajectory, archive, analysis, CLI, navigation, TUI |
| installed-wheel harness tests | 1,210 | 18 | Standard-library harness and fake-executable tests |
| telemetry plus harness | 5,154 | 123 | 70% of test lines; highest-priority topology audit area |

The corresponding telemetry runtime is 7,361 lines. Size alone does not prove
over-testing: it is a cross-platform boundary involving SQLite, local files,
ZIP archives, JSONL, sensitive data, and TUI state. The relevant question is
whether each test family protects a distinct plausible defect.

The earlier 97/115 method counts were a stale declaration-based estimate. The
correct count was obtained from the same PDM environment with
`unittest.TestLoader().discover(...)` per file, and reconciles with the
authoritative 213 cases from `pdm run test`. The ledger uses those counts only
for navigation; neither count nor line total is a quality target.

## Evidence of Overlap or Coupling

| Family | Evidence | Why it is a topology concern | Candidate direction |
| --- | --- | --- | --- |
| Codex source normalization | [`test_telemetry_codex_rollout.py`](../../../tests/test_telemetry_codex_rollout.py) and [`test_telemetry_codex_trajectory.py`](../../../tests/test_telemetry_codex_trajectory.py) each exercise explicit source → meta/message/tool records, result-before-call, and record limits | The same input/output story is asserted at multiple adjacent layers | Retain one adapter mapping contract and one streaming/identity contract; share fixture data or parameterize distinct variants |
| Acceptance bundle/analysis fixtures | [`tools/accept_agent_thread.py`](../../../tools/accept_agent_thread.py) declares independent record, manifest, loss, bound, and analysis structures; [`test_accept_agent_thread.py`](../../../tests/test_accept_agent_thread.py) manually constructs another large fake bundle/analysis response | The harness must be black-box, but it is becoming a second schema implementation | Let core validation own deep record/manifest legality; keep harness assertions to installed-wheel behavior, a small frozen synthetic golden, package isolation, and safety-critical output properties |
| Harness slice execution | Four slice smoke tests and the `all` path repeat wheel/venv/command/cleanup scaffolding | Repetition obscures the one distinct property per slice and raises change cost | Extract test support and use a table-driven slice matrix; retain dedicated tests only for distinct error/cleanup paths |
| Private-helper/UI coupling | Provider/archive tests call private helpers; TUI tests inspect private state and concrete widget IDs | A behavior-preserving refactor can fail despite the public contract remaining intact | Preserve direct tests for security/atomicity primitives; move other tests toward public render models, CLI surfaces, and observable screen state |
| Source-text assertions | Navigation tests use source-string absence checks alongside AST-oriented checks | String checks are brittle and do not establish the intended structural invariant | Use one AST/import/dependency-boundary rule with deliberate positive and negative fixtures |
| Capacity checks | Navigation and TUI both prove portions of the 5,000-row/lazy-loading contract | The pure cap and the user-facing lazy interaction are separate, but currently overlap | Keep the cap/unit proof in navigation and one end-to-end TUI smoke for lazy expansion and selection |

## High-Value Dynamic Contracts to Preserve

These are not candidates for replacement by static checks:

- deterministic ZIP/trajectory construction, restrictive publication mode,
  no-overwrite, no publication after provider errors, and schema-v1 bounded
  rejection
- SQLite metadata-only safe projection, bounded sensitive projection, unsafe
  path/reparse handling, descriptor identity, and source-race behavior
- sensitive acknowledgement, public error redaction, direct-vs-bundle analysis
  equivalence, and no Textual import on JSON paths
- installed-wheel SHA/wheelhouse isolation, cleanup, package leakage rejection,
  and platform-specific venv execution
- TUI selection generation, stale-load rejection, key handling, and terminal
  restoration

## Static-Gate Opportunity

No `mypy`, `pyright`, `ruff`, or comparable configured static gate appears in
the current `pyproject.toml`/PDM script surface. Static checks could own:

- type/protocol consistency across provider, trajectory, analysis, navigation,
  and service seams
- import and dependency boundaries, especially render-neutral JSON paths
- structural prohibitions now expressed as source-text searches
- ordinary formatting, unused imports, and accidental unreachable branches

They cannot prove the high-value dynamic contracts above. Tool selection is
deliberately deferred until the first slice studies repository fit, package
cost, Python version support, and a representative defect set.

## Slice 1A Execution Evidence

The first implementation deliberately changed only
`tests/test_accept_agent_thread.py`:

- Four individual successful-slice methods became one four-subtest matrix.
  Every slice retains its unique check: inventory SHA report; bundle report
  redaction; analysis installed-Textual/response redaction; and UI response
  redaction.
- The aggregate `all` command-order test remains separate, but shares the same
  fake isolated-run setup. Negative bundle/schema, install, venv, case, and
  cleanup tests remain unchanged.
- Focused command: `pdm run python -m unittest discover -s tests -p
  'test_accept_agent_thread.py'` → 15 passing tests.
- Full command: `pdm run test` → 210 passing tests in 13.824 seconds.

The pre-slice baseline was 213 cases. The three-case numerical difference is
an incidental result of replacing four methods with one test containing four
named subtests; it is not a completion target or a claim that four behaviors
were reduced to one.

## Slice 2 Execution Evidence

The second implementation changed only the two adjacent Codex test suites:

- `test_telemetry_codex_rollout.py` now owns native source field-path mapping:
  workspace, message, reasoning, tool-call, and linked tool-result fields.
- `test_telemetry_codex_trajectory.py` now owns canonical stream order,
  record/source identities, orphan-result determinism, and record-limit
  diagnostics.
- Deleted rollout tests were strict subsets of the retained stream proofs:
  result-before-call only asserted `unresolved`, and sink rejection only
  asserted count/partial. The retained tests additionally prove deterministic
  tool identities or exact record-limit diagnostics.
- Source replacement and append-after-open remain distinct physical versus
  stream-growth faults; neither changed.
- Focused commands: retained mapping 1/1; retained stream cases 3/3; both
  Codex modules 41/41. Full command: `pdm run test` → 208 passing tests in
  14.804 seconds.

The second two-case numerical change follows the documented replacement
relationship. It is not a target, and no runtime contract changed.
