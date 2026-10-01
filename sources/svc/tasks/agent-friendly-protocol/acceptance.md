# Agent-friendly Core CLI Implementation Acceptance

## Evidence boundary

This file records execution evidence for the implementation authorized on
2026-08-08. Product acceptance uses real repositories and real Consumer
commands. Temporary directories in unit tests verify mechanics only and are
not counted here. Existing dirty Consumer roots were read-only; all mutations
occurred in disposable copies of those real repositories.

The following are distinct evidence classes:

- **natural Consumer evidence**: an unchanged real project root;
- **disposable Consumer evidence**: a real repository copy with the proposed
  SVC migration or declaration applied;
- **real-project mechanism evidence**: a temporary declaration around an
  existing project command where no Consumer has adopted that declaration yet;
- **mechanical evidence**: unit/integration tests and clean-wheel smoke;
- **unavailable**: a required external service or credential was absent. No
  fixture is substituted for an unavailable real lifecycle.

## Source and package gates

The complete final source gate after native-Windows correction was:

- `pdm run test`: 198 passed;
- `pdm run lint-tests`: passed;
- `pdm run typecheck`: 31 source files passed;
- `pdm run lint-imports`: five contracts passed;
- `pdm run lint-workflows`: no findings, four configured suppressions;
- `pdm run check-release-projections`: passed;
- `pdm run check-documents`: 22 canonical documents passed;
- `git diff --check`: passed;
- `pdm build`: wheel and sdist built with CLI `11.0.1` and Corpus `12.0.0`;
- clean installed-wheel smoke: command tree, help, exact lookup/read, regex,
  four-operation init, and packaged config-v2-to-v3 descriptor passed. The
  final no-source-fallback run imported
  `/private/tmp/svc-final-wheel.0aq5XI/venv/lib/python3.12/site-packages/svc_cli`,
  read Corpus 12.0.0 deployment content, and loaded the packaged 2 -> 3
  descriptor.

Changie's dry-run gate was unavailable because the `changie` executable is not
installed on this macOS host. Generated release projections are independently
checked; the missing executable is not represented as a passing Changie gate.

## macOS real-project evidence

### Natural read-only roots

Evidence root:
`/var/folders/rk/8_krr0y14p9g5plk8n77lgyr0000gn/T/tmp.Hz7WyHbZg8`.

| Project | Observed result |
| --- | --- |
| InKCre client-web | Schema-v2 root selected config upgrade first; base and local overlay produced two exact operations; `dev identity` preserved instance `4ac9df364b54706e`; init was blocked with zero operations until config migration. |
| InKCre core-py | Same staged routing and two-operation base/local migration; instance `b0a97f7ca6abfdf7`; Python direct-reader guidance was included. |
| InKCre docs | Schema-v2, no dev section; config plan was version-field-only and did not invent dev configuration. |
| SFP7 Camera | Non-Git identity `fc804c7cb2752f5f`; `repository_id == worktree_id == d87b89d11b65d9deb884`; host/manual target retained its real failing exec probe evidence. |
| Anana `mvp-HA` | Real unadopted project; status reported unadopted and init planned exactly four effects with no SVC Skill. |

For compact JSON calls, terminal results were on stdout and the other channel
was empty. Config apply receipts explicitly retained the still-pending Corpus
target instead of implying full project migration.

### Disposable mutation copies

Evidence root:
`/var/folders/rk/8_krr0y14p9g5plk8n77lgyr0000gn/T/tmp.hd0sG8gf4S`.

- InKCre docs config migration rewrote only `svc.json`, then init deleted the
  clean generated `.agents/skills/svc/SKILL.md` and refreshed AGENTS/docs.
  Repeated init was noop; status remained actionable only for the Corpus
  baseline.
- Anana init created only schema-v3 `svc.json`, the `.gitignore` and AGENTS
  managed blocks, and `docs/index.md`. Status became healthy and repeated init
  was noop.
- SFP7 config migration rewrote only `svc.json` and retained mode `0600`.
  Init deleted the clean legacy Skill and refreshed AGENTS/docs. Its real
  `x86_64-f43-custom-kernel` target produced
  `manual-action-required`, `ready:false`, exec-probe exit 1 and 194 bounded
  output bytes for both ensure and stop; stop performed no PID mutation.

### Unavailable database lifecycle rows

The macOS host has no Docker executable, so the client-web/core-py native
database ensure/stop rows could not run there. Native Windows Docker reached
client-web's real provider but `docker pull ghcr.io/inkcre/core-py:stable`
failed `unauthorized`. These rows remain unavailable; no sleep process, local
HTTP fixture, or fake database was substituted.

## WSL real Consumer lifecycle

Host: `wsl.win-ws.localhost` (Linux WSL2). Disposable real client-web checkout:
`/tmp/svc-acceptance.lovqSi/client-web`, commit
`37546a51c3f2b022dbd21363df3b316cab4e6b5f`.

The built wheel installed under `/tmp/svc-acceptance.lovqSi/venv`. Config
upgrade planned digest
`97b0c7375e9364529daee0a145f2d645c6565555322add03072e1084dcabb13b`,
applied schema 2 -> 3, and reminded that Corpus 10.0.1 -> 12.0.0 remained.

Portless used an isolated non-privileged state at
`/tmp/svc-acceptance.lovqSi/portless-localhost`, port 1356 and the Consumer's
required `.localhost` TLD. Project dependencies were installed from the real
lock, and the declared `@inkcre/core build` was run before the real web target.

Lifecycle evidence:

1. `svc dev ensure web --json` returned `started`, `ready:true`, execution
   `45483a1b-7590-4522-87c6-af62ec7cc2dd`, state `released`, and merged log
   `/run/user/1000/svc/execution/45483a1b-7590-4522-87c6-af62ec7cc2dd/output.log`.
2. After that SSH starter exited, an independent status probe remained healthy
   and a second ensure returned `reused`; it did not publish another attempt.
3. The disposable target then declared its existing real cleanup command
   `node scripts/dev-stop.mjs`. `svc dev stop web --json` executed once as
   `1451c105-bb35-40bc-821e-e0695e925aea`, wrote a 130-byte shared log,
   returned `stopped`, `ready:false`, and its final probe exited 1.
4. The log named the exact route/PID stopped and confirmed that no database
   runtime existed. A later independent status returned
   `continuation: ensure`.

### Real-project run convergence

No Consumer had already adopted `svc run`. A disposable declaration named
`core-build` invoked the repository's existing
`pnpm --filter @inkcre/core build`; this is mechanism evidence, not adoption
evidence.

Two simultaneous calls returned owner and follower receipts for the same
execution `e0d3633c-73fe-4c15-9eea-1ad032ec8875`, duration 6311 ms, exit 0,
stdout 1323 bytes, stderr 305 bytes, and the same two log paths. Default
`--inspect` rendered the entry, exact command, cwd, duration and both log
references. A later explicit invocation reran as
`bab487cf-edc6-40d7-bf0c-e435ed16d0b5`, proving that only the active intent
converges.

### Linked-worktree identity

The same disposable real repository added `client-web-linked`. Both roots had
`repository_id e8f53c897ae292c958ba` and namespace
`690a973a9a68fe9a77ba`; the main worktree had
`worktree_id a742d15f905296ae06ae`, instance `4caadb98425df7cd`, while the
linked worktree had `worktree_id 3b4e4aa58fdb3afe56a2`, instance
`16716132647de99b`. This proves repository sharing without collapsing
worktree-scoped capability identity.

Both isolated WSL Portless proxy processes were stopped through their exact
state directories after acceptance.

## Native Windows qualification

Host: `win-ws.localhost` (Windows 10.0.19045.6466). Disposable real client-web
checkout:
`C:\Users\yyh\AppData\Local\Temp\svc-acceptance-3c8wiagj\client-web`, same
commit as WSL. The built wheel installed into the adjacent `venv`.

### Package/config behavior

- `svc --version` returned CLI 11.0.1.
- Identity returned Git root, instance `7238de1f593e448b`, repository ID
  `ce0525104972e45ef5da`, and worktree ID `ad8019b203a59a75191a`.
- Config migration digest
  `f47c71cdec7780c107f82cd9877d4ff3bf4ad4acea786e392bacb4c6136f349b`
  applied one exact rewrite. Windows file facts correctly omitted POSIX mode;
  the receipt retained the pending Corpus target.
- The unchanged real database target reached Docker and failed only at the
  private GHCR authorization boundary. Its failure log remained referenced by
  the dev receipt.

### Defects found and corrected

Native qualification found three SVC defects that fixtures and POSIX tests did
not expose:

1. Windows returned Node errno `-4058` as DWORD `4294963238`. New writes now
   expose signed 32-bit exit codes and the schema-v2 reader accepts and
   normalizes already-persisted DWORD values.
2. Python's Windows `signal` module has no `SIGKILL`. Force cleanup now uses
   `Popen.kill()` for foreground children and exact `taskkill /T /F` for an
   isolated owned tree; the retest returned a structured
   `readiness-timeout` receipt instead of a traceback.
3. `CREATE_NEW_PROCESS_GROUP`, and then that flag plus `DETACHED_PROCESS`, both
   allowed a real Vite target to become ready but did not survive SSH job
   closure: the next call returned `started` again. Adding
   `CREATE_BREAKAWAY_FROM_JOB` produced the required persistence.

The real Consumer also had Windows-specific `spawn('pnpm')` and no-extension
Portless probe-shim defects. Only the disposable checkout was patched
(`shell: win32` and `portless.CMD`); those changes are not part of this SVC
implementation or claimed as SVC acceptance results.

### Terminal-close proof

To isolate SVC's carrier from Portless's own daemon behavior, the disposable
config declared `web-direct` around the real client-web Vite executable and its
real `/__inkcre/dev/<instance>` HTTP endpoint on loopback port 4472. It did not
use a fixture server. Stop was deliberately `manual`, so SVC could not infer
PID authority.

1. With final carrier flags, ensure returned `started`, `ready:true`, HTTP 200,
   execution `71a0d735-c0a1-4b91-918e-86b9e88b7a9d`, and state `released`.
2. After the SSH session closed, a new SSH invocation returned `reused` and
   port 4472 was still listening at PID 37300.
3. `svc dev stop web-direct --json` returned
   `manual-action-required`, `ready:true`, stdout/3, and did not mutate the
   process.
4. Read-only process inspection proved PID 37300 was exactly
   `node node_modules/vite/bin/vite.js --host 127.0.0.1 --port 4472
   --strictPort`. Acceptance cleanup then terminated only that PID/tree and
   verified that port 4472 no longer listened.

This closes the Windows release boundary: console detachment alone is
insufficient under OpenSSH; job breakaway is required and is now executable
contract, not inferred documentation.

## Residual limits

- Database owner/external-owner cleanup remains unavailable on the tested
  hosts because of Docker absence or private registry authorization. The WSL
  web lifecycle and Windows real Vite carrier cover long-lived process and
  stop semantics but do not replace database-specific ownership evidence.
- `core-build` and `web-direct` are disposable real-project declarations, not
  claims that client-web has adopted those public entries.
- The Windows Consumer compatibility patches identify actionable client-web
  portability work but remain outside this repository and task scope.
