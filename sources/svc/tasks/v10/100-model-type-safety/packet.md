# Model and Type-Safety Evolution

- **Objective**: Determine whether targeted Pydantic v2 adoption and a mature
  static type checker can improve SVC's model authority and type safety without
  weakening canonical telemetry, archive, or analysis contracts; implement
  only an approved, evidence-backed pilot or migration.
- **Guardrails**:
  - Keep one authority per fact. A Pydantic model may not become a second,
    drifting description of a released trajectory/manifest/analysis schema.
  - Preserve the current canonical JSON parsing, duplicate-key rejection,
    deterministic bytes, streaming/resource bounds, ZIP safety, and
    schema-v1 fail-closed behavior unless a replacement proves each invariant.
  - Do not adopt Pydantic merely because it is available. Prefer it where it
    makes an untrusted boundary model clearer, stricter, or cheaper to evolve.
  - Do not introduce a whole-repository type gate with a large ignored baseline.
    A selected checker must have a bounded owner, invocation, error budget, and
    representative defect class.
  - Keep this task distinct from test-topology convergence and the 11.0.0
    observability delivery; no wire-schema, product behavior, runtime
    dependency, CI, or existing packet mutation occurs without a
    slice-specific Impact Handshake and Sir's explicit start.
- **Verification**:
  - An authority map classifies every candidate boundary as retain-manual,
    Pydantic candidate, or static-type seam, with an explicit reason.
  - Any Pydantic pilot proves valid and adversarial fixtures, output/canonical
    equivalence where relevant, bounds, error codes, and no duplicate authority.
  - The selected type checker passes a small named scope with no unbounded
    suppression policy; its local and CI invocation are mechanically verified.
  - The full suite, package build, and affected black-box acceptance remain
    green after every approved implementation slice.
- **Current Truth**:
  - Pydantic v2 is already a runtime dependency and is used well for strict,
    frozen, discriminated project configuration in `svc_cli/config.py`.
  - Telemetry uses frozen dataclasses/protocols for domain seams and manual
    `Mapping[str, object]` validators for trajectory, manifest, and analysis
    wire data.
  - Manual telemetry validation owns non-negotiable behavior that generic DTO
    parsing does not automatically provide: duplicate JSON key detection,
    canonical serialization, byte accounting, incremental collection, and
    archive publication safety.
  - A local Pydantic v2.13.4 probe confirmed that JSON duplicate keys collapse
    before model validation (`{"x":1,"x":2}` becomes `x=2`), so
    `extra="forbid"` cannot replace the current duplicate-key parser.
  - A four-module, Python 3.11 comparison found the same 17 concrete defects
    in Pyrefly 1.1.1 and mypy 2.3.0. Mypy's older adoption model and Pydantic
    v2 plugin make it the primary gate; Pyrefly remains an evaluated optional
    developer/IDE comparator rather than a second CI authority.
  - No telemetry Pydantic migration has a demonstrated net gain today. The
    existing Pydantic configuration models remain the right boundary; canonical
    telemetry stays hand-validated. The selected implementation slice only
    adds a bounded static gate and removes the observed ambiguity.
  - The implementation now locks mypy 2.3.x in a development-only `quality`
    group, checks the named four-file scope with `pydantic.mypy`, and runs the
    same `pdm run typecheck` command in a Python 3.11 CI job. It is zero-error
    with no baseline or broad suppressions.
  - Focused behavior tests (28), the full suite (208), wheel/sdist build, CLI
    smoke, and lockfile check all passed after the change.
- **Next Step**: No further automated change is warranted. Leave broader
  Pydantic migration deliberately deferred unless a future boundary earns its
  own measurable, authority-preserving proposal.

## Supporting Material

- Evidence: [`evidence.md`](evidence.md)
- Authority map: [`authority-map.md`](authority-map.md)
- Migration options: [`migration-options.md`](migration-options.md)
- Tool evaluation: [`tool-evaluation.md`](tool-evaluation.md)
- Verification matrix: [`verification.md`](verification.md)
- Related test topology task: [`../90-test-topology-convergence/packet.md`](../90-test-topology-convergence/packet.md)
