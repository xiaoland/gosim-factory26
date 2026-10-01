# Dev Configuration Topology Review

## Reopened question

Adding target-local `stop` exposed an older layer in the current schema:

```text
dev.profile -> dev.profiles.<profile>.targets.<target>
```

The original design intended profiles to hold several complete, committed,
team-shared dev alternatives while `svc.local.json` selected or sparsely
refined one alternative. The concepts are therefore theoretically distinct:
profiles are named base declarations; the local file is an ignored effective-
environment overlay.

## Real Consumer evidence

The distinction has no demonstrated Consumer:

- InKCre client-web and its phase-3 worktree each declare only `local`;
- InKCre core-py declares only `local`;
- SFP7 Camera declares only `f43-builder`;
- the observed client-web and core-py local overlays refine provider, SSH,
  port, environment, and access values but never select another profile.

The only multi-profile example is a framework test/configuration example using
fabricated `worktree` and `shared` alternatives. Target-local `scope` already
expresses worktree/repository/host sharing, so that example does not establish
a second independent profile need. There is also no CLI profile selector; a
caller cannot directly express a profile intent.

## Accepted simplification

Sir accepted flattening the effective dev declaration on 2026-08-08:

```text
dev.targets.<target>
```

The resulting complete shape is:

```json
{
  "dev": {
    "targets": {
      "web": {
        "scope": "worktree",
        "probe": {"kind": "exec", "argv": ["probe-web"]},
        "provision": {"kind": "exec", "mode": "run", "argv": ["start-web"]},
        "stop": {"kind": "exec", "argv": ["stop-web"]},
        "access": []
      }
    }
  }
}
```

`svc.local.json` refines the same sparse path:

```text
dev.targets.<target>.<field>
```

This removes `dev.profile`, `dev.profiles`, `${dev.profile}`,
`SVC_DEV_PROFILE`, the profile field in command results, and the profile
component of capability coordination identity. Target name, declared scope,
workspace/repository/worktree identity, execution namespace, and canonical
probe endpoint continue to qualify a capability.

Multiple committed environment alternatives are not reserved speculatively.
Current Consumers should use the committed target declaration plus
`svc.local.json` for actual execution-environment differences. A future need
for shareable alternatives must first demonstrate its selection interface,
identity effect, overlay interaction, and Consumer.

## Impact boundary

This is a schema and coordination-contract change, not a presentation-only
cleanup. Implementation must migrate every real schema-v2 Consumer, flatten
base/local validation and resolution, remove profile interpolation and result
fields, and prove that capability locking still separates every meaningful
effective target. Existing multi-profile tests prove old mechanics only and
must not be treated as product evidence for retaining the layer.

No product implementation is authorized by this review.
