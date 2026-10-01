# Lead Proposal — Explore Frame Method

- **State**: accepted for design in `D-050`; real-task evidence remains open
- **Consumer**: `WP × P1 / 10-DS`
- **Question**: what method lets Frame determine “key information” without
  prematurely fixing the problem or forcing every Explore into causal analysis
- **Sources**: classic exploratory-search, software-comprehension,
  sensemaking, design-framing, information-compression, and causal-invariance
  research; Sir's proposed essence model; current Task corrections
- **Not decided now**: what follows Frame, the complete Explore SOP, Explorer
  sub-agent method, or durable source layout

## Evidence Boundary

The cited software studies are qualitative and context-specific; they reveal
question shapes and failure pressure rather than a universal Agent algorithm.
Sensemaking/design theories supply useful models, not mechanically verified
SOPs. Information bottleneck and invariant prediction make parts of Sir's
intuition mathematically precise under strong formal assumptions, but do not
decide product purpose, scope, or acceptable loss.

## Cases and Research Findings

| Context | Finding | Frame consequence |
| --- | --- | --- |
| Software change tasks | Sillito, Murphy, and De Volder observed questions about initial focus points, related entities, subgraphs, and relations among subgraphs; programmers jumped, abandoned paths, and returned rather than following category order | A context-location Frame must name the needed level only provisionally; the relevant scope can expand or move as focus points appear |
| Industrial developer information needs | Ko, DeLine, and Venolia found many distinct information needs; difficult needs included causal, rationale, occurrence-condition, expected-behavior, dependency-change, and task-relevance questions | “Get context” is not one information need. Frame must distinguish what kind of answer would make progress |
| Exploratory search | Marchionini distinguishes lookup from learning and investigation; exploratory search is especially relevant to the latter two | Obvious lookup should stay cheap; non-trivial Frame must reveal whether the task seeks a known fact or develops understanding |
| Data/Frame sensemaking | Klein, Moon, and Hoffman model a frame as shaping what counts as data while new data elaborates, questions, or replaces the frame | Frame is necessary but provisional; commitment sufficient to guide attention must coexist with anomaly-driven reframing |
| Creative design | Dorst and Cross observed problem and solution spaces co-evolving; partial solution ideas changed designers' formulation of the problem | A design-related Frame cannot require complete problem definition before trying ideas or loading solution evidence |
| Wicked planning problems | Rittel and Webber argue that some stakeholder/value problems have no definitive formulation or objectively true/false solution | For such work, Frame establishes a current value/scope agreement and decision horizon, not final objective truth |
| Relevant-information compression | Tishby, Pereira, and Bialek formalize a short representation of `X` that preserves information relevant to a target `Y` | “Key” is relational and compression has an adequacy cost; relevance cannot be selected without a target |
| Invariant causal prediction | Peters, Bühlmann, and Meinshausen use stability across environments/interventions to distinguish causal prediction from association | Sir's intervention/environment/stability test is valuable for causal Frames, but only when causal prediction is the intended return and assumptions/evidence support it |

Primary sources:

- [Questions Programmers Ask During Software Evolution Tasks](https://doi.org/10.1145/1181775.1181779)
- [Information Needs in Collocated Software Development Teams](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/icse07_ko.pdf)
- [Exploratory Search: From Finding to Understanding](https://doi.org/10.1145/1121949.1121979)
- [Making Sense of Sensemaking 2](https://doi.org/10.1109/MIS.2006.100)
- [Creativity in the Design Process: Co-evolution of Problem–Solution](https://sites.cc.gatech.edu/classes/AY2018/cs8803cc_spring/research_papers/Dorst_Cross2001.pdf)
- [Dilemmas in a General Theory of Planning](https://doi.org/10.1007/BF01405730)
- [The Information Bottleneck Method](https://arxiv.org/abs/physics/0004057)
- [Causal Inference by Using Invariant Prediction](https://people.math.ethz.ch/~peterbu/Files/Manuscripts/invariant-causal-prediction.pdf)

## Deduction — Frame Owns Provisional Relevance

Explore exists to find key information. No piece of information is key in
isolation: keyness depends on what the Task is trying to make possible, what
kind of answer is needed, and at what boundary/resolution the answer must hold.

But a Frame cannot be treated as final problem truth. It is itself a fallible
working model that selects attention. New information can reveal a mistaken
question, vocabulary, scale, stakeholder, causal model, solution assumption,
or return.

The strongest common definition is therefore:

> **Frame is a provisional definition of relevance for Explore:** it states what
> the exploration is trying to make possible, what kind of answer is sought,
> and the scope and distinctions under which information would count as key;
> later findings may revise any of these.

It is a working selection rule shared when necessary, not a durable authority,
mandatory artifact, or Human approval gate.

## Proposed Core Frame

For non-trivial Explore, establish the smallest useful answers to four prompts:

### 1. Purpose

What should become possible after this exploration? Examples include locating
a change surface, explaining an event, understanding a system, predicting an
effect, comparing alternatives, or deciding what to change.

This is not limited to the user's literal question. Recover the intended value
while keeping Human factual/solution claims challengeable.

### 2. Sought answer

What kind of answer is actually missing, about what target? Start with a plain
verb phrase rather than a taxonomy:

```text
locate <where behavior is owned>
explain <why this event occurred>
understand <how these parts cooperate>
predict <what changes under load>
compare <which option preserves the desired qualities>
```

The verb matters because evidence sufficient to locate a focus point is not
sufficient to explain a mechanism or predict an intervention.

### 3. Scope and resolution

At which material scale and boundary must the answer hold? Specify only axes
that can change relevance—for example event versus recurring class, function
versus service versus product, current platform versus multiple environments,
one stakeholder versus an affected group.

Do not fill a universal boundary checklist. The Frame should expose a disputed
or consequential scale, not enumerate every possible scale.

### 4. Keyness test

What difference must information make to count as key? Normally at least one:

- changes or selects the current route/decision
- rules out a material alternative or false assumption
- reveals a constraint, owner, mechanism, or boundary without which the return
  is unreliable
- compresses many observations into a simpler model that preserves the
  distinctions the return needs

If none can yet be stated, use a discovery Frame: find enough vocabulary,
candidate structures, and contrasting examples to formulate the first useful
keyness test.

The compact form is:

```text
To <purpose>, seek an answer that <answer verb + target>,
for <material scope/resolution>;
information is key if it changes or secures <needed distinction>.
```

This is a thinking aid. Obvious lookup remains one direct action; a complex or
delegated inquiry may externalize the Frame in its Inquiry/Plan surface.

## Frame Is Revised, Not Merely Filled In

Reframe when findings materially change:

- the purpose or stakeholder value actually at issue
- the kind of answer required
- the target, vocabulary, boundary, scale, or environment
- the plausible causal/design structure or the alternatives worth comparing
- the expected value of continuing exploration

Reframing is not failure or restarting by default. Preserve useful findings,
replace only the invalid relevance definition, and redirect subsequent work.
This is why Frame is the first Explore method but not a one-time gate.

## Conditional Causal/“Essence” Deepening

Sir's definition—goal-relative, minimal sufficient, stable causal structure—is
a strong specialization when the sought answer is **explain**, **predict**, or
**intervene**, especially across recurring events or environments.

Then deepen the Frame with:

- `Y`: the result whose behavior matters
- `A`: the feasible or hypothetical interventions relevant to the Task
- `E`: the environments/scales across which the conclusion must remain useful
- `Z`: the smallest representation that preserves the needed prediction of
  `Y` under `A` and `E`, within acceptable error

Use mechanism/constraint/representation separation, counterfactual deletion,
invariant search, prediction of unobserved cases, and intervention evidence as
available. Treat “essence” as relative to `Y/A/E`, not an intrinsic property of
the system.

### Necessary corrections to the supplied model

- Not every key fact is causal. Location, interface, provenance, convention,
  stakeholder preference, and feasibility facts can decide a Task.
- A relevant cause need not be directly manipulable; interventions can be
  hypothetical, prohibited, or outside current authority.
- Minimal sufficient representations need not be unique or identifiable from
  available observations. Sufficiency depends on acceptable error, loss, and
  the environments considered.
- Cross-environment invariance is not always the goal. A one-off incident or
  platform-specific defect may require unstable local detail.
- Product value and acceptable error are authority/decision questions; a
  causal or mathematical model cannot choose them.
- “Root cause” may be a set of contributing conditions rather than one node.

Therefore do not require every Frame to produce a causal graph, first-principle
decomposition, minimal model, or mathematical notation. Load this deepening
only when it changes the intended return enough to repay its cost.

## Worked Contrasts

| Explore case | Frame | What is key |
| --- | --- | --- |
| Exact symbol/API lookup | Locate the current authoritative definition | The defining source and applicable version; usually no externalized Frame |
| Context location for a feature change | Understand where product behavior is owned across the smallest material system boundary | Initial focus points and relations that identify the change/consumer surface; not the whole repository |
| Recurring production failure | Explain and predict the failure across stated load/environment conditions | Mechanism and constraints whose variation changes the failure; causal deepening is justified |
| Product/design ambiguity | Decide which problem/solution pairing serves stakeholders within cost and taste constraints | Surprising information, alternatives, and value conflicts that reframe both problem and candidate design; no fixed causal minimum is assumed |

## Working Posture Design Anti-pattern

### Co-occurrence Capture

> A behavior commonly occurs while using a posture, so the designer promotes
> it into that posture's SOP without showing that the posture needs a distinct
> version of the behavior.

Before admitting an SOP element, ask:

1. Would the same rule apply unchanged in most other postures?
2. Is it already owned by the universal protocol or another capability?
3. What Explore-specific failure does its inclusion prevent?
4. Would removing it make Explore's method incomplete, or merely less generally
   disciplined?

Co-occurrence establishes an interface candidate, not ownership. This
anti-pattern applies to every later Working Posture design.

## Review Disposition

Sir accepted provisional relevance, the four minimum prompts, and conditional
causal/essence deepening as the current design in `D-050`. The design looks
correct but requires time and real Consumer Tasks before its effect is treated
as established. [`design/44`](44-explore-post-frame-routing.md) records the
accepted post-Frame continuation.
