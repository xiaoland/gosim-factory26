# Resolve Missing Parent Records

Read this when a child must resolve an uncertain data relationship and return a small query plus its actual result instead of transferring the whole investigation.

Suppose failures may arise because invoices refer to accounts that no longer exist, but the relationship and relevant data scope are uncertain.
Give the child the schema, failing identifiers, snapshot entry, and read-only scope.
It investigates the relationship and whether null references, archived records, or deleted accounts are legitimate.
It can return an illustrative query of this form, adapted to the actual relationship:

```sql
SELECT i.id, i.account_id
FROM invoices AS i
LEFT JOIN accounts AS a ON a.id = i.account_id
WHERE i.account_id IS NOT NULL AND a.id IS NULL;
```

The useful return includes the actual result for the relevant snapshot and its interpretation, rather than “there are orphans.”
The caller checks that the join and null handling represent the intended relationship, that the selected records include the failing cases, and that the result was actually obtained from the stated input.
This can replace reading all invoices or repeating the child's search for the relationship.
It supports a repair direction if those cases match; it does not establish every business rule or authorize deleting records.
If the domain excludes archived records or treats a missing parent as valid history, the query and conclusion must reflect that condition.
If the relationship and query were obvious from the beginning, direct execution would have been enough.
