# Python Ecosystem Boundary

## Baseline

The published 10.0.0 runtime has no third-party dependencies. PDM 2.27.0 resolves the project environment, `pdm lock --check` passes for Python 3.11 and 3.12 constraints, and `pdm run test` passes all 51 current tests. Towncrier remains isolated in the release dependency group.

The dependency question is therefore capability-driven: a package enters the runtime only when it replaces a real cross-platform or schema boundary, not because it offers a more fashionable spelling of small stdlib code.

## Adopt for This Delivery

| Package | Owned boundary | Why it is now justified | What remains SVC-owned |
| --- | --- | --- | --- |
| Pydantic v2 | Strict validation of complete effective `svc.json` models and discriminated probe/provision unions | Schema v2 has nested dynamic maps, union variants, defaults, and cross-field constraints. Continuing with ad-hoc validators would create protocol code with worse error locality and schema visibility. | Duplicate-key/non-finite JSON rejection, sparse overlay authority, recursive merge, exact error mapping, and JSONC edits. |
| platformdirs | Per-user runtime, state, and log roots on Linux, macOS, and Windows | Locks, evidence, and logs must stay outside the repository without hard-coded OS paths. | Directory permissions, identity hashing, retention, and diagnostic layout. |
| filelock | Per-capability inter-process lock | Concurrent Agent/human ensures require one cross-platform coordinator; filelock is pure Python and uses native OS locks with fallback. | Coordination key, second-probe rule, timeout outcome, and all readiness semantics. Lock files remain in the platformdirs runtime root and are not deleted on release. |

Dependencies are added only through PDM after implementation is explicitly authorized. Intended compatibility lines are Pydantic `>=2.13,<3`, platformdirs `>=4,<5`, and filelock `>=3.29,<4`; PDM resolves and locks the exact graph for the supported Python matrix.

## Keep in the Standard Library or Protocol Core

- `argparse` remains the CLI parser. Nested `dev` commands do not justify a Typer/Click migration or a second CLI idiom.
- `subprocess`, process groups, signals, and bounded polling supervise only the current launch attempt. `psutil` is deferred: its native extension and process-inspection authority do not buy a truthful universal cleanup guarantee. Platform limitations are reported as `partial` or `unknown`.
- `socket` owns TCP probes; the Git executable owns worktree discovery. No generic networking or Git abstraction is added.
- The first HTTP probe is deliberately small: GET/HEAD, HTTP(S), status interval, strict TLS by default, no redirects, no ambient proxy settings, and no response-expression language. A narrow `http.client` adapter connects only to the address just validated against network scope while preserving the configured Host/SNI, avoiding a second DNS resolution; it uses an explicit `SSLContext` and bounded per-attempt timeout. The coordinator caps each attempt by its remaining monotonic deadline.
- Strict JSON decoding uses `json` with `object_pairs_hook` and `parse_constant`. Pydantic validates values after the byte boundary.
- Overlay merge, interpolation, target identity, Behavioral SemVer exception verification, and retry timing are short protocol algorithms; generic deep-merge, template, SemVer, or retry packages would obscure their rules.
- The existing release PyPI query remains on `urllib.request`; importing HTTPX into that independent tool path would not improve its single bounded request.

## Deliberately Reject for the First Delivery

- `portalocker`: overlaps filelock and adds a Windows `pywin32` conditional dependency without needed distributed-lock functionality.
- HTTPX: its API is better for a broad HTTP client, but the initial probe would add HTTPX plus httpcore, h11, anyio, certifi, idna, and typing-extensions for a status-only HTTP/1.1 observer. It also would not own SVC's total deadline, address policy, instance provenance, or result vocabulary. Reconsider it only when response predicates, authentication, HTTP/2, or broader network clients become real requirements.
- `psutil`: defer until verified process-tree diagnostics or cleanup cannot be expressed truthfully with platform adapters.
- `pydantic-settings`: local overlay resolution is file authority, not environment-variable settings resolution.
- Typer, Click, Rich, Tenacity, deepmerge, GitPython, and generic SemVer libraries: no distinct owner or verification benefit in this slice.
- Existing Python JSONC libraries: audited candidates either strip comments, parse JSON5 rather than strict JSONC, fail to preserve arbitrary bytes, are stale/experimental, or introduce unstable/native dependencies.

VS Code Tasks and `package.json` therefore use one narrow lexical span editor. It validates the whole JSON/JSONC structure, rejects duplicate structural keys, and inserts or refreshes only SVC's marked/reserved entry. It is not exposed as a general JSONC library, and fixture tests must prove that every unrelated byte survives.

## PDM Gate

Implementation and verification use only declared PDM surfaces:

```text
pdm add <approved runtime dependencies>
pdm lock --check
pdm run test
pdm run build-monolith
pdm run svc --help
pdm build
pdm run release ...
```

A fresh wheel smoke test may create an isolated environment and install the built artifact because that verifies packaging rather than developing around PDM. No feature implementation uses bare `python`, `pip`, Poetry, uv, npm, or another project runner.

## Reviewed Sources

- Pydantic strict models and Python support: <https://docs.pydantic.dev/latest/concepts/strict_mode/> and <https://pypi.org/project/pydantic/>
- platformdirs platform paths: <https://platformdirs.readthedocs.io/en/latest/platforms.html>
- filelock cross-platform lock design: <https://py-filelock.readthedocs.io/en/latest/>
- Python HTTP transport, timeout, and TLS primitives: <https://docs.python.org/3.11/library/http.client.html> and <https://docs.python.org/3.11/library/ssl.html>
- HTTPX comparison point: <https://www.python-httpx.org/advanced/timeouts/> and <https://pypi.org/project/httpx/>
- JSONC syntax boundary: <https://jsonc.org/trailingcommas.html>
