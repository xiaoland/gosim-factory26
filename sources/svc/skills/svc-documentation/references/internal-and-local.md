# Internal Design and Development Instructions

Internal design preserves knowledge about one logical unit that is expensive to recover and should survive a refactor.
Development instructions help a contributor enter the repository or avoid a recurring hazard in a physical subtree.
These have different consumers and change conditions: a responsibility can move between directories, while nearby instructions apply to a concrete path.

## Preserve an Internal Invariant

Use internal design when the knowledge concerns one unit's state, storage, authority, sequencing, naming, or technology, can change without forcing another unit to change, and cannot be cheaply preserved by code or executable constraints alone.
Put a short rationale next to the relevant code when that is the cheapest usable location.
Create a unit design document only when the invariant spans implementation sites or has stable depth that a future maintainer must understand together.

State the invariant, the conditions over which it holds, its reason, and what would fail if it were removed.
Connect state transitions, ownership, and failure behavior to the actual symbols or sources.
Explain which alternative was rejected when that prevents a plausible future mistake.
Keep observations separate from intended guarantees; source code can contradict a design claim.

For example, one storage unit commits its journal before acknowledging a write so that an acknowledged operation can be recovered after restart.
The order and reason may remain important even if functions or directories change.
Keep that explanation with the storage design and use applicable recovery observations to judge it.
If another unit must depend on an acknowledgement's durability, put that external promise in the shared technical agreement; keep the private mechanism here.

Revisit the invariant when its state model or failure assumptions change.
Update its current definition and references to moved code rather than preserving obsolete paths as architecture.
Do not create a design document simply to describe obvious control flow or mirror every module.

## Give Contributors an Entry

A root AGENTS file or CONTRIBUTING guide should help a contributor find the product basis, technical responsibilities, operating instructions, task materials, and actual development commands.
Describe what each entry answers and which surface owns a recurring instruction.
Use executable configuration for versions and commands when it already provides the current basis; do not maintain an independently drifting copy.
Machine-specific paths or credentials do not belong in shared instructions.

Add local AGENTS guidance after diagnosing a repeated fragile seam, non-obvious authority path, or dangerous shortcut that nearby reminders can prevent.
Name its physical scope, the invariant or allowed entry, the shortcut and consequence, the recurrence signal, and useful feedback or escalation conditions.
For example, a subtree that maintains a generated index may need to direct edits to its source and regeneration command because manual edits are repeatedly lost.
An isolated mistake or a new directory does not by itself justify permanent local policy.

Keep local guidance narrow: reference root policy and the owning design instead of copying them or creating another architecture definition.
Remove a tripwire when the underlying mechanism now prevents the hazard or the guidance no longer applies.
Use the [local instructions template](../assets/templates/local-instructions.template.md) only when those conditions hold.
