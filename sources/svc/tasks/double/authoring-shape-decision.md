# Double Authored-Shape Reuse Decision

## Decision

Do not add a second set of Pydantic models for authored `$bsl` YAML in v0.
Keep Pydantic discriminated unions as the normalized IR authority and keep the
existing source-aware compiler checks as the authored host-grammar authority.
This closes, rather than postpones, the authoring half of the tagged-model
reuse decision.

## Evidence

[`authoring_shape_probe.py`](spikes/reuse-convergence/authoring_shape_probe.py)
executes the production `TypeAdapter(Matcher)` and `TypeAdapter(ValueNode)` over
real ruamel-authored values. It proves:

- the strict IR enum requires a tuple and rejects an ordinary authored YAML
  sequence with `tuple_type`;
- because IR variants preserve fixed-null compatibility fields, an exact
  matcher containing authored `values` reports `none_required`, not the BSL
  unknown-key diagnostic;
- the IR range validator collapses an explicitly authored null bound into
  “requires minimum or maximum”, losing the v0 distinction that authored null
  is invalid;
- Pydantic `JsonValue` admits non-finite floats, so the SVC strict-JSON boundary
  remains necessary;
- authored value nodes use `match`, `validate`, `source`, and `media-type`, omit
  compiled `path`/location/snapshot fields, and have phase-dependent allowed
  keys. The IR adapter therefore reports simultaneous missing and extra fields;
- ruamel source coordinates remain mechanically available, but translating all
  the mismatched adapter errors back to the current codes/messages/paths would
  reproduce the existing host grammar in a diagnostic layer.

The earlier Pydantic probe correctly established that discriminated variants
are superior for IR and that a Pydantic error can be associated with a ruamel
key. It did not establish that the production IR model is also the authored
grammar or that a separate authoring model eliminates code. The production
probe supplies that missing comparison.

## Decision Table

| Candidate | Decision | Authority count | Diagnostic effect |
| --- | --- | ---: | --- |
| Production IR TypeAdapters directly over authored YAML | Reject | two, but incompatible | rejects valid YAML representation and misclassifies authored fields |
| Separate Pydantic authoring variants plus translation | Reject for v0 | three | duplicates phase/key semantics and still needs source-aware compiler policy |
| Current source-aware host grammar plus tagged IR | Keep | two intentional boundaries | preserves exact BSL diagnostics and makes compiled illegal states unrepresentable |

## Boundary

This is not a rejection of Pydantic or schema-driven authoring in general. A
future BSL version may define an authoring AST whose field names, collection
types, phase variants, and error contract are designed for direct validation.
That requires a versioned language decision, not a behavior-preserving refactor.

No product source, dependency, runtime behavior, grammar, fixture, or test case
changes in this decision stage.
