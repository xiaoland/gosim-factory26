---
name: agent-browser
description: Operate applications through a browser; run existing application checks with retained exit results and owned-process cleanup, with or without a temporary service.
---

Read `agent-browser skills get core` for the version-matched interface and workflows. Use `--help` or a specific bundled reference for unfamiliar commands.

Before the first browser interaction, choose a named session with `agent-browser session id --scope worktree --prefix task` and retain the returned name in your working notes. Pass that literal name on every command: `agent-browser --session <name> open <url>`, then `agent-browser --session <name> snapshot -i`. An `export` in one Bash tool call does not persist into the next call; do not fall back to an unnamed session there. Parallel browser tasks in the same worktree need distinct names or prefixes. Pass the name when handing off the same journey so the next agent can continue with the same page and login state. Close only the named session you own (`agent-browser --session <name> close`). In a shared run, do not use `close --all`, even if a general CLI example suggests it; setting a session name does not scope that global operation. Sessions belong to browser tasks, independently of agent identities; use native profile or CDP options when the task needs them.

Observe the current page, perform the requested interaction, then inspect the state that answers the question. DOM references expire after page changes. Use screenshots when appearance matters and the accessibility tree for controls and content. Preserve evidence paths and return only observations relevant to the delegated question. A successful click is not proof that the application persisted or applied the change. Use normal UI interactions for the behavior being checked; direct API or JavaScript state mutation is only an explicitly identified precondition or diagnostic action.

When running an existing browser, API or build check, or when you need to start and clean up its service, read [Application check execution](references/application-checks.md). It describes when the durable execution record is sufficient and when `scripts/with-service.py` is needed. Browser observations and evidence judgment above still apply.
