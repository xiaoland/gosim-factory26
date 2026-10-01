# Working Note — Constructive Collaboration Surfaces

- **State**: provisional-note
- **Sources**: Sir's references, primary sources reached through them, and
  bounded Lead synthesis
- **Use**: Connect context engineering, constructive data modeling, design
  review, Explorer tool use, and SVC ownership without creating mandatory
  phases, files, or schemas

## Source Anchors

- [How to Write an Effective Software Design Document](https://refactoringenglish.com/excerpts/write-an-effective-design-doc/)
  and its linked
  [design-review guidance](https://refactoringenglish.com/blog/useful-feedback-on-design-docs/)
- [The new rules of context engineering for Claude 5 models](https://x.com/i/status/2080710971228918066)
- [Constructive data modeling slides](https://github.com/lexi-lambda/talks/blob/master/2026-07%20constructive%20data%20modeling/slides.pdf)
  reached through Sir's
  [ChatGPT synthesis](https://chatgpt.com/share/6a641b23-ed10-83ea-baff-d284c4a9f049)
- [CodeStruct: Code Agents over Structured Action Spaces](https://arxiv.org/html/2604.05407v3),
  [Structural Code Search using Natural Language Queries](https://arxiv.org/html/2507.02107),
  and ast-grep's
  [test-before-scan Agent skill](https://github.com/ast-grep/agent-skill),
  reached through Sir's
  [Explorer-tool synthesis](https://chatgpt.com/share/6a6f2fb4-84d4-83ea-ab03-02edef19d772)

## Evidence Boundary

The references do not have one proof horizon:

- Michael Lynch's design-document guidance and Mitchell Hashimoto's large-work
  method are practitioner experience, not controlled evidence.
- Thariq's X article reports an internal context-engineering change and coding
  evaluation for a particular generation of Claude models and Claude Code.
- Alexis King's constructive-data-modeling slides directly present a general
  modeling argument.
- CodeStruct and the natural-language-to-structural-query paper provide bounded
  experiments on particular models, benchmarks, and interfaces.
- The two ChatGPT shares are useful syntheses with citations. They are not
  original research or OpenAI product policy; material technical claims should
  be resolved against their primary sources.

## Converging Direction

The common move is from textual regulation toward structural enablement:

- constructive data modeling makes valid states natural to construct and moves
  handling obligations to the consumer best equipped to resolve them
- structured code tools expose named program entities and validated actions
  instead of forcing Agents to manipulate anonymous text spans
- progressive context engineering replaces an always-loaded instruction mass
  with a small core, pressure-loaded skills, tools, and high-fidelity references
- an effective design document exposes costly decisions and unresolved issues
  for review without specifying every implementation detail

A provisional SVC principle is:

> Prefer collaboration structures that make useful moves easy to express,
> invalid or unauthorized moves difficult or visible, obligations local and
> explicit, and uncertainty cheap to inspect. Add prose rules only where the
> surrounding structure cannot preserve the needed judgment or boundary.

This does not mean every judgment can be encoded, every wrong action can be
made impossible, or more structure is always cheaper.

## Four Surfaces, Not Four Artifacts

```text
intent and current pressure
  -> context surface
  -> decision surface
  -> action surface
  -> evidence surface
  -> observed result and updated understanding
```

- The **context surface** makes the smallest relevant truth, instruction,
  source, and local gotcha discoverable when needed.
- The **decision surface** exposes a material question, alternatives,
  consequences, uncertainty, authority, and current resolution to the people
  or Agents who must judge it.
- The **action surface** offers appropriately scoped ways to inspect or change
  the system and carries effect authority in its interface.
- The **evidence surface** connects a claim or artifact to observations,
  mechanical checks, independent review, Human taste, and residual unknowns.

These are analytical lenses. Do not create four documents, stages, packet
fields, or CLI namespaces from them. One type, compiler error, task dossier,
test, tool, or Human interaction may participate in several surfaces.

## Constructive Obligation Routing

Constructive data modeling adds a stronger idea than state validity: a data or
interface change should propagate the handling obligations it creates.
Exhaustive pattern matching is a strong mechanical example. Weaker forms
include a schema rejection, failing contract test, compiler error, owner link,
or explicit open decision.

This suggests a candidate interpretation of low-cost large-system evolution:

> A system is easier to change when a material change can be expressed at its
> semantic owner and the resulting obligations become local, visible, and
> checkable at the consumers best equipped to handle them.

This proposition directly addresses one contributing mechanism under
`O-SYSTEM`: it can reduce impact rediscovery and make some cross-boundary change
work explicit. It is not a unifying explanation of all three outcomes. It may
help `O-TASK` when fewer dependencies remain hidden and may help
`O-INTERACTION` when Human review receives clearer consequences, but those
effects require a concrete causal path in the episode under review. A compiler
can propagate every type obligation while the product remains wrong, the
Human's taste remains unmet, or a long task still fails to integrate.

Hidden cross-field constraints, comments that say “must,” copied truth,
unresolved review threads, and broad optional state push those obligations
into future rediscovery. More precise models are not automatically better:
choose the simplest representation that prevents expensive impossible states
and propagates the obligations the system actually needs.

The same idea applies to collaboration:

- Human owns intent, taste, and material value trade-offs because Human has the
  relevant authority and context.
- Lead owns coupled framing, decomposition, integration, and escalation.
- A specialized Agent owns a bounded method and local result.
- A compiler, schema, test, or other verifier owns the mechanical claim it can
  actually decide.

Do not send an obligation downstream to an actor that lacks the information or
authority to resolve it.

## Context: Invariants Versus Scaffolding

The X reference reports that newer Claude models retained coding-evaluation
performance after a large system-prompt reduction. Its more durable warning is
that overlapping rules, skills, user requests, and repository instructions can
conflict and consume reasoning merely to determine what applies.

Separate:

- **normative invariants**: product, safety, authority, compatibility, and
  project truths that remain required regardless of model capability
- **local gotchas and domain knowledge**: facts that cannot be cheaply inferred
  from the repository or surrounding artifact
- **behavioral scaffolding**: extra rules, examples, repetition, or workflow
  hints compensating for a particular model or harness limitation

Behavioral scaffolding should be treated as a compatibility measure with a
cost and a reopen condition, not silently promoted into timeless framework
truth. Remove obvious or repeated advice when the environment already expresses
it; retain explicit dangerous boundaries and knowledge that the Agent cannot
recover reliably.

The proposed current-rule resolver therefore looks less like a rule oracle and
more like a context projection mechanism: discover applicable canonical
sources, expose the relevant constraints with provenance and conflict, and
leave the pending judgment with its owner.

## Decision Dossiers and Durable Truth

The design-document reference suggests two useful pressure rules:

- design effort should rise with the cost and irreversibility of getting the
  decision wrong
- the document should include only the subset of objective, background, goals,
  non-goals, scenarios, constraints, interfaces, risks, alternatives, open
  issues, and evidence needed for useful review

For SVC, do not infer a universal durable `design-doc` owner or full template.
Keep distinct:

- `packet.md`: the compact resume and control surface
- a pressure-created design dossier: the active Human-Agent decision surface
- durable product, technical, operational, or ADR owners: accepted expensive
  truth that must survive the task
- code, types, schemas, tests, configuration, and automation: executable truth

Review questions and misunderstandings should improve the current dossier or
canonical owner rather than survive only in comments or chat. Open issues need
an explicit next move; resolved issues need the decision and useful rationale.
Do not preserve every rejected idea or comment thread.

For long work, use milestones or slices that produce observable artifacts,
tests, replays, or demos soon enough to correct product understanding. A
milestone is valuable because it changes what can be learned or judged, not
because it moves a progress percentage.

## Explorer as Query and Tool Routing

The strongest supported model is not “an Explorer knows many commands.” It is
an adaptive loop:

```text
understand the claim or decision need
  -> classify the information shape
  -> load the smallest suitable tool or skill
  -> execute a bounded query
  -> inspect query validity and evidence scope
  -> cross-check weak or negative evidence when needed
  -> update the search plan or return a compact evidence map
```

A useful provisional routing table is:

| Information shape | Likely first surface | Important boundary |
| --- | --- | --- |
| Exact text, known identifier, path, or literal | `rg` or equivalent text search | Do not pay a structural-query setup cost |
| Syntactic shape or repeated mechanical transformation | AST/structural search such as ast-grep | Validate parser, selector, example matches, and result bounds |
| Definitions, references, types, symbol identity, or call graph | LSP, SCIP, compiler index, or code graph | Text/AST shape alone may confuse same-named symbols |
| Data flow, taint, or security property | Static-analysis engine suited to that property | A syntactic match is not a semantic proof |
| Product concept, business intent, or unknown vocabulary | Repository map, owner registry, documentation, semantic retrieval, then source inspection | Similarity is navigation evidence, not authority |
| Post-change invariant | Predefined rule, compiler, type checker, schema, test, or other verifier | Prefer reused mechanical checks over a new natural-language search |

The route is selected by the question's semantics and required proof horizon,
not by a global tool priority. A zero-result structural query proves only that
the chosen parser and rule found no matches; completeness-sensitive claims need
another evidence path. Limit result volume before it enters Agent context.

When the Agent must synthesize a query in an unfamiliar DSL, a clean interface
may be insufficient. Primary experimental evidence shows that validated paired
examples, local explanations, and executable error feedback can materially
outperform API documentation alone. The reconciled rule is therefore:

- remove generic tutorials, repeated prompt rules, and always-loaded tool
  schemas when the interface is already legible
- retain the smallest executable examples and feedback loop for unfamiliar,
  brittle, or underspecified action languages

## Structured Interfaces Are Conditional Leverage

CodeStruct reports that AST-addressed reads and edits improved accuracy and
reduced tokens or cost for most tested model configurations, but not all. One
small model used substantially more tokens while achieving much higher task
accuracy; another configuration saved tokens without improving accuracy.

The important inference is not “prefer AST.” It is:

- identify the dominant failure: irrelevant context, localization, brittle
  editing, tool-expression difficulty, or reasoning limitation
- choose an action space that removes that failure without imposing a larger
  representation burden
- keep navigation, read, edit, and validation interfaces coherent; a partial
  structural interface can be worse than a consistent text workflow
- evaluate result quality and total cost separately

This reinforces the earlier role model: specialized Explorer value comes from
choosing and operating a coherent evidence interface, not from possessing the
largest tool list.

## Human-Agent Consequence

Progressive disclosure should also govern discussion. Put the objective,
current pressure, consequential alternatives, and requested Human judgment
first; expose deeper evidence and system detail only when review reaches it.

Rubrics, examples, mockups, replays, tests, and verifier Agents can make product
or technical taste easier to communicate and check. They are reference and
evidence carriers, not automatic transfers of Human acceptance authority.

## Current Boundary

This note is a candidate explanatory model. It does not yet authorize:

- new mandatory packet fields or dossier sections
- a universal design-document template or approval state machine
- an AST-first Explorer policy or fixed search-tool router
- automatic rule deletion, generated context, or model-specific SVC variants
- new CLI action spaces, validators, schemas, or durable owners

Keep the model only while it helps explain concrete design pressure. Simplify
or split it when its own conceptual cost exceeds that return.
