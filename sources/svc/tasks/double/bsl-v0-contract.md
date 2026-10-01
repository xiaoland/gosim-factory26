# BSL v0 Concrete Authoring Contract

Status: final pre-implementation candidate. It refines the semantic boundary in
[`design-v2.md`](design-v2.md); it does not authorize source mutation.

## Module Shape

The YAML surface is one strict document with these exact top-level keys:

```yaml
language: svc.double/v0
scenario: {}
```

`language` is exactly `svc.double/v0`. `scenario` has:

| Key | Required | Meaning |
| --- | :---: | --- |
| `name` | yes | Stable module-local identifier matching `[a-z][a-z0-9.-]*` |
| `claim` | yes | Non-empty Consumer-visible behavior the real Consumer test will assert |
| `boundary` | yes | One HTTP provider boundary and optional selected contract operation |
| `policy` | no | Only event-target network policy in v0 |
| `interactions` | yes | Non-empty ordered authoring list; runtime selection is by matching, never list order |
| `events` | no | Named explicit inbound stimuli |

Unknown keys fail. The module has no imports, parameters, provider entities,
states, completion condition, product assertion, timer, retry, or automatic
event transition.

## Representative Module

```yaml
language: svc.double/v0

scenario:
  name: payment-confirmed
  claim: consumer exposes a paid order after an accepted provider event
  boundary:
    name: payment-provider
    protocol: http
    contract:
      kind: openapi-3.1-operation
      source: contracts/payment.openapi.yaml
      method: POST
      path: /v1/payments
  policy:
    event-targets: loopback-only

  interactions:
    - name: create-payment
      provenance:
        kind: provider-contract
        source: contracts/payment.openapi.yaml#/paths/~1v1~1payments/post
      request:
        method: POST
        path: /v1/payments
        headers:
          content-type: application/json
        body:
          structured:
            externalId:
              $bsl:
                kind: capture
                name: external_id
                example: 00000000-0000-4000-8000-000000000001
                match:
                  kind: semantic
                  semantic: rfc.uuid
                  using: svc.rfc-uuid/v1
      response:
        status: 201
        headers:
          content-type: application/json
        body:
          structured:
            paymentId:
              $bsl:
                kind: generated
                semantic: opaque-token
                using: svc.opaque-token/v1
                options:
                  alphabet: lower-alphanumeric
                  length: 24
                bind: payment_id
                validate:
                  kind: regex
                  pattern: '^[a-z0-9]{24}$'

  events:
    - name: payment.succeeded
      target: consumer.payment-events
      provenance:
        kind: provider-documentation
        source: https://provider.example/docs/payment-events
      request:
        method: POST
        path: /webhooks/payment
        headers:
          content-type: application/json
        body:
          structured:
            externalId:
              $bsl:
                kind: derived
                expression: bindings.external_id
                validate:
                  kind: semantic
                  semantic: rfc.uuid
                  using: svc.rfc-uuid/v1
            paymentId:
              $bsl:
                kind: derived
                expression: bindings.payment_id
                validate:
                  kind: regex
                  pattern: '^[a-z0-9]{24}$'
```

The start binding is an origin, not the event path:

```text
--target consumer.payment-events=http://127.0.0.1:9010
```

## Boundary and Contract

`boundary` requires `name` and `protocol: http`. Optional `contract` has exactly
`kind`, `source`, `method`, and `path`:

- `kind` is `openapi-3.1-operation`;
- `source` is a local path resolved from the module directory and contained by
  the selected workspace;
- `method` is an uppercase HTTP method token;
- `path` is an exact static OpenAPI path beginning with `/` and contains no
  template parameter.

When present, every interaction uses that exact method/path. The compiler
snapshots the document and admitted local references, validates every
materialized structured request/response against the selected schemas, and
reports the narrower `selected-operation-schema` fact.

## Provenance

Every interaction and event has exactly one `provenance` object:

```text
kind := consumer-requirement | provider-contract | provider-documentation
      | provider-capture | synthetic
source := non-empty local reference or external reference string
```

Local sources are snapshotted and hashed. External references are never
retrieved or treated as provider-currentness proof. `provider-capture` also
requires `sanitized: true`; SVC records that declaration but does not make a
privacy claim. The compiler derives mechanical fidelity/non-fidelity facts from
the used features. There is no open-ended authored `fidelity.claims` list.

## Requests, Responses, and Events

An interaction request requires `method` and `path` and may declare `query`,
`headers`, and one `body`. A response requires `status` and may declare
`headers` and one `body`. An event requires unique `name`, symbolic `target`,
`provenance`, and a request.

Body modes are mutually exclusive:

```yaml
body:
  structured: <JSON-shaped BSL value>
```

or:

```yaml
body:
  raw:
    $bsl:
      kind: managed
      source: fixtures/provider-event.bin
      media-type: application/octet-stream
```

Interaction requests may instead declare a strict form field map:

```yaml
body:
  form-urlencoded:
    ext_order_id:
      $bsl:
        kind: capture
        name: external_order_id
        match: {kind: regex, pattern: '^[0-9a-f-]{36}$'}
```

`form-urlencoded` is request-only. Its field values follow the query string
surface (strings, typed string values, or arrays for repeated fields). Runtime
parsing requires UTF-8 `name=value` pairs, strict percent encoding, and an exact
declared field-name set; `+` decodes to space and ordering is insignificant.
It adds no provider state and is not an OpenAPI JSON request schema claim.

Structured bodies use deterministic `json.compact-utf8/v1`: UTF-8, no BOM,
compact separators, preserved array order, and no non-finite numbers. JSON
objects reject duplicate keys and request matching requires the same key set by
default. Raw bodies preserve the snapshotted bytes exactly.

Header names are case-insensitive; header values are exact unless typed with a
matcher. A v0 map cannot express duplicate response header fields. Query values
are a scalar or an array of values; arrays express repeated values. Parsing is a
strict decoded name/value multimap and does not treat ordering as significant.

## Local Typed Nodes

An object with sole key `$bsl` is a typed value. The allowed kinds and phases
are:

| Kind | Request | Response/event | Effect |
| --- | :---: | :---: | --- |
| `literal` | yes | yes | Escapes a provider value that structurally collides with `$bsl` |
| `match` | yes | no | Matches without binding |
| `capture` | yes | no | Matches and binds the observed value once |
| `example` | no | yes | Materializes a declared inline example |
| `derived` | no | yes | Evaluates one restricted CEL expression |
| `generated` | no | yes | Materializes one closed-registry value once per run |
| `managed` | yes | yes | Reads snapshotted local bytes or structured JSON; request use is exact matching |

Ordinary request values are exact matchers. Ordinary response/event values are
constant output. An optional `example` within `match` or `capture` is authoring
material only and never changes matching.

`capture.name` and optional output `bind` use `[a-z][a-z0-9_]*` and publish one
immutable value under `bindings.<name>`. Equal retry capture is accepted;
conflict is a visible runtime failure. Compilation proves a binding is
available before a derived expression can read it.

## Matcher and Validator Algebra

Request `match` and output `validate` share one closed algebra but have different
effects:

```text
exact | enum | range | regex | semantic
```

- `exact` carries one JSON value;
- `enum` carries a non-empty same-type value list;
- `range` carries admitted inclusive numeric bounds;
- `regex` carries one CEL/RE2-profile pattern and applies only to strings;
- `semantic` carries a closed semantic identifier plus exact validator ID.

V0 semantic validators are limited to the semantics of the closed generator
registry, initially `svc.rfc-uuid/v1` and `svc.rfc3339/v1`. A matcher selects
traffic; a validator rejects materialized output before emission. Neither
asserts Consumer product behavior.

## Derived and Generated Values

`derived` requires `expression` and `validate`. It may optionally `bind`. The
CEL environment contains only typed `request`, `bindings`, `run`, and
`scenario`; no guard position is admitted in v0.

`generated` requires `semantic`, `using`, and `validate`; generator-specific
`options` are strict and it may optionally `bind`. The closed registry is:

- `svc.uuid-v4/v1`;
- `svc.opaque-token/v1` with declared alphabet and length;
- `svc.bounded-integer/v1`;
- `svc.enum-choice/v1`;
- `svc.fixed-clock-rfc3339/v1`.

Generated values are arranged once per run from the reported seed/fixed clock.
Field names never select generators. Project/provider IDs and generic Faker
methods are compile errors.

## External Materializer

A response or event request may replace its ordinary headers/body
materialization with `materializer`. The response still declares `status`; the
event still declares `target`, and its request still declares `method` and
`path`. In either case,
ordinary event `query`, `headers`, and `body` are mutually exclusive with
`materializer`:

```yaml
request:
  method: POST
  path: /webhooks/payment
  materializer:
    argv: [python, scripts/sign-event.py]
    cwd: .
    env: {}
    timeout-ms: 2000
    max-output-bytes: 1048576
```

The compiler resolves `argv[0]` to an absolute executable, requires `cwd` to
remain within the selected workspace, records exact argv/cwd/literal
environment, and gives the process one strict JSON context on stdin. The
process returns one strict JSON envelope on stdout; stderr is bounded
diagnostics. For an event, the envelope cannot contain a
target; method/path must equal the declared request. For a response, returned
status must equal the declared status and the returned envelope must satisfy the
selected contract when present. Redirects and target fallback are never enabled
by materializer output.

The stdin context has exactly `schema_version: 1`, `phase` (`response` or
`event`), immutable `run` replay facts, `scenario` identity, current immutable
`bindings`, and `request`: the normalized matched request in response phase and
exactly `null` in event phase. Raw request bytes use base64. It contains no
ambient environment, filesystem path, secret lookup, clock, or random handle.
The private control capability is never included.

The response envelope has exactly `status`, `headers`, and `body`; the event
envelope has exactly `method`, `path`, `query`, `headers`, and `body`. `headers`
is a string map and `query` is the same scalar/array map as authored requests.
`body` is exactly one of:

```json
{"kind":"empty"}
```

```json
{"kind":"structured","value":{"provider":"shaped JSON"}}
```

```json
{"kind":"raw","base64":"cHJvdmlkZXItYnl0ZXM="}
```

Unknown/null envelope fields, malformed base64, duplicate JSON keys, non-finite
numbers, or phase-incompatible values fail before network response/delivery.

`validate` inspects the declaration but never executes it. Runtime invocation
has a timeout and byte bound. SVC does not sandbox the command or claim its code,
dependencies, network behavior, determinism, or provider fidelity.

## Event Target Policy

`policy.event-targets` defaults to `loopback-only`. Target CLI values must be
origins with no userinfo, path other than `/`, query, or fragment. Default
origins use numeric loopback IP literals.

`explicit-remote` in the module only permits a caller to request remote
delivery; the matching target name must also receive
`--allow-remote-target NAME` at `start`. Delivery uses the bound origin plus the
event's declared path/query, follows no redirect, and reports the final resolved
origin before any emit. Any `2xx` is acknowledged; redirect, non-`2xx`, and
transport failure are resolved non-successes and are never retried.

## Rejected Surface

Compilation rejects YAML tags/aliases/anchors/merge keys, unknown keys,
multiple documents, product assertions, completion conditions, implicit
callbacks, response sequences, state transitions, timers, arbitrary functions,
embedded scripts, route registration, remote assets/contracts, and unsupported
generator/validator identifiers.
