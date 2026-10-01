# Migration Options

## A — Retain Manual Canonical Validators

Use for JSONL decoding, duplicate-key rejection, canonical byte generation,
schema-version rejection before member access, bounded incremental collection,
and archive publication. These operations combine streaming, provenance,
resource accounting, and exact wire behavior; a generic DTO parser would not
remove their authority.

## B — Add a Pydantic Boundary DTO Pilot

Consider only a bounded, inbound/outbound shape whose authority is currently a
large `Mapping[str, object]` projection and whose validity does not depend on
canonical byte order or incremental source state. The pilot must not require
the core validator to parse a Pydantic-produced dictionary as its only oracle.

Candidate selection requires evidence of all of the following:

- one clear input/output consumer
- explicit strictness and unknown-field policy
- no loss of source coordinates, bounds, or stable error codes
- no full duplicate of trajectory/manifest/analysis schema
- a measured reduction in ambiguous casts or duplicated checks

## C — Static Type Checker Pilot

Start with one named, sealed seam rather than `svc_cli` as a whole. The pilot
must define its checked paths, configuration, baseline error count, permitted
suppression policy, local command, CI invocation, and one defect class that the
tool catches. Pydantic runtime validation and static typing are complementary;
neither is a substitute for the other.

## Selected First Slice

Use mypy 2.3.x with Pydantic's supported `pydantic.mypy` plugin as the one
blocking checker. Its initial scope is exactly `svc_cli/config.py` and the
agent-thread navigation/TUI seam. It uses Python 3.11, checks unannotated
bodies, forbids implicit generic `Any`, and rejects unused ignores. No baseline
or per-module `ignore_errors` is permitted in the slice.

Pyrefly 1.1.1 was evaluated and agreed on the measured defects. It is not added
as a second permanent gate: one canonical type verdict is clearer, while its
newer, frequently changing 1.x diagnostic surface is useful later as an IDE or
non-blocking comparison.

The Pydantic migration decision is intentionally **no production telemetry
migration in this slice**. There is no DTO candidate that removes enough
ambiguity to justify a second schema surface. A future post-validation
`TypeAdapter` shadow comparison remains possible only if a fixed boundary gains
a concrete consumer and measurement.

## Rejected Shortcut

Do not replace every dataclass or every `Mapping[str, object]` with `BaseModel`.
That would add construction/serialization semantics and a second schema surface
without proving that it preserves the telemetry format's safety properties.
