# One Rule, Several Consumers

Read this when a changed shared rule must be adopted by several implementations or branches, and publication could be mistaken for adoption.

Suppose a project has explicitly decided that a user preference overrides a workspace default when both apply.
Keep that precedence and its exceptions in one shared definition rather than separately explaining it in editor and importer tasks.

```text
Product requirement
  → Shared definition: precedence, exceptions, examples, revision
      ├─ Editor implementation and checks
      ├─ Importer implementation and checks
      └─ Task packets and discussions link to the definition
```

An overlap example should exercise both values together; two isolated checks cannot demonstrate precedence.
If the decision changes, replace the old precedence in the shared definition and publish its commit.
Tell the editor and importer contributors the exact difference and which overlap check must change.
Each compares the new definition with their branch and check expectations, then reports the adopted commit or the remaining dependency.
A comment saying “updated” or an old passing test is not that comparison.
This particular precedence is illustrative, not a default rule for other products.
Documentation keeps the intended semantics available; observations establish whether each consumer actually follows them.
