# Source Landing: Repository Layout and Corpus Writing

> **Historical/non-normative**: do not implement this file's `sections/`
> layout or `CONTRIBUTING.md` authoring owner. Current layout and realization
> contracts are [`design/87`](87-symmetric-corpus-navigation.md) and
> [`design/88`](88-p2-review-and-realization-outline.md).

- **State**: partially superseded by the browse-first correction in
  [`design/85`](85-browse-first-layout-and-task-cli.md); retained as the prior
  `sections/`-based alternative and writing-contract derivation
- **Consumer**: `P2 — Source Landing Design` and its five participating Cells
- **Question**: how the accepted capability model should become a small,
  discoverable source topology and a coherent corpus-authoring contract
- **Inputs**: `D-013..D-090`, [`design/32`](32-integrated-task-packet-shape.md),
  [`design/36`](36-corpus-writing-standard-draft.md),
  [`design/69`](69-working-protocol-current-target-and-domain-boundary.md),
  [`design/79..82`](79-minimal-sub-agent-capability-and-landing.md), and the
  current canonical `src/` tree
- **Not authorized**: editing `src/`, templates, CLI/runtime, release metadata,
  or generated projections

## Landing Has Two Projections

Source landing is not primarily a transcription of the P1 dossiers. It has two
coupled design outputs:

1. **Repository layout** maps each stable semantic owner, entry trigger,
   consumer, and progressive depth to a discoverable source address.
2. **Corpus writing** makes each address cheap to interpret without erasing
   authority, conditions, causal meaning, or uncertainty.

Implementation ordering, compatibility handling, and verification are derived
from these outputs; they are not a third content taxonomy.

The five Task Tracks all participate because a coherent landing cannot shrink
Working Protocol until the routed Task Packet, Sub-agent, Verification, and
Design/taste owners exist. The Tracks remain Task management axes. The source
tree is organized by semantic ownership and retrieval, not by copying Track
names into five directories.

## Repository Layout Laws

1. **One stable semantic entry per concern.** A file owns a coherent contract;
   links project or route that contract rather than restating it.
2. **Flat before nested.** Put an admitted entry directly under `sections/`.
   Add a same-stem directory only when useful depth already exists and has a
   narrower trigger or consumer.
3. **Entry before depth.** A reader must be able to discover why and when to
   load deeper material without loading it first.
4. **Progressive depth is not an extension.** `sections/extensions/` remains
   for optional Consumer topology/capability contracts such as multi-repo or
   alignment. Core guidance that is conditionally loaded stays beside its core
   owner.
5. **Templates are executable projections.** They live under `assets/`, have a
   named guidance owner, and do not become the semantic authority merely
   because a CLI copies them.
6. **Public paths are contracts.** Renaming a packaged Markdown/template path
   requires an explicit compatibility and Behavioral SemVer disposition; a
   cleaner tree alone does not authorize churn or duplicate authorities.

## Proposed Initial Tree

```text
src/
├── index.md
├── sections/
│   ├── working-protocol.md
│   ├── working-methods.md
│   ├── working-methods/
│   │   ├── explore.md
│   │   ├── design.md
│   │   └── implementation.md
│   ├── task-packet.md
│   ├── sub-agents.md
│   ├── verification.md
│   ├── implementation-taste.md
│   ├── prd.md
│   ├── product-tdd.md
│   ├── unit-tdd.md
│   ├── deployment.md
│   └── extensions/
└── assets/templates/
    ├── task-packet/
    │   └── packet.template.md
    └── <existing non-packet templates>

AGENTS.md
CONTRIBUTING.md  # initial owner of the src/ corpus-authoring standard
```

This is an initial pressure-supported shape, not a permanent taxonomy:

- `working-protocol.md` stays the cheap operational kernel and router.
- `working-methods.md` owns method composition, the stateless/non-ritual law,
  and cheap bootstraps. The three accepted foundational methods already have
  enough distinct guidance to justify one level of progressive depth.
- Current Agent Task Analysis content moves behind the Explore route. It can
  remain a bounded use case inside `working-methods/explore.md`; no deeper
  directory is pre-created.
- `task-packet.md` owns SVC guidance for the volatile Consumer package. It does
  not make active Task state a durable truth destination.
- `sub-agents.md` and `verification.md` each begin as one compact owner. No
  profile, verifier, assurance, or role directories are admitted.
- `working-methods/design.md` supplies the Product/Technical/Test Design route
  and retrieves specialist taste. Existing `implementation-taste.md` remains
  the first specialist depth; no UI/UX or Architecture file is pre-created.
- Corpus-writing rules initially belong in `CONTRIBUTING.md` because their
  consumer is an SVC corpus author, not a Consumer project. Root `AGENTS.md`
  supplies the Agent trigger. Split a dedicated maintainer document only if
  that section becomes costly to retrieve or maintain.

`src/index.md` needs two visibly different maps:

- **Agent work guidance** routes to Working Protocol, Working Methods, Task
  Packet, Sub-agents, Verification, and taste.
- **Consumer knowledge owners** continues to map product/technical/runtime
  claims to PRD, Product TDD, Unit TDD, Deployment, code, configuration, tests,
  and local instructions.

This prevents Task Packet guidance or Verification guidance from being
misread as a new durable destination for Consumer project truth.

## Track-to-source Projection

| Track | Existing foothold | Proposed owner change | Content that must not be copied |
| --- | --- | --- | --- |
| `TP` | WP packet minimum, `task-packet-growth.md`, flat packet template, diagnostics matrix | consolidate the accepted package grammar in `task-packet.md`; route from WP; use the packet template family | live task state, every optional module, final acceptance, Working Methods |
| `WP` | one flat umbrella `working-protocol.md` | retain the kernel; move foundational method depth to `working-methods.md` and its three children; move corpus-authoring rules to the maintainer surface | profile contracts, verifier catalog, taste library, Task Packet filesystem detail |
| `SA` | no canonical owner | add one compact `sub-agents.md` with delegation economics and Explorer/Executor contracts | Explore/Implementation method logic, universal Return schema, Reviewer or validator persona |
| `VF` | proof language scattered through WP/PRD/Product TDD/Deployment | add one compact `verification.md` for claim-relative qualification and route local proof back to its existing semantic owner | Product/Technical claims, Test Design expectations, acceptance authority, all task-local evidence |
| `TD` | WP posture entry and `implementation-taste.md` | place Design method and Product/Technical/Test routing in `working-methods/design.md`; refine and link existing implementation taste | project truth, universal architecture, prebuilt UI/UX or architecture taxonomy |

## Corpus Writing Contract

The standard should optimize total interpretation and maintenance cost, not
word count. It applies to authored `src/` content and source templates as SVC
artifacts; it does not silently become the writing standard for Consumer PRDs,
TDDs, Task Packets, code, UI copy, or commit messages.

### Governing principles

- Start with the owned contract and its use condition. Put rationale, history,
  examples, and rare exceptions after the normal meaning.
- Keep one canonical normative claim. A local projection repeats only enough
  meaning to route or act without ambiguity.
- Prefer one stable term for one concept. Use direct subjects and verbs; make
  conditions, authority, expected consequence, and exceptions explicit when
  they change behavior.
- Optimize **semantic compression**: delete redundancy and motivational prose,
  but preserve distinctions whose loss can cause a wrong action, wrong owner,
  false confidence, or expensive rediscovery.
- Treat every SVC-specific concept as recurring common-ground cost. Admit it
  only when plain language or an existing term cannot economically preserve a
  management-relevant distinction.
- Describe applicability with ordinary language such as `use when`; avoid
  lifecycle verbs such as `activate` or `exit` unless a real state transition
  exists.
- Separate requirement, default, rebuttable guidance, example, hypothesis,
  and evidence. Compression must not turn contextual judgment into law.
- Give deeper content an explicit retrieval pressure. Do not create a file,
  heading, taxonomy, diagram, or template only to make the structure regular.
- State negative boundaries only when a plausible misreading would materially
  change work, authority, evidence, or effect.

### Representation follows the relation

| Information structure | Preferred carrier |
| --- | --- |
| one invariant, causal explanation, or qualified rule | short prose |
| a few independent obligations or checks | bullets |
| repeated-field comparison, ownership mapping, exact projection | table |
| dependency, hierarchy, branching, joins, or coupled loops | restrained topology/flow diagram |
| timing, authority transfer, feedback, request/return order | sequence diagram |
| a small set of real states and legal transitions | state diagram |
| precise transformation or structural contract | pseudocode/grammar |
| a rule whose boundary is easily overgeneralized | example + counterexample |

Use Mermaid only when it materially lowers reconstruction cost. A normative
diagram needs searchable prose for its scope and important exceptions, but the
prose must not duplicate every edge.

### Document bootstrap without a universal template

An intended reader should be able to learn near the entry:

1. why this content exists and when it is relevant;
2. what behavior, meaning, or decision it owns;
3. what useful action/return it enables;
4. which authority, invariant, exception, or conflict rule constrains it; and
5. where deeper guidance or verification belongs.

These are reading outcomes, not mandatory headings or front matter. Different
owners may use prose, a topology, a table, or an example when that is the
cheapest truthful carrier.

## Compatibility and Migration Questions

The target layout meets four different path pressures:

1. the uncommitted `sections/task-packet-growth.md` candidate versus canonical
   `sections/task-packet.md`;
2. the released `assets/templates/task-packet.template.md` versus
   `assets/templates/task-packet/packet.template.md`;
3. the released diagnostics template, whose whole-Task shape may conflict with
   the mixed-task/Inquiry model; and
4. the machine-exposed Agent Task Analysis method reference, which currently
   points to a section inside `working-protocol.md` but semantically belongs
   behind Explore.

Before mutation, the applicable Cell must choose one explicit disposition for
each: preserve a genuinely useful narrow projection, retain the current path,
or make a declared major transition. A dummy alias containing duplicate
normative content is not the default. The current Task Packet growth path and
CLI command are uncommitted and should be corrected before release rather than
treated as legacy.

## Landing Verification

The later source change should prove, at minimum:

- every new owner is reachable from the intended entry and packaged lookup;
- local Markdown paths/fragments and the generated monolith remain valid;
- catalog/wheel projection includes one canonical copy of each admitted file;
- old WP claims are either retained in the kernel, moved to one linked owner,
  or explicitly retired—never silently duplicated;
- a simple task can stop at the WP entry without loading Task Packet topology,
  Sub-agent, Verification, or taste depth;
- representative positive/negative reading rehearsals can route an Agent to
  the right owner without treating a role, test, template, or preference as
  authority.

Mechanical checks can prove paths, packaging, and selected stable wording
contracts. They cannot prove that prose is tasteful, a diagram is useful, or
the semantic owner is correct; those require review and later real-task use.

## Current Recommendation

Use the proposed tree as the P2 working candidate. It has one universal entry,
one method-family entry with justified depth, one compact owner for each new
cross-cutting capability, one reused taste foothold, and no speculative
taxonomy. Complete the five Cell-specific content/move contracts and the two
public-path dispositions before producing an Impact Handshake.
