---
name: exploration-tools
description: Choose the smallest local or remote exploration tool for a concrete information gap.
---

Start with the tool that answers the current question; switch or combine tools when the information gap requires it.

- Use `rg` for known text, filenames, symbols, and error messages.
- Use `ast-grep` for syntax structure, such as matching a call or expression across a language.
- Use Context7 for a known library's API, version, or official usage. Resolve the library when its identity is unknown; use an already established library ID directly.
- Use Exa when the source is unknown or cross-site discovery is needed. Fetch a known URL directly; otherwise search to locate a relevant primary source, then read it.

The main entry sets `MCPORTER_CONFIG` to `assets/mcporter.json` shipped with this skill. It contains only the public Context7 and Exa servers. For unattended calls, always pass `--no-oauth` and preserve the returned error when a service is unavailable.

Examples:

```sh
rg -n 'needle' path/
ast-grep run --pattern 'foo($$$ARGS)' --lang python path/
mcporter call context7.resolve-library-id --args '{"libraryName":"react","query":"official API documentation"}' --no-oauth
mcporter call context7.query-docs --args '{"libraryId":"/org/project","query":"specific API behavior"}' --no-oauth
mcporter call exa.web_search_exa --args '{"query":"official project documentation","objective":"find the primary source for this behavior"}' --no-oauth
mcporter call exa.web_fetch_exa --args '{"urls":["https://example.com/source"]}' --no-oauth
```

If a remote tool's arguments are unclear, inspect only that service's schema:

```sh
mcporter list context7 --schema --json --no-oauth
mcporter list exa --schema --json --no-oauth
```
