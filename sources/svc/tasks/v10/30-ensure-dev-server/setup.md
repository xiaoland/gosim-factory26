# Setup Integration Protocol

## One Command, Two Modes

```text
svc dev setup vscode [<target>] --plan
svc dev setup vscode [<target>] --apply <digest>

svc dev setup npm [<target>] --plan
svc dev setup npm [<target>] --apply <digest>
```

`vscode` and `npm` are explicit targets and never run together implicitly. Omitting `--plan`/`--apply` remains a read-only plan for compatibility, but documentation uses explicit `--plan`. Apply reconstructs the plan from current config and target bytes; it does not accept or execute a serialized external plan.

The plan digest binds the project/config schema, base and local declaration digests, selected profile/targets, setup projection version, normalized ordered operations, and every target file's before/after digest. Plan output contains no timestamp or randomness.

## VS Code Tasks

Setup may create `.vscode/tasks.json` when absent or surgically insert/refresh one generated task per selected target. The task uses a process invocation:

```json
{
  "label": "svc:dev:frontend",
  "type": "process",
  "command": "svc",
  "args": ["dev", "ensure", "frontend"],
  "problemMatcher": []
}
```

The generated object is bounded by JSONC comments carrying target identity and a body digest. A unique, clean marker may refresh; edited, malformed, duplicate, or ambiguous markers and reserved-label collisions block without modifying the file.

The editor must preserve comments, trailing commas, key order, line endings, formatting, and every unrelated byte. Whole-file parse-and-reserialize is not acceptable. Invalid JSONC, duplicate structural keys, a non-array `tasks`, symlinks, and non-UTF-8 content block.

`launch.json` is never read or written in this slice. Consumers may reference the stable task label through their own `preLaunchTask` configuration.

## `package.json` Scripts

`npm` denotes the npm-compatible `package.json` scripts projection, not an inferred npm runner. Setup reads only root `package.json`; it never scans workspaces or chooses npm/pnpm/yarn/bun.

The reserved key is `svc:dev:<target>` and its value invokes only the stable SVC target:

```json
{
  "scripts": {
    "svc:dev:frontend": "svc dev ensure frontend"
  }
}
```

Because the string contains only normalized SVC tokens and does not serialize the provisioner argv, it avoids consumer-command shell quoting. A missing reserved key may be inserted; an exact value is a no-op; a different value is a conflict and is never overwritten. Missing `package.json` blocks rather than creating package metadata.

Package edits are surgical and preserve every unrelated byte, key order, indentation, line ending, and file mode. Malformed JSON, duplicate keys, non-object `scripts`, symlinks, or non-UTF-8 content block.

## Ownership and Lifecycle

The containing files remain Consumer-owned. SVC owns only marked VS Code task objects and reserved exact script keys. Setup does not infer declarations from existing entries and does not automatically remove orphan entries when a target disappears; it reports them for explicit human cleanup.

All writes use the shared local plan engine: deterministic order, exact digest, preconditions, staged bytes, atomic commit, postconditions, full ordinary rollback, and preservation of an intervening Consumer edit.
