---
name: hyperformula
description: Use when choosing or implementing HyperFormula for formula evaluation, dependency recalculation, cell references, or spreadsheet structure changes in a JavaScript application. It is a headless engine, not a grid UI.
---

# HyperFormula

Use this when the application actually uses HyperFormula, or when deciding whether its calculation engine fits the required formula behavior. Keep the application's raw formulas, persistence, transaction rules, and specified error strings separate from the engine's calculated values. Check the installed package version before copying an API example.

Read only the reference that answers the present question:

- [Getting started](references/getting-started.md): instance and sheet setup.
- [API quick reference](references/api-quickref.md): edits, rows and columns, batching, events, undo, and clipboard.
- [Configuration](references/configuration.md): locale and calculation options.
- [Error handling](references/error-handling.md): typed errors and displayed values.
- [General pitfalls](references/general-pitfalls.md): lifecycle and compatibility limits.
- [Custom functions](references/custom-functions.md) and [Vue integration](references/vue3.md) only when those features are used.

The engine has [GPLv3 or commercial licensing](https://hyperformula.handsontable.com/docs/guide/licensing.html); choose the license appropriate to the application and configure its license key. The skill's MIT license does not license the application library. For a current API gap, query official HyperFormula documentation through the configured `handsontable-docs` MCP.

Use the configured documentation service for a specific API question:

```sh
mcporter call handsontable-docs.search_docs --args '{"query":"formula error handling in HyperFormula","limit":3}' --no-oauth
mcporter list handsontable-docs --schema --json --no-oauth
```

When the installed version matters, add `hf_version` to the query arguments using the service's schema.
Preserve connection errors and use the official documentation when the service is unavailable.
