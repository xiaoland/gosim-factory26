# Case Card: `WIN-F`

## Boundary and Provenance

- **Case scope**: One selected long-running package/component-system evolution
  thread on Windows.
- **Packet relation**: No resolved packet attachment; planning/control artifacts
  appear in permitted dialogue but cannot be treated as attached source truth.
- **Known selection/context limits**: Framework/tool-version compatibility,
  registry credentials, browser harness stability, and consumer integration are
  environment or project boundaries. Component-level checks do not establish
  downstream application adoption.
- **Outcome confidence**: Multiple scoped packages/components have local and
  interaction-evidenced checks plus narrow commits. Real consumer integration,
  visual-regression rigor, and network-backed behavior remain unobserved.

## Trajectory

| Episode | Boundary rationale | Control-loop summary | Outcome evidence status | Outcome / uncertainty | Evidence pointer |
| --- | --- | --- | --- | --- | --- |
| `F1` | A new platform package starts with source/consumer authority discovery | Human selects the target authority; Agent reads structure and refuses to treat a cross-platform implementation as direct target truth | interaction-evidenced (design decision) | Design decision only; no package mutation | `WIN-F · F1 · lines 7–256 · dialogue/coordination/tool outcome` |
| `F2` | Explicit start permits implementation and build-chain repair | Agent introduces the scoped package, resolves build/dependency boundaries, and creates a narrow commit | locally evidenced (package checks); interaction-evidenced (start/continue decision) | Package checks and commit evidence; real consumer use remains unknown | `WIN-F · F2 · lines 257–901 · dialogue/tool/patch/task outcome` |
| `F3` | Atomic component migration becomes an externally documented scope | Human fixes naming and exclusions; Agent records each component's interface/accessibility intent and validates exports/build | locally evidenced (package checks); interaction-evidenced (scope decision) | Package-level behavior evidence; no consuming-app acceptance | `WIN-F · F3 · lines 902–1188 · dialogue/coordination/patch/task outcome` |
| `F4` | Presentation infrastructure and evidence matrix are introduced | Agent creates contract vocabulary and generated-artifact checks, then adapts the visual/story harness to compatible tooling | locally evidenced (generated/package checks); interaction-evidenced (browser smoke) | Layered local/browser-smoke evidence; visual-diff gate remains absent | `WIN-F · F4 · lines 1189–2420 · dialogue/tool/coordination/patch/task outcome` |
| `F5` | A delivery wave applies the component evidence loop repeatedly | Small components are implemented with registry, story, and narrow-commit discipline | locally evidenced (package/story checks); interaction-evidenced (review feedback) | Repeated package/story evidence; consumer adoption remains unknown | `WIN-F · F5 · lines 2421–3794 · dialogue/tool/patch/task outcome` |
| `F6` | Visual/information-architecture feedback generates a repair episode | Human uses in-app observation to correct density/semantic distinctions; Agent changes the verification form when a browser interaction is unstable | locally evidenced (component checks); interaction-evidenced (visual review) | Bounded visual/semantic repair; unstable harness is not treated as a component failure | `WIN-F · F6 · lines 3795–4566 · dialogue/tool/browser/patch/task outcome` |
| `F7` | A richer interactive component is clarified, completed, and committed | Human corrects a partial implementation; Agent separates variants and validates the declared scope | locally evidenced (package checks); interaction-evidenced (scope feedback) | Local/package evidence; no real backend/end-to-end interaction proof | `WIN-F · F7 · lines 4567–5240 · dialogue/browser/tool/patch/task outcome` |
| `F8` | Responsive-layout vocabulary is made public before abstraction | Human constrains over-abstraction; Agent promotes stable vocabulary, discovers an edge case through browser smoke, and adds a guard | locally evidenced (layout checks); interaction-evidenced (browser review) | Scoped layout evidence; broader page-level benefit is unproven | `WIN-F · F8 · lines 5241–5914 · dialogue/tool/browser/patch/task outcome` |
| `F9` | Composite control and design-governance work ends in a future proposal | Human visual feedback revises geometry/style; Agent validates the control and records a deliberately narrow roadmap | locally evidenced (control checks); interaction-evidenced (visual feedback) | Current control evidence; later container proposal is not implementation | `WIN-F · F9 · lines 5915–6540 · dialogue/browser/tool/patch/task outcome` |

## Observable Coordination

| Dimension | Observed mechanism | Boundary or alternative explanation | Evidence pointer |
| --- | --- | --- | --- |
| Intent and authority | Human establishes platform authority, design preferences, mutation/commit gates, and correction via direct visual feedback | The design system's close human review may not be available in all consumer projects | `WIN-F · F1/F3/F6/F9 · dialogue` |
| Shared state | Interface/accessibility intent, vocabulary, generated registry, stories, verification matrix, and narrow commit history externalize component state | No resolved attachment proves a specific packet version was followed | `WIN-F · F3/F4/F5 · coordination/patch/task outcome` |
| Coordination | Scope isolation excludes unrelated local artifacts; delegated research is bounded and main checks remain local | The audit cannot quantify whether this reduces total delivery time | `WIN-F · F2/F5/F6 · coordination/patch` |
| Observability | Generated checks, type/build, story coverage, browser/ARIA smoke, and direct visual feedback provide distinct evidence layers | Smoke/harness success is not visual regression, consumer integration, or network-backed interaction evidence | `WIN-F · F4/F5/F6/F7 · tool/browser/task outcome` |
| Recovery and continuity | Dependency/harness mismatch and visual-feedback corrections lead to compatible tooling, changed evidence form, and style vocabulary updates | Tool instability can mask defects; alternate evidence needs its own limitations | `WIN-F · F4/F6/F9 · dialogue/tool/browser/patch` |

## Within-Case Inferences

- **The case uses an episode-level contract that names interface,
  accessibility, vocabulary, and proof boundaries.**
  - **Why the evidence supports it**: scope and quality expectations are made
    explicit before repeated small deliveries, and later feedback can correct a
    known contract rather than restart discovery.
  - **What remains uncertain / competing explanation**: this may add overhead
    for small, isolated components.
  - **Evidence pointer**: `WIN-F · F3/F4/F5 · dialogue/coordination/patch`
- **The case distinguishes browser-smoke evidence from what it does *not*
  prove.**
  - **Why the evidence supports it**: local/package/browser checks repeatedly
    find useful issues while real consumer and network-backed outcomes remain
    outside the trace.
  - **What remains uncertain / competing explanation**: a dedicated consumer
    fixture may be too expensive for every component episode.
  - **Evidence pointer**: `WIN-F · F4/F6/F7 · tool/browser/task outcome`

## SVC Relation

- **Classification**: Within-case candidate hypothesis.
- **Reasoning**: SVC can support a generic episode contract, generated-artifact
  freshness gate, evidence ladder, scope/commit boundary, and explicit unknown
  status. Component semantics, design vocabulary values, tool versions, and
  consumer adoption remain project/design-system-owned.
- **Smallest testable intervention, if applicable**: offer an optional
  component-work packet profile with `contract`, `generated outputs`,
  `local proof`, `interaction proof`, `consumer proof`, and `known unknowns`.
- **Scope boundary**: this does not justify forcing all layouts or component
  changes through the same packet/profile, nor treating local smoke as
  production compatibility.
