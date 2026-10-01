# Baseline Evidence

## Confirmed Local Facts

| Surface | Current authority | Evidence |
| --- | --- | --- |
| Project configuration | Pydantic v2 strict frozen models | `svc_cli/config.py` uses `BaseModel`, `ConfigDict(extra="forbid", strict=True, frozen=True)`, `Field`, validators, and discriminated unions |
| Telemetry domain seams | Frozen dataclasses, enums, and protocols | `svc_cli/telemetry/agent_threads.py`, `navigation.py`, `tui.py`, and selected trajectory/analysis result types |
| Telemetry wire validation | Hand-written structural/canonical validators over `Mapping[str, object]` | `trajectory.py` and `analysis.py` validate keys, references, JSON semantics, bounds, and canonical bytes |
| Static type checking (pre-slice) | None | No `mypy`, `pyrefly`, `pyright`, or configured command in `pyproject.toml`; none was installed in the project environment |

The project's Pydantic dependency is `pydantic<3,>=2.13`. That proves only
availability, not that Pydantic is the right authority for every runtime model.

## Local Boundary Probe

Using the installed Pydantic 2.13.4, a strict `BaseModel` accepted
`b'{"x":1,"x":2}'` as `x=2`; `pydantic_core.from_json` likewise returned
`{"x": 2}`. JSON duplicate keys have already collapsed before
`extra="forbid"` can act. This is incompatible with telemetry's explicit
duplicate-key rejection and is decisive evidence against replacing its raw
JSON parser with `model_validate_json`.

`frozen=True` is also only faux immutability: it blocks field assignment but
does not deep-freeze contained lists or dictionaries. Existing Pydantic config
models remain appropriate boundary snapshots, but this setting is not a reason
to migrate telemetry's immutable value objects.

## Static-Checker Evaluation

Both candidates were installed only in an external temporary environment and
run against the project's Python 3.11 virtual environment; no dependency or
configuration was changed during measurement.

| Tool / mode | Result | Interpretation |
| --- | --- | --- |
| Pyrefly 1.1.1 basic preset | 0 errors, 2 suppressed | Deliberately high-confidence-only default; insufficient as a gate. |
| Pyrefly 1.1.1 default preset | 17 errors, 2 suppressed | Finds concrete boundary errors but is a newly production-ready 1.x tool with a fast-moving error surface. |
| mypy 2.3.0 + `pydantic.mypy` | 17 errors | Finds the same defects under Python 3.11 with `check_untyped_defs`, `warn_unused_ignores`, and `disallow_any_generics`. |

The checked files were `svc_cli/config.py`,
`svc_cli/telemetry/agent_threads.py`, `navigation.py`, and `tui.py`. The
defects split into three independently understandable classes:

- normalized string-or-enum input was later treated as an enum without a
  statically visible normalization boundary;
- an untyped `**kwargs` bridge erased the mutable navigation node's contract;
- Textual worker results and optional loaders crossed an async boundary as
  `Any | None`, despite runtime validation.

Mypy also found two real variance mismatches in the existing Pydantic config
name validator and one unmodelled object-to-dictionary merge invariant. These
are all behavior-preserving annotation/guard refinements, not a model rewrite.

## Implemented-Slice Result

The selected mypy scope is now zero-error under the locked project environment.
The affected configuration, navigation, and TUI tests passed (28 tests); the
full repository suite passed 208 tests. `pdm lock --check`, `pdm build`, and
`pdm run svc --help` also passed. CI runs the identical PDM script in a
dedicated Python 3.11 job.

## Questions to Resolve

1. Which telemetry inputs are untrusted DTO boundaries rather than canonical
   wire-format authorities?
2. Can Pydantic validate those DTOs without changing error-code, byte-bound,
   canonicalization, or streaming behavior?
3. Can a type checker begin with a sealed, already annotated seam and uncover
   plausible defects without blanket ignores?
4. Which tool's runtime, Pydantic support, and CI model fit Python 3.11+ and
   PDM's frozen dependency workflow?
