# Verification Matrix

| ID | Claim | Required evidence |
| --- | --- | --- |
| MOD-01 | Model authority is explicit | Candidate map identifies one authority and rejects duplicate-schema designs |
| MOD-02 | Pydantic is introduced only where it improves a boundary | Pilot compares valid/invalid fixtures and shows no wire/behavior regression |
| MOD-03 | Canonical telemetry safety remains intact | Duplicate-key, bounds, canonical bytes, schema-v1, ZIP, and publication proofs remain green |
| TYP-01 | Type checker has a high-signal bounded adoption | Named scope starts with a known baseline and has no broad ignore escape hatch |
| TYP-02 | Type checker is operationally real | PDM command and CI invocation run from a frozen development environment |
| TYP-03 | Type evidence complements runtime evidence | A representative static defect and retained dynamic boundary cases demonstrate the division of labor |
| MOD-04 | No release regression | Focused checks, `pdm run test`, build/package, and affected acceptance pass |

## Selected-Slice Proof

1. `pdm run typecheck` checks only `config.py`, `agent_threads.py`,
   `navigation.py`, and `tui.py`, with no error baseline and no broad ignore.
2. `tests/test_config.py`, `tests/test_telemetry_navigation.py`, and
   `tests/test_telemetry_tui.py` preserve the affected runtime behavior.
3. `pdm run test`, `pdm build`, and `pdm run svc --help` prove the package and
   the existing command surface remain intact.
4. CI installs the locked `quality` group on Python 3.11 and invokes the same
   PDM script as local development.

## Result

All four selected proofs passed: `pdm run typecheck` reported zero errors;
the 28 focused tests and 208-test full suite passed; the lockfile, build, and
CLI smoke passed; and the CI workflow contains the dedicated locked
Python-3.11 typecheck job.
