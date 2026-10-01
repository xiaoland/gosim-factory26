# Agent Observability Analysis

- **Objective**: Evolve `svc telemetry agent-thread` into an analysis-first,
  local observability capability that helps maintainers improve SVC from real
  human-Agent collaboration. Users can navigate threads through a
  workspace-path directory tree (a non-authoritative project-like grouping),
  distinguish active and archived work, recognize a thread from its title and
  first user message, collect a bounded cross-provider trajectory, and analyze
  it through human- and Agent-readable surfaces.
- **Guardrails**:
  - Treat normal export as an intentionally lossy collect/normalize boundary,
    not an audit archive. Omit provider-native transcripts, discard noise,
    bound low-value content, and declare every loss. V1 adds no raw/debug
    export path.
  - Cut off schema-v1 archives completely. Add no legacy reader, converter,
    re-export selector, or transition mode; an old archive is an unsupported
    input, not a normalization source.
  - Preserve safety invariants independent of byte fidelity: explicit local
    selection, no automatic collection/network egress, no source/repository
    mutation, no overwrite, containment, private output, bounded resources, and
    non-leaking diagnostics.
  - Keep the current non-interactive `list` safe and scriptable. Show title,
    first-user-message preview, and workspace only in an explicitly entered
    sensitive surface; model archive lifecycle separately from source
    availability and treat workspace/CWD only as provenance.
  - Make `analysis` the product capability and keep its normalized records
    provider-neutral.
  - Keep private thread content and the existing eight-case corpus outside Git.
  - Use Letta trajectory and ccxray as design evidence, not copied schemas,
    identifiers, runtime topology, or implementation code.
  - Do not mutate runtime code or durable product truth until Sir approves a
    slice-specific Impact Handshake and explicitly starts it. Sir approved the
    Slice 1 handshake and later the exact Slice 2–5 continuous implementation
    handshakes on 2026-07-28.
- **Verification**:
  - Existing list fixtures plus headless interaction fixtures prove both the
    safe automation contract and large project/workspace tree navigation with
    title/message recognition and archive filtering.
  - Cross-provider-shape fixtures prove deterministic normalized records,
    stable tool linkage, declared loss, bounded resources, safe diagnostics,
    honest partial-result behavior, and absence of native transcript members.
  - Analysis runs without the provider home and proves traceable,
    multi-resolution, tool/task/terminal/concurrency and SVC-specific findings.
  - A privacy-safe aggregate study over the eight private cases measures
    usefulness and compatibility; final acceptance includes repository tests,
    monolith build, UI headless proof, and cross-platform fresh-wheel fixtures.
- **Current Truth**:
  - On 2026-07-28 Sir corrected the product purpose: agent observability exists
    to improve SVC. The earlier audit-completeness framing was a product error.
  - The pre-v11 10.0.2 baseline retained the raw export introduced in 10.0.1:
    it preserved provider bytes, hashed/sized the native source, hard-failed
    source changes, indexed structure, and copied task-packet material.
    Published v11.0.0 replaces that behavior with the intentionally lossy
    schema-v2 collect boundary and cuts schema-v1 archives off directly.
  - Current Codex state on all three inspected systems exposes the v1
    identification/lifecycle/recognition fields. Slice 0 freezes exact field
    authority, missing/invalid behavior, bounds, and filter-before-limit
    semantics without assuming future provider schemas are identical.
  - Letta trajectory and ccxray support the normalized, analysis-oriented
    direction; Textual is frozen as the v1 local human-analysis runtime. SVC
    owns its schema, safety boundary, deterministic analysis, and Agent JSON.
  - Slice 0 freezes the public grammar, schema-v2 normalized bundle, declared
    loss/bounds, schema-v1 archive cut-off, inventory authority, analysis
    projections, Textual dependency range, and ordinary MAJOR consequence.
  - Slices 0–5 are implemented. The safe list remains non-sensitive; the
    explicitly entered navigator exposes bounded recognition data; export
    contains only `manifest.json` and `trajectory.jsonl`; Agent JSON and the
    Textual UI consume the same deterministic ten-dimension analysis.
  - The eight-case private aggregate completed without identifiers/content:
    all sources were stable, all normalizations were ready, no known shape was
    unsupported, coverage was available in every case, and unavailable/partial
    projections remained explicit rather than fabricated.
  - The integrated 224-item pytest suite, Ruff, mypy, Import Linter, zizmor,
    release check, monolith/build, exact wheel metadata/RECORD inspection, CLI
    smoke, privacy review, and installed-wheel inventory/bundle/analysis/UI
    harness all pass. macOS 3.12.10, WSL 3.13.5, and Windows 3.14.0 used the
    same wheel SHA-256
    `f57fbe6a212a37ae49a8736f648667f0e42b6e56375c346546cebeae828af507`;
    harness and caller staging cleanup were both proven.
  - The shared stale `F:`/`/mnt/f` worktree was not used or mutated. The
    implementation landed as `2b457442789a88a09897234d0147a252971c6936`;
    reviewed release merge `f99baad7cf9b8798475c3037636dbc8a0e7a738b`
    owns annotated tag `v11.0.0`. PyPI and the published GitHub Release expose
    the accepted wheel SHA-256 above and matching original sdist SHA-256
    `377cd1ab36fc8f227566743019775f96ef3324b5a7a7ba1ff8e150ac9f6900b0`.
    Release recovery hardening landed on `main` as
    `38440db85894a2db89694c879b66b45537969257`; its post-merge CI and no-fragment
    Release PR workflows both passed.
- **Next Step**: Only hands-on terminal acceptance remains. In a real macOS
  terminal and Windows Terminal, judge workspace-tree readability, title plus
  first-message recognition, active/archived switching, keyboard navigation,
  narrow/resize behavior, analysis-view usefulness, and alternate-screen
  restoration on `Escape`/`q`.

## Supporting Material

### Decisions

- Product-purpose and compatibility change:
  [`contract-delta.md`](contract-delta.md)
- Thread inventory and tree interaction:
  [`inventory-navigation.md`](inventory-navigation.md)
- Provider-neutral collection model:
  [`trajectory-schema.md`](trajectory-schema.md)
- Exact normalized record schema:
  [`trajectory-records.md`](trajectory-records.md)
- Human- and Agent-facing analysis:
  [`analysis-contract.md`](analysis-contract.md)
- Exact Agent JSON schema:
  [`analysis-schema.md`](analysis-schema.md)
- Deterministic projection algorithms:
  [`analysis-algorithms.md`](analysis-algorithms.md)
- Exact manifest, capabilities, loss, and diagnostics:
  [`bundle-manifest.md`](bundle-manifest.md)
- Frozen Slice 0 decisions:
  [`slice-0-decisions.md`](slice-0-decisions.md)

### Evidence

- Letta trajectory, ccxray, and terminal UI research:
  [`research.md`](research.md)
- Contract, privacy, compatibility, and package proof:
  [`verification.md`](verification.md)
- macOS, WSL, and Windows acceptance preflight:
  [`acceptance-environments.md`](acceptance-environments.md)

### Work

- Slice order and exact Slice 1–5 Impact Handshakes:
  [`delivery-plan.md`](delivery-plan.md)
- Implementation topology, sequence, and failure rehearsal:
  [`implementation-rehearsal.md`](implementation-rehearsal.md)
- Previous export contract:
  [`../40-export-agent-thread/packet.md`](../40-export-agent-thread/packet.md)
- Field-study boundary:
  [`../50-agent-thread-field-study/packet.md`](../50-agent-thread-field-study/packet.md)
- Existing audit method:
  [`../70-agent-thread-audit/packet.md`](../70-agent-thread-audit/packet.md)
