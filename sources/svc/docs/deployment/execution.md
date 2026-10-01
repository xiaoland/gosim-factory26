# Local Execution Runtime

Use this [Deployment](index.md) depth when operators or developers need the
runtime authority, storage, recovery, and platform behavior shared by `run`
and `dev`. Product-visible behavior and cross-unit identity remain with Product
Truth and Product TDD.

Shared execution evidence lives under the platform user runtime directory in
an `svc/execution` tree. Each UUIDv4 execution has one strict atomically
replaced schema-v2 JSON record and policy-selected byte logs; domain
coordination pointers and locks are derived from semantic coordination keys. Paths,
records, and domain identifiers are validated before access. Files request
user-only permissions where supported, but this is the established same-user
trust boundary, not protection from a hostile process under the same account.

The runtime is local operational evidence, not archival storage. It may be
removed by reboot or platform cleanup, and the first slice adds neither an
automatic retention policy nor a reset command. Settled records are not
automatically deleted. Missing, malformed, mismatched, or partially published
authority fails closed so SVC cannot start a duplicate or fabricate a receipt.
Writes use same-directory temporary files and atomic replacement.

The initiating run CLI retains the lifetime lock and child handle. If it is
lost uncatchably, an orphan child may remain; the next caller may record
`owner-lost` only after acquiring the abandoned lock and must not replace the
execution in that invocation. Dev ensure may deliberately persist `released` after
readiness and then relinquish its handle. After release, later dev authority
comes from capability probes rather than the historical PID, and complete
process-lifetime log capture is not promised.

On POSIX, isolated dev attempts use null stdin, merged log redirection, and a
new session so a ready released capability is not tied to the starter terminal.
Windows uses `DETACHED_PROCESS`, `CREATE_NEW_PROCESS_GROUP`, and
`CREATE_BREAKAWAY_FROM_JOB`: console detachment and job breakaway are separate
requirements, and process-group creation alone does not preserve a child when
an OpenSSH session job closes. A parent job that forbids breakaway makes launch
fail instead of silently weakening persistence. While SVC still owns an
unsettled isolated attempt, interruption targets only that exact process group
or tree; Windows uses `taskkill /T /F` because a detached process cannot receive
the starter console's control event. Once released, only Consumer-declared stop
plus readiness verification may clean it up.
