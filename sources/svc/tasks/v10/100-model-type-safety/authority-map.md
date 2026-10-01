# Telemetry Model Authority Map

## Keep the Current Manual Authority

| Boundary | Current authority | Why Pydantic must not replace it |
| --- | --- | --- |
| Native Codex JSONL input | Provider parser and normalizer | Unknown native shapes must be classified as loss/truncation, while duplicate keys, non-finite values, line/source limits, and source coordinates remain observable. |
| Canonical trajectory records | `trajectory.validate_record`, strict loader, and `TrajectoryCollector` | Exact key sets, fingerprints, cross-record order, canonical JSONL bytes, hashes, and incremental byte/record bounds are one combined contract. |
| Manifest and bundle | `validate_manifest`, `validate_bundle`, and ZIP writer | Schema-v1 pre-open refusal, member safety, cross-object count/lossiness relations, deterministic ZIP bytes, and publication safety are not a DTO parse. |
| Analysis output | `validate_analysis` and canonical analysis encoder | Evidence references, cross-bundle integrity, dimension membership, limits, and deterministic byte trimming exceed one object shape. |
| Filesystem/archive safety | provider snapshots and `archive.py` | Descriptor identity, reparse/symlink rejection, no-overwrite publication, and source races are operational authority, not data validation. |

## Retain Existing Pydantic and Dataclass Choices

| Boundary | Current authority | Decision |
| --- | --- | --- |
| Project config, probe and provision variants | Strict frozen Pydantic models with discriminated unions | Retain. This is a stable untrusted configuration boundary and already matches Pydantic v2's strengths. |
| Navigation/TUI/process-local state | Frozen stdlib dataclasses, enums, and protocols | Retain. These are in-process immutable values with behavior and privacy-oriented repr semantics, not JSON DTOs. |
| Thread/source selection and sensitive inventory row | Frozen dataclasses with degradation rules | Retain initially. Control-text-to-null, truncation, Path, and source-availability semantics are deliberate behavior, not simple field coercion. |

## Candidate Seams

| Candidate | Potential gain | Constraint / pilot shape |
| --- | --- | --- |
| Safe `ThreadDescriptor` CLI projection | A small fixed allowlisted DTO could make the public list response's type/extra-field policy explicit | Preserve `ThreadInventoryItem.as_descriptor()` as the projection authority; compare emitted JSON exactly; never include title, transcript, or source path. |
| Inventory query DTO | Pydantic can express enum + bounded integer constraints | Low gain: existing frozen dataclass is already clear and safe. Do not migrate only for tool uniformity. |
| Post-validation fixed envelope shadow validator | A `TypeAdapter`/model can independently check a fixed outer manifest, analysis, or `meta` record shape | Shadow only after current validation; never parse raw input, generate canonical output, or decide publication. Must prove zero mismatches before any behavior change. |
| Provider → archive and service payload seams | `TypedDict`/Protocol types can reduce `Mapping[str, object]` ambiguity without creating a second runtime schema | Prefer a type-only façade after a checker is selected. Runtime validator remains the authority. |
| Navigation/TUI async seam | Already typed frozen values make a good first type-check scope | Can establish a checker with lower risk than trajectory/provider security code. |

## Rejected First Moves

- Replacing every `Mapping[str, object]` with a Pydantic model.
- Making Pydantic JSON parsing the canonical trajectory/manifest parser.
- Pydantic-izing `SensitiveInventoryRow` before proving that its degradation
  semantics and redaction behavior are unchanged.
- Adding a broad static `TypedDict` hierarchy that mirrors the released wire
  schema without a clear type-only consumer.
