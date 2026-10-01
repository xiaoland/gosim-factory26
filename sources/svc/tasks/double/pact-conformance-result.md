# Double Pact Matcher Conformance Follow-up

## Outcome

The pinned Pact compatibility suite is useful supplemental evidence, but its
regex matcher is not directly isomorphic to BSL v0. Exact scalar behavior and
the simplest positive/negative body regex vector align. Pact's unanchored query
and header regex vectors require whole-value matching, while CEL `matches`
admits a matching substring. SVC therefore accepts Pact-negative `9999X` for
the pattern `\d{1,4}`.

No production semantic is changed in this follow-up. Changing BSL regex from
the documented CEL/RE2 behavior to implicit full-match would be a language
decision and could invalidate existing modules that intentionally use substring
patterns. It cannot be smuggled into a behavior-preserving convergence pass.

## Reproducible Source and License

- upstream: [`pact-foundation/pact-jvm`](https://github.com/pact-foundation/pact-jvm);
- pinned commit: `97abd7bfcec15f3532109f984db37bcb5ccfb49c`;
- selected source paths:
  `compatibility-suite/pact-compatibility-suite/features/V2/http_consumer.feature`,
  `features/V3/matching_rules.feature`, and their referenced matcher fixtures;
- the compatibility-suite-local `LICENSE` is Apache License 2.0;
- Pact's official documentation describes the repository as the BDD feature
  and fixture suite for checking Pact implementations and documents the matcher
  fragment naming convention:
  [Pact compatibility suite](https://docs.pact.io/implementation_guides/jvm/compatibility-suite/pact-compatibility-suite).

No upstream source or fixture is copied into SVC. The executable
[`pact_matcher_probe.py`](spikes/reuse-convergence/pact_matcher_probe.py) accepts
an external checkout, verifies its exact commit and local license, reads the
upstream features/fixtures, and passes the derived values through production
`matcher_accepts`.

## Result Matrix

| Upstream fact | SVC v0 result | Assessment |
| --- | --- | --- |
| exact `OK` accepts `OK` | accepts | aligned locally; Pact's cascading reset behavior is outside BSL |
| exact `OK` rejects `Lovely` | rejects | aligned locally |
| `\w{3}\d{3}` accepts `HHH123` | accepts | aligned |
| `\w{3}\d{3}` rejects `a` | rejects | aligned |
| `\d{1,4}` accepts query `9999` | accepts | aligned |
| `\d{1,4}` rejects query `9999X` | accepts | **semantic divergence** |
| `\d{1,4}` accepts header `1000` | accepts | aligned |
| `\d{1,4}` rejects header `9999ABC` | accepts | **semantic divergence** |

## Decision Boundary

Three coherent choices now exist:

1. keep CEL substring semantics and require authors/Agents to anchor patterns
   when whole-value matching is intended;
2. amend BSL v0 regex to implicit whole-value matching and treat the change as
   a compatibility correction with explicit migration evidence;
3. version a separate whole-value matcher in a future BSL grammar.

Strict boundary verification favors whole-value matching because an omitted
anchor otherwise broadens accepted provider input silently. Compatibility and
the existing language statement favor retaining CEL semantics unless the
contract is deliberately amended. Sir's product decision is required before a
production change.
