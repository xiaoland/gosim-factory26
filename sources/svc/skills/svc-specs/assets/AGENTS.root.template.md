# <Project Name>

<One sentence describing the product or repository.>

> Replace every angle-bracket placeholder. Delete any optional owner row that is not admitted; a completed root must contain no placeholder or `absent` marker.
> Put absolute paths or other machine-local information to `AGENTS.local.md` (under repository root).

## SVC Guidance

<!-- Replace these pointers with the actual adopted locations. The placeholders do not prescribe an installation layout; this entry must remain visible to the Agent during ordinary project work. -->

- Human authority covers Product intent, preferences, permissions, consequential trade-offs, and acceptance. Check factual and technical claims against evidence. Before durable mutation, establish the authorized effect, semantic owner, affected consumers and invariants, and proportionate verification.
- For every non-trivial Task, use `svc-task-packet` at `<adopted-svc-task-packet-entry-path>`. Recover an existing Packet before creating another, and keep task state sufficient to resume and verify completion.
- Load other adopted SVC Skills only when their pressure is present. Their use does not grant write, delegation, external-effect, or acceptance authority.

## Repository Map

- `<path>`: <crucial responsibility>
- `<path>`: <crucial responsibility>
- `docs/`: durable project knowledge
- `tasks/`: task packets

## Knowledge Owners

- Product what and why: `docs/prd/*`
- Cross-unit technical contracts, when admitted: `docs/product-tdd/*`
- Unit design and local seam guidance, when admitted: `docs/unit-tdd/*`
- Runtime, packaging, migration, observability, and recovery truth, when admitted: `docs/deployment/*`
- Nearer `AGENTS.md` files are additive for their subtree.
- `tasks/` are task packets, they are volatile.

## Development Workflow

- Runtime and package manager: <versions/tools>
- Common commands: `your install/test/lint/check/build/smoke commands`
- Runtime data: `<state, database, logs, cache, and config paths>` (refer to AGENTS.local.md if it's absolute path)
- Environment overrides: `<locations>`
