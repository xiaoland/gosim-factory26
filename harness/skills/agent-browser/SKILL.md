---
name: agent-browser
description: Operate the isolated application through a browser and gather relevant UI evidence.
---

Read `agent-browser skills get core` for the version-matched interface and workflows. Use `--help` or a specific bundled reference for unfamiliar commands. Factory automatically selects the browser session from the native session ID; do not override it or connect to a personal browser.

Observe the current page, perform the requested interaction, then inspect the state that answers the question. DOM references expire after page changes. Use screenshots when appearance matters and the accessibility tree for controls and content. Preserve evidence paths and return only observations relevant to the delegated question. A successful click is not proof that the application persisted or applied the change. Use normal UI interactions for the behavior being checked; direct API or JavaScript state mutation is only an explicitly identified precondition or diagnostic action.
