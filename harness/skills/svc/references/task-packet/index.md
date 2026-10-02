# Task Packet

A Task Packet stores the current state of one non-trivial task so an Agent can resume work after a context boundary.
For a task that needs more than one obvious action, create or resume `tasks/<task-id>/packet.md` directly.
The packet does not replace requirements, source code, or verification evidence.

Keep `packet.md` short enough to recover the outcome, constraints, current evidence, unresolved decisions, and next action without reading the whole task history.
Name the source of each material claim and link to supporting files when they exist.
Update the packet when a finding changes the route, a change is integrated, or evidence changes the completion judgment.
Do not create a child file merely because a template exists.

Use [Planning topology](planning.md) when independent work owners or a real shared barrier make one linear plan unclear.
Use [Information modules](information.md) when an inquiry, design, decision, or verification result needs a stable address.
Use [Growth guidance](growth.md) to split an existing packet without duplicating current truth.
Use the [template index](../../assets/templates/index.md) to choose a starting shape after its owner is needed.

At completion, leave the implemented source, checks, and task evidence in their appropriate locations.
The packet remains task state and need not become another project specification.
