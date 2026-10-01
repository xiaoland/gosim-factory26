# Cross-Unit Technical Design

Cross-unit technical design preserves the agreement that independently responsible units need to cooperate safely.
A unit is a logical responsibility boundary, such as an editor, importer, storage component, service, or library; a directory boundary alone does not define one.
Use this responsibility when two or more units must agree on authority, topology, interfaces, lifecycle, ordering, compatibility, or failure behavior, and executable definitions do not preserve the important meaning clearly enough.
The benefit is that each unit can change its private implementation while retaining the shared behavior its consumers rely on.

## Describe Cooperation

Begin with the product claims and constraints the cooperation must realize.
Name the participating units, the state or decision each owns, and how data and control cross their boundary.
Describe who may create, change, read, or retire shared state and when it becomes usable by another unit.
Record relevant ordering, retries, idempotency, compatibility, and failure semantics rather than only naming calls and fields.
Explain the choice and the failure it prevents; distinguish an intentional constraint from an incidental implementation detail.

For example, an importer writes a configuration that the editor later opens.
A schema can constrain field names, but may not express whether omitted values preserve a user preference, reset to a default, or fail the import.
The shared definition must also say whether a failed import leaves prior configuration intact and when the editor may observe the new version.
Those meanings affect both units and belong in their common basis.
The importer's private parser structure does not belong there unless another unit must depend on it.

Use existing types, schemas, and executable constraints for field-level facts; reference their current source instead of duplicating a field catalog in prose.
Use a concise sequence or state diagram when it clarifies authority or ordering that prose leaves ambiguous.
Keep conditions, exceptions, and precedence together.
Equal names or compatible data shapes do not establish equal semantics.

## Maintain the Agreement

Keep one current definition and link dependent work to it.
Before consumers rely on a change, identify the affected units, the difference from the earlier agreement, and the version carrying it.
The publishing and adoption method in the skill entry applies: notification, implementation, and observed agreement are separate facts.
Update compatibility and failure assumptions when real feedback challenges them rather than accumulating private exceptions in each consumer.

Evidence must concern the agreement being claimed.
Two local checks can each succeed while a connected import-and-edit journey fails at the handoff.
Observe the meaningful cross-unit result and the relevant failure or overlap condition; do not infer interoperability from publication or compilation alone.
Use [verification design](../../svc-verification/references/check-design.md) when choosing such evidence requires deeper work.

Product purpose remains with [product documentation](product.md), private invariants with [internal design](internal-and-local.md), and rollout or restoration procedures with [operation](operations.md).
Use the [technical agreement template](../assets/templates/technical-design.template.md) when an independent document is useful; a current interface document may already be enough.
