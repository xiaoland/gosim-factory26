# Repository-control Payload and Readback

Status: applied and read back on 2026-07-30. This is task evidence, not a
tracked substitute for GitHub's live authority.

## Observed Baseline — Before Slice 3

Read-only API results:

```text
repository = xiaoland/svc
default branch = main
repository rulesets = []
main branch protection = absent
release environment protection rules = []
release environment deployment policy = null
repository immutable releases = disabled
GitHub Actions app ID on current CI checks = 15368
```

The future stable check contexts are `Python 3.11`, `Python 3.14`, `Quality and
architecture`, `Distribution`, and `Release policy`. The payload must not be
applied until every one has run successfully on `main` from GitHub Actions app
`15368`.

## Main Ruleset

Create one active repository ruleset at
`POST /repos/xiaoland/svc/rulesets`:

```json
{
  "name": "svc-qualified-main",
  "target": "branch",
  "enforcement": "active",
  "bypass_actors": [],
  "conditions": {
    "ref_name": {
      "include": ["refs/heads/main"],
      "exclude": []
    }
  },
  "rules": [
    {"type": "deletion"},
    {"type": "non_fast_forward"},
    {
      "type": "pull_request",
      "parameters": {
        "allowed_merge_methods": ["merge", "squash", "rebase"],
        "dismiss_stale_reviews_on_push": true,
        "require_code_owner_review": false,
        "require_last_push_approval": false,
        "required_approving_review_count": 0,
        "required_review_thread_resolution": true
      }
    },
    {
      "type": "required_status_checks",
      "parameters": {
        "do_not_enforce_on_create": false,
        "strict_required_status_checks_policy": true,
        "required_status_checks": [
          {"context": "Python 3.11", "integration_id": 15368},
          {"context": "Python 3.14", "integration_id": 15368},
          {"context": "Quality and architecture", "integration_id": 15368},
          {"context": "Distribution", "integration_id": 15368},
          {"context": "Release policy", "integration_id": 15368}
        ]
      }
    }
  ]
}
```

The explicit zero approval count makes this a PR-and-checks admission boundary,
not a second human release gate. The empty bypass list is intentional; an
administrator can still change repository policy, but no operating bypass is
silently granted by this ruleset.

## Release-tag Ruleset

Create one active tag ruleset:

```json
{
  "name": "svc-immutable-release-tags",
  "target": "tag",
  "enforcement": "active",
  "bypass_actors": [],
  "conditions": {
    "ref_name": {
      "include": ["refs/tags/v*"],
      "exclude": []
    }
  },
  "rules": [
    {
      "type": "update",
      "parameters": {"update_allows_fetch_and_merge": false}
    },
    {"type": "deletion"}
  ]
}
```

It deliberately has no `creation` rule. GitHub applies one bypass set to all
rules in a ruleset: using a creator bypass would also let that actor update or
delete tags. With the observed single repository writer, ordinary repository
write authority remains the authorized new-tag path, while the Publish workflow
has only `contents: read` and cannot create tags. Any future grant of write
authority therefore changes release approval authority and requires review.

## Publisher Environment and Immutable Releases

First update the existing `release` environment:

```json
{
  "wait_timer": 0,
  "prevent_self_review": false,
  "reviewers": [],
  "deployment_branch_policy": {
    "protected_branches": false,
    "custom_branch_policies": true
  }
}
```

Then ensure the only custom deployment branch/tag policy is `v*` with
`POST /repos/xiaoland/svc/environments/release/deployment-branch-policies`:

```json
{"name": "v*", "type": "tag"}
```

Finally enable immutable releases with:

```text
PUT /repos/xiaoland/svc/immutable-releases
```

The `release` environment intentionally has no required reviewer: the
protected tag is the sole approval. The `v*` custom policy is a ref boundary,
not a second approval. `type` is intentionally explicit: omitting it creates
a branch policy rather than a tag policy.

## Apply and Readback Sequence

1. Read active check runs on the exact current `main` commit; require the five
   names above and GitHub Actions app ID `15368`.
2. Create/read back the `main` ruleset, then confirm
   `GET /repos/xiaoland/svc/rules/branches/main` exposes PR, status-check,
   no-force-push, and no-deletion rules.
3. Create/read back the tag ruleset, then query the effective tag rule surface
   and verify matching `v*` refs have update/deletion rules.
4. Update/read back `release`; list deployment policies and require exactly
   one policy named `v*` with `type: tag` and no reviewer protection rule.
5. Enable/read back immutable releases and require `enabled: true`.
6. Open a deliberately failing probe PR and record that the required checks
   prevent merge. Do not use a direct push, destructive tag probe, or a
   production release as a test.

Official API semantics: [repository rulesets](https://docs.github.com/en/rest/repos/rules),
[deployment branch/tag policies](https://docs.github.com/en/rest/deployments/branch-policies),
and [immutable releases](https://docs.github.com/en/rest/repos/repos#enable-immutable-releases).

## Applied Evidence — 2026-07-30

- Bootstrap merge `fa478617f0898cdbcefcf8eef2717fbc7bb7bebb` produced all five
  required contexts from GitHub Actions app `15368` on main run
  [`30470940669`](https://github.com/xiaoland/svc/actions/runs/30470940669):
  `Python 3.11`, `Python 3.14`, `Quality and architecture`, `Distribution`,
  and `Release policy` all concluded `success`.
- The active `svc-qualified-main` ruleset is ID `19984694`. Effective rules
  for `main` read back as deletion and non-fast-forward protection, PR
  admission, and exactly those five strict required status checks with no
  bypass actor.
- The active `svc-immutable-release-tags` ruleset is ID `19984704`. Its
  `refs/tags/v*` scope has update and deletion protection with no bypass
  actor; it deliberately permits authorized creation of a new tag.
- The first policy creation omitted `type`; GitHub read back policy
  `55950839` as `name: v*`, `type: branch`. The first real tag run therefore
  completed planning and bundle construction but was rejected before PyPI or
  GitHub Release mutation: `Tag "v11.0.1" is not allowed to deploy to release
  due to environment protection rules.` The wrong policy was deleted.
- `release` now has no reviewer protection rule and exactly one custom
  deployment policy: ID `55951894`, `name: v*`, `type: tag`. Repository
  immutable releases reads back as `enabled: true`. The successful recovery
  and exact-complete dispatch in
  [`v11.0.1-acceptance.md`](v11.0.1-acceptance.md) prove the tag policy accepts
  the protected tag and no branch ref.
- Probe PR [#17](https://github.com/xiaoland/svc/pull/17), an empty commit
  intentionally missing `release:none`, ran CI
  [`30471304529`](https://github.com/xiaoland/svc/actions/runs/30471304529).
  `Release policy` failed in 14 seconds while the other four qualification
  checks succeeded; GitHub reported `mergeStateStatus: BLOCKED`. The PR was
  closed at `2026-07-29T16:34:50Z` and its remote probe branch deleted without
  a merge.
