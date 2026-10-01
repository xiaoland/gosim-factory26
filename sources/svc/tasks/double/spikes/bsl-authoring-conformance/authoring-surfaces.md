# YAML Authoring Surface Comparison

All three surfaces can serialize the same abstract value. The comparison is
about reviewability and reliable compilation, not YAML aesthetics.

## A. Local typed node

```yaml
vehicleRegistration:
  $bsl:
    generate:
      semantic: uk.dvla.current-registration-mark.syntax
      using: spike.uk-dvla-current-style/v1
      locale: en_GB
      match:
        semantic: uk.dvla.current-registration-mark.syntax
        using: spike.uk-dvla-current-style-validator/v1
    bind: vehicle_registration
```

The value, materialization rule, validator, and binding stay at one source
location. It parses as ordinary YAML/JSON data and can be checked by JSON
Schema. The cost is visible verbosity and a reserved-node collision rule: a
literal provider object whose only key is `$bsl` must use an explicit literal
escape.

## B. YAML tags

```yaml
vehicleRegistration: !generated
  semantic: uk.dvla.current-registration-mark.syntax
  using: spike.uk-dvla-current-style/v1
  locale: en_GB
  match: !semantic uk.dvla.current-registration-mark.syntax
  bind: vehicle_registration
```

This is shorter, but ordinary `safe_load` rejects the unknown constructors.
Every parser, editor, formatter, schema tool, and future JSON surface needs
BSL-specific tag support. Nested roles also become a mix of YAML node kinds and
domain semantics. Tags therefore make YAML itself part of the abstract
language and are rejected for v0.

## C. Adjacent path maps

```yaml
response:
  body:
    vehicleRegistration: AB51 ABC
  generators:
    $.body.vehicleRegistration:
      semantic: uk.dvla.current-registration-mark.syntax
      using: spike.uk-dvla-current-style/v1
      locale: en_GB
  matchers:
    $.body.vehicleRegistration:
      semantic: uk.dvla.current-registration-mark.syntax
      using: spike.uk-dvla-current-style-validator/v1
  bindings:
    $.body.vehicleRegistration: vehicle_registration
```

The provider-shaped example is visually clean, but four independently edited
trees must agree on a path language. Arrays, moves, and refactors create stale
paths; review has to join distant declarations mentally. This form remains
useful as a normalized interchange projection, as Pact demonstrates, but is a
poor primary authoring surface.

## Decision Table

Score: `1` poor, `3` workable, `5` strong.

| Criterion | Weight | Typed node | YAML tags | Adjacent maps |
| --- | ---: | ---: | ---: | ---: |
| Locality of value semantics | 25 | 5 | 5 | 2 |
| Generic YAML/JSON tooling | 20 | 5 | 1 | 5 |
| Source diagnostics | 15 | 5 | 3 | 2 |
| Refactor/path safety | 15 | 5 | 5 | 1 |
| Concision | 10 | 3 | 4 | 2 |
| Future non-YAML surface | 10 | 5 | 1 | 5 |
| Literal collision/escape cost | 5 | 3 | 5 | 5 |
| **Weighted total / 100** | **100** | **94** | **68** | **58** |

Provisional result: use local typed nodes for authoring and compile them to a
path-indexed normalized IR. Do not admit `$bsl` or the exact key layout yet;
the spike admits the structural choice, not the spelling.

The first execution also exposed a surface-level conformance trap:
`PyYAML.safe_load` resolved an unquoted clock into a Python `datetime`. A
follow-up `ruamel.yaml` probe configured for YAML 1.2 did the same until its
timestamp constructor was narrowed. BSL must pin and test its exact scalar
resolution; it cannot inherit a host library's implicit schema defaults.
