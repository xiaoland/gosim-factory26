# Type-Tool Evaluation

## Comparison

The same four-module Python 3.11 scope was measured in an external temporary
environment. Pyrefly 1.1.1's unconfigured basic preset reported no actionable
errors because that preset intentionally enables only a high-confidence subset.
Its default preset reported 17 errors. Mypy 2.3.0, using `pydantic.mypy`,
reported the same 17 errors.

This agreement is useful evidence that the selected scope contains ordinary
type-boundary defects rather than one checker's stylistic preference. It is not
evidence for a whole-repository gate.

## Decision

Mypy 2.3.x is the sole blocking tool for the first slice:

- it is an established gradual-typing tool;
- Pydantic v2 documents and supports its plugin;
- Python 3.11 is within the tool's supported range;
- it can be locked in PDM's development-only `quality` group; and
- the initial scope starts at zero errors without a baseline or suppression
  policy.

Pyrefly is not discarded: its built-in Pydantic support and matching findings
make it a good later IDE/non-blocking comparison. Its recent 1.x release line
and intentionally evolving diagnostics make it the wrong source of a second
authoritative CI verdict today.

The selected mypy command is implemented as `pdm run typecheck`; it is zero
error locally and is run in CI on Python 3.11 from the locked `quality` group.
Python 3.11 is intentionally both the configured target and CI interpreter: it
is SVC's lowest supported runtime, so the gate rejects use of newer-only syntax
or standard-library APIs. The existing test matrix remains responsible for
runtime behavior on newer interpreters.

## Pydantic Decision

Keep the existing strict, frozen, discriminated configuration models. Do not
replace telemetry's canonical parser, collector, archive, analysis validator,
or internal immutable dataclasses. Pydantic's duplicate-key collapse and
faux-immutability make that migration both unsafe and low-value.

The only future Pydantic candidate is a fixed, non-canonical boundary validated
in shadow mode after the existing authority. It is explicitly deferred until a
consumer demonstrates a measurable reduction in ambiguity.
