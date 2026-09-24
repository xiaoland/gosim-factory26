---
name: agent-browser
description: Operate the isolated application through a browser and gather relevant UI evidence.
---

Read `agent-browser skills get core` for the version-matched interface and workflows. Use `--help` or a specific bundled reference for unfamiliar commands.

Use the default session for a single browser task. For parallel browser tasks, choose a distinct `--session <name>` for each task and reuse it on every command. Pass that name when handing browser work to another agent so it can continue with the same page and login state. Sessions belong to browser tasks, independently of agent identities; use native session, profile, or CDP options when the task needs them.

Observe the current page, perform the requested interaction, then inspect the state that answers the question. DOM references expire after page changes. Use screenshots when appearance matters and the accessibility tree for controls and content. Preserve evidence paths and return only observations relevant to the delegated question. A successful click is not proof that the application persisted or applied the change. Use normal UI interactions for the behavior being checked; direct API or JavaScript state mutation is only an explicitly identified precondition or diagnostic action.
