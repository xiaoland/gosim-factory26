---
name: handsontable
description: Use when choosing or implementing Handsontable as an editable web data grid, especially selection, cell editing, keyboard and clipboard interaction, grid plugins, or its HyperFormula integration.
---

# Handsontable

Handsontable supplies a grid component, not a complete spreadsheet application. Use it only when its interaction model fits the requirements. The application still owns durable data, atomic changes, custom dialogs, business rules, and exact accessible names and states. Compare the installed version with the documentation before using an example.

Select the relevant reference rather than reading every example:

- [Data workflows](references/data-workflows.md): saving, import/export, validation, and undo UI.
- [Interaction plugins](references/interaction-plugins.md): menus, filtering, search, shortcuts, and layout.
- [Custom cells](references/custom-cells.md): renderers, editors, validators, and cell types.
- [Types](references/type-definitions.md): TypeScript API details.
- [Official documentation map](references/docs-map.md): current guides and API entry points.

When a feature changes selection, keyboard input, clipboard, or accessibility, verify the required browser behavior against the task's own criteria; the library defaults are not a substitute. [Handsontable requires an appropriate license key](https://handsontable.com/docs/javascript-data-grid/api/core/#licensekey), and its runtime license is separate from this skill's MIT license. For version-specific uncertainty, query the configured `handsontable-docs` MCP.

Use the configured documentation service for a specific API question:

```sh
mcporter call handsontable-docs.search_docs --args '{"query":"selection API in Handsontable 18","limit":3}' --no-oauth
mcporter list handsontable-docs --schema --json --no-oauth
```

When the installed version matters, add `ht_version` to the query arguments using the service's schema.
Preserve connection errors and use the official documentation when the service is unavailable.
