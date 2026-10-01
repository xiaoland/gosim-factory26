# Project and Local Configuration

## Two-Layer Contract

`svc.json` is the complete, committed base document. Its root `schema_version` selects the schema used for both files. `svc.local.json` is an optional sparse overlay for machine-, execution-environment-, credential-, or worktree-specific configuration. It is a partial form of the complete project configuration, not a `dev`-specific document.

The overlay schema is derived from the base schema:

- every field marked locally overrideable becomes optional;
- `schema_version`, `svc_version`, and any future schema/adoption authority field are excluded;
- fixed objects reject unknown keys; explicit dynamic maps such as profile and target names validate their values;
- `svc.local.json` containing `schema_version` or a non-overrideable path is invalid rather than silently ignored.

Resolution is deterministic:

```text
parse and validate complete svc.json
  -> parse and validate sparse svc.local.json when present
  -> recursively merge objects
       missing local key = inherit base
       scalar or array    = replace atomically
       object             = merge recursively
  -> validate the complete effective document
```

The first schema does not define deletion or a `null` tombstone. Removing a local key restores the base value. If deletion becomes necessary, it receives a separate schema rule rather than an ad-hoc sentinel.

`dev.profile` is the only selected-profile location. A top-level `profile` is invalid. The base may define portable profiles and targets; the local overlay may select or refine any schema-declared local field. The effective config is an in-memory projection and is never written back to either source.

Strict external validation is owned by Pydantic v2 models with coercion disabled, unknown fixed-object fields forbidden, and discriminated probe/provision unions. A small stdlib JSON loader still rejects duplicate keys and non-finite values before Pydantic sees a Python object. Overlay authority and merge semantics remain explicit SVC protocol code rather than a generic deep-merge library.

## Initial Schema Boundary

`schema_version`, `svc_version`, and `dev` are the only root fields. `dev` is optional so projects that use only the packaged corpus remain valid. When present, `dev.profile` and `dev.profiles` are required, the selected profile must exist, and each profile contains an explicit dynamic `targets` map.

Each target has:

- `scope`: `worktree` by default, or explicit `repository`/`host`; host scope also requires a stable `host_key`;
- one discriminated `probe`: `http`, `tcp`, or `exec`;
- one discriminated `provision`: `exec` in `run`/`activate` mode, or `manual`;
- optional access URLs plus bounded readiness timeout/poll interval;
- exact argv arrays, optional working directories, and explicit environment overrides where applicable.

HTTP probes use bounded `GET` by default, no redirects, strict TLS, an explicit accepted status interval, and loopback-only network scope unless the consumer opts into remote addresses. TCP probes declare host, port, network scope, and timeout. Exec probes declare exact argv, working directory, timeout, and an output limit. No SVC-created shell or undeclared environment interpolation exists.

Worktree-scoped targets must make expected instance provenance observable through a `${dev.instance}` token in the resolved probe identity. The first delivery does not invent a generic response-expression language; consumers needing custom provenance can use an exact exec probe. Repository- and host-scoped targets deliberately do not require worktree instance proof.

## Illustrative Shape

```json
{
  "schema_version": 2,
  "svc_version": "10.0.1",
  "dev": {
    "profile": "worktree",
    "profiles": {
      "worktree": {
        "targets": {
          "frontend": {
            "scope": "worktree",
            "probe": {
              "kind": "http",
              "url": "https://frontend-${dev.instance}.localhost/health",
              "success_status": [200, 399]
            },
            "provision": {
              "kind": "exec",
              "mode": "run",
              "cwd": ".",
              "argv": ["portless", "--name", "frontend-${dev.instance}", "--", "pnpm", "dev"]
            },
            "access": ["https://frontend-${dev.instance}.localhost/"]
          }
        }
      }
    }
  }
}
```

The example uses consumer-owned `portless`; it is not a built-in adapter or dependency.

## Init and Ignore Boundary

`svc init` plan/apply-maintains this exact generated projection inside root `.gitignore`:

```text
# svc:begin local-config sha256=<digest>
svc.local.json
# svc:end local-config
```

Missing `.gitignore` is created; otherwise the section is appended while every unmarked byte is preserved. One current section is a no-op. A malformed, duplicate, or digest-modified section blocks. `svc init` does not create, read-modify-write, chmod, or delete `svc.local.json`.

An existing unmarked `svc.local.json` ignore rule is Consumer-owned. Init retains it byte-for-byte and appends the marked section despite semantic duplication; it never removes or silently adopts the Consumer line. This keeps the generated contract mechanically inspectable without turning an already-correct ignore rule into a blocker.

## Status and Upgrade

`svc status` reports base schema validity, local presence/validity, effective config validity, and managed-ignore status without disclosing configuration values. Invalid local configuration makes status unhealthy; SVC never silently falls back to base values.

The published v10.0.0 schema is minimal v1. The expanded document becomes schema v2. Under the product owner's one-time zero-known-adopted-consumer exception, 10.0.1 provides no automatic v1 migration: an existing v1 or future schema blocks writes and is reported explicitly. `svc adopt` changes only the `svc_version` string span of a valid current-schema base and preserves all unrelated bytes; it never erases `dev` configuration or silently performs a project-schema migration.
