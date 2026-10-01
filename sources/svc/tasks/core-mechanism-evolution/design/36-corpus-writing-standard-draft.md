# Draft — SVC Corpus Writing Standard

- **State**: evolving task-local draft; no durable SVC authority
- **Source**: Sir's request after reviewing the three-state topology; current
  SVC Documentation Quality rules; observed corpus communication pressure;
  ASD-STE100 Issue 9 as a fallible controlled-language reference
- **Consumer**: later cross-cluster reconciliation and any future authorized
  edit to the canonical SVC corpus under `src/`
- **Use**: make the SVC framework content authored under `src/` concise,
  structurally legible, unambiguous, useful to both Human and LLM readers, and
  mechanically checkable where semantics permit

This draft remains inside the Task Packet. It should improve as the capability
discussions expose communication failures or better representations. It does
not authorize source edits, a new corpus document, a style linter, or a fixed
template.

## Scope Boundary

This standard governs the authored SVC corpus under `src/`: the framework's
canonical sections, extension guidance, owner/routing surfaces, and source
templates as applicable. Generated artifacts such as `build/monolith.md` are
verified projections, not independent writing owners.

For a template under `src/`, this standard governs how the SVC source explains
and encodes that template's framework contract. It does not thereby make this
draft the writing standard for documents later instantiated in a Consumer
project; those documents keep their own semantic-owner rules.

It does **not** directly govern:

- volatile Task Packets under `tasks/`
- a consumer project's PRD, Product TDD, Unit TDD, deployment truth, or other
  durable project documents
- ordinary source-code style, commit messages, or runtime UI copy

Some principles—semantic ownership, progressive disclosure, direct language,
and restrained diagrams—may later prove reusable there. Reuse requires the
applicable owner and consumer contract; this draft must not silently turn into
a universal documentation standard.

## Controlled-Language Reference Boundary

[ASD-STE100 Issue 9](https://www.asd-ste100.org/assets/files/ASD-STE100_ISSUE9.pdf)
is a controlled natural-language standard for technical documentation. Its
writing rules and controlled dictionary aim to reduce ambiguity—for example by
using stable approved meanings, one preferred term rather than synonyms, and
consistent technical nouns/verbs.

SVC should study rather than claim compliance with it. STE was shaped for
precise operational/maintenance documentation and English comprehension; the
SVC corpus also carries conceptual boundaries, defeasible design guidance,
cross-owner relations, and Agent-operational knowledge. Full vocabulary or
grammar restriction could erase needed nuance, inflate explanations, or reject
established software terms.

Provisional reusable pressure:

- prefer one stable term for one SVC concept and one intended meaning per term
- keep subject, action, condition, and outcome explicit in normative guidance
- avoid synonym variation when it forces Human or Agent concept reconciliation
- keep project/domain technical terms controlled by their semantic owner
- write a sentence so one requirement or relation can be interpreted and
  checked without reconstructing several implicit clauses

These are candidates already compatible with semantic compression, not adopted
STE rules. Full rules, a controlled vocabulary, or linting require corpus cases
showing lower total interpretation/error cost without material meaning loss.

## Desired Reading Outcome

A reader at the document's intended entry point should be able to determine,
with minimum irrelevant loading:

1. why this content exists and when it applies
2. which claim, behavior, or decision it owns
3. what the reader should understand or do
4. which authority, invariant, exception, or conflict rule constrains it
5. where deeper detail or verification belongs

Optimize total interpretation and maintenance cost, not line count alone.
Compression that removes necessary scope, authority, exceptions, or causal
structure is not concision.

## Core Authoring Rules

### One corpus owner, controlled projections

- Keep one canonical statement for each durable normative claim.
- Distinguish canonical `src/` content, consumer-facing template/projection,
  example, rationale, and historical evidence.
- Repeat only the minimum meaning needed for routing, control, or local
  comprehension; label authority/freshness when confusion is plausible.
- Repair contradictions from the applicable authority/semantic owner outward.
- Delete or supersede obsolete prose rather than accumulating corrections that
  force the reader to reconstruct current truth.

### Structure around meaning and consumption

- Give each document and section a coherent concern and intended consumer.
- Give same-kind navigable concepts one predictable physical grammar. In the
  selected source layout, a concept is always a directory whose stable entry is
  `index.md`; current depth must not decide whether the concept is represented
  by a file or directory or force its canonical address to change later.
- Apply symmetry to node shape, not content volume. Siblings may have different
  pressure-proven depth; do not manufacture empty mirrored topics merely to
  equalize their children.
- Put the governing contract before elaboration, examples, history, or edge
  cases unless evidence is required to understand the contract.
- Give an entry a compact meta-description: why it exists, when it applies,
  what it owns and excludes, what minimum result it provides, and where a
  narrower question continues. Do not require fixed front matter or headings
  when natural prose communicates the same contract more cheaply.
- Explain the causal reason for a non-obvious rule and the material condition
  that weakens or reverses it. Keep that logic near the rule; do not preserve
  the full design history as rationale.
- Use headings that name the question, boundary, or decision; avoid generic
  buckets such as “Miscellaneous” or “More Details.”
- Keep work sequence out of semantic-owner content unless the sequence is
  itself the owned contract.
- Split by semantic ownership/retrieval pressure, not arbitrary length; keep a
  stable `index.md` synthesis when supporting depth grows.

### Use direct, stable language

- Prefer concrete nouns and verbs over abstract labels or motivational prose.
- Use one stable term per concept; expand local handles/acronyms before relying
  on them.
- Optimize for **semantic compression**, not literal word or tokenizer-token
  count: prefer one accurate familiar term when it carries the necessary
  behavior and distinctions with less interpretation cost than a phrase.
- Count ambiguity, wrong action, rereading, retrieval, translation, correction,
  and version-drift cost. A longer phrase is more efficient when a shorter word
  is overloaded, obscure, or induces the wrong behavior.
- Test wording by the behavior it evokes. “Find/obtain key information” keeps
  filtering and synthesis in scope; “collect information” can reward evidence
  volume. `Use when` describes applicability; `activate` can invent a method
  lifecycle. Preserve such contrasts only when they teach a recurring boundary.
- State negative boundaries when a plausible misreading would change behavior.
- Separate requirements, defaults, recommendations, examples, hypotheses, and
  evidence instead of letting tone imply authority.
- Preserve uncertainty and conditions; do not convert a contextual heuristic
  into an absolute rule for brevity.

### Budget the required common ground

- Treat every SVC-specific concept as a recurring collaboration cost: Human and
  Agent must learn, recall, align, translate, and update it while switching
  among Tasks and framework versions.
- Admit a new term only when it removes enough recurring ambiguity, control
  loss, or reasoning cost to outperform plain language or an existing concept.
- Make task purpose, consequential action/effect, likely return, authority
  boundary, material uncertainty, request, and decision explainable when
  consequential. Do not turn them
  into a continuously monitored Human status surface: Human expectation is
  often coarse, the exact return may emerge during work, and detail should grow
  when direction, cost, risk, authority, or likely return changes materially.
- Keep Working Method identity and specialist taxonomy Agent-facing; translate
  only their task consequences when ordinary Human collaboration requires it.
- Treat a Human's chosen term as possible evidence about intended meaning, not
  automatically as normative vocabulary. Infer the underlying concern, preserve
  room to challenge the term, and align explicitly only when differing readings
  could change the work or decision.
- Let specialist and Agent-oriented concepts remain progressive depth when the
  Human does not need them for collaboration or judgment.
- Give one admitted concept one stable name and a concise local bootstrap;
  remove synonyms, unexplained acronyms, and lifecycle metaphors that do not
  correspond to real state.
- Challenge sunk vocabulary during revision. A familiar framework term does
  not keep its place unless its coordination value still repays its concept
  budget.

Before adding a concept, ask:

1. Which recurring misinterpretation or control failure does it prevent?
2. Can plain language or an existing term carry the same distinction?
3. Who must know it—Human, every Agent, or only a specialist reader?
4. Does its recurring benefit exceed onboarding, recall, translation,
   task-switching, and version-drift cost?

### Disclose progressively

- Keep universal entry content small and sufficient for routing.
- Move specialist method, domain taste, extended rationale, and rare exceptions
  behind explicit triggers and discoverable links.
- Do not make a reader load a broad document merely to obtain one narrow rule.
- Do not create a file, section, diagram, vocabulary item, or template until it
  lowers interpretation, decision, verification, or maintenance cost.

## Choose the Representation That Carries the Relationship

Representation is part of semantic compression, not decoration after prose is
written. When information must cross a Human/Agent, context, or time boundary,
select the carrier that minimizes total communication, reconstruction,
challenge, maintenance, and loss cost for the intended consumer. The Working
Method that produced the information does not prescribe its format.

A shorter artifact is not automatically more efficient: a sequence diagram may
preserve the timing and authority of a complex payment flow more accurately
than a much longer nested list, while a paragraph may outperform a diagram for
one qualified invariant. Do not translate structured relations into prose first
and only then ask whether a diagram would look better.

| Representation | Prefer when | Avoid when |
| --- | --- | --- |
| short prose | one causal explanation, invariant, or nuanced qualification | several peer mappings or branches must be reconstructed mentally |
| bullets | a small set of independent rules or checks | order, dependency, hierarchy, or comparison is the main information |
| table | repeated-field comparison, exact mapping, ownership matrix, or decision alternatives | cells become paragraphs or sequence/causality is primary |
| topology / flowchart | ownership, hierarchy, dependency, branching, joins, or several coupled loops matter | a sentence or two-node relation is equally clear |
| sequence diagram | timing, authority handoff, request/return, feedback, or update order across participants matters | only static ownership is being shown |
| state diagram | a small set of real states and valid transitions is itself the contract | ordinary recursive work would be forced into a false state machine |
| pseudocode / grammar | behavior, transformation, ordering, or structural contract needs precision without committing to production implementation | the content is a contextual judgment or the implementation itself is the relevant evidence |
| executable prototype / code | behavior must be experienced or the implementation is the cheapest truthful reviewable carrier | rationale, rejected alternatives, cross-owner obligation, or long-lived intent would become invisible |
| example + counterexample | a rule is easy to overgeneralize or its boundary is the lesson | examples would substitute for the governing principle |

### Mermaid and visual topology

- Use Mermaid when relationships are materially harder to recover from linear
  prose—especially ownership, non-linear topology, joins, feedback, authority
  transfer, and cross-participant sequence.
- Choose the smallest diagram that preserves the important relationship. Split
  a diagram when labels become prose or unrelated concerns share one canvas.
- Use stable concept names and a deliberate direction (`LR` for flow/sequence,
  `TD` for hierarchy when suitable). Make edge labels carry the meaningful
  relation, not decoration.
- Accompany a normative diagram with enough prose/table content to state its
  scope, authority, exceptions, and consequences. Do not make an image the only
  searchable statement of a critical rule.
- Do not duplicate every diagram edge as a bullet list. Explain the governing
  interpretation and the non-obvious exceptions instead.
- Do not use diagrams merely to make a document look designed; visual parsing,
  rendering, maintenance, and generated-monolith cost must be repaid.

## LLM-Oriented Clarity Without LLM-Only Prose

- Put trigger, owner, expected action/return, stop condition, and conflict rule
  near the instruction they constrain.
- Prefer explicit relation names—owns, consumes, projects, invalidates, waits
  for, verifies—over vague proximity or “related to.”
- Make the normal path and the meaningful exception distinguishable.
- Use positive and negative examples where structurally similar actions have
  different authority or effects.
- Keep references resolvable and loadable through the packaged corpus; a link
  is optional depth, not a substitute for the local contract.
- Match the declared consumer. Human-facing or shared contracts must remain
  reviewable without Agent-only reconstruction; specialist Working Method depth
  may optimize for Agent use without forcing Human onboarding, while retaining
  enough explicit semantics for intentional framework audit and maintenance.

## Review and Verification

Before adding or materially revising `src/` corpus content, check
proportionally:

- Can the intended reader identify purpose, trigger, owner, action/return,
  exception, and verification without reading unrelated sections?
- Does another location make the same normative claim with competing wording?
- Is every projection visibly lower-resolution than its semantic owner?
- Does each table or diagram expose a relationship that prose obscured, and is
  its scope clear?
- Does the selected carrier fit the information structure and the intended
  reader's comparison, sequencing, simulation, review, or memory task better
  than a simpler alternative?
- Are names, paths, anchors, fragments, generated projections, and Mermaid
  syntax mechanically valid where tooling supports them?
- Does the simple-task reader avoid specialist content and ceremony?
- Can a fresh intended reader explain the contract and apply it to a positive
  and negative case without inventing missing rules? For a shared/Human-facing
  surface, can the Human do so without learning unrelated Agent taxonomy?

Mechanical checks should enforce only stable, objectively decidable contracts.
They cannot prove that a diagram is useful, prose is tasteful, or a semantic
owner is correct.

## Evolution and Possible Landing

- Capture concrete ambiguity, redundancy, navigation, misrouting, diagram, and
  maintenance failures as task evidence; revise this draft by causal lesson,
  not personal irritation alone.
- Prefer correction or replacement over indefinitely appending new rules.
- Reconcile this draft with Working Protocol, the `src/` owner registry,
  Verification, and Tastes & Design Ability before selecting a durable owner.
- The current `Documentation Quality` section in Working Protocol is a foothold,
  not a preselected final owner. A separate source surface requires a distinct
  trigger, consumer, conflict rule, verification path, and complexity return.
- Defer templates, lint rules, diagram checks, and other automation until a
  repeated failure and a mechanically enforceable invariant justify them.
