# Lead Proposal — When Is Explore Information Enough?

- **State**: accepted for design in `D-054`; operational and outcome evidence
  remain open
- **Consumer**: `WP × P1 / 13-IQ`
- **Accepted input**: Explore returns key information relative to a provisional
  Frame; satisfied and bounded-incomplete returns are distinct
- **Question**: what operational judgment prevents both premature closure and
  wasteful certainty-seeking
- **Not decided now**: numeric thresholds, a fixed strategy catalog, mandatory
  checklists/artifacts, real-task experiment design, or durable SVC landing

## Evidence Boundary

Decision theory supplies a normative relation between information and its
effect on action, but exact utilities and probabilities are rarely available
in software work. Sequential testing gives rigorous stop boundaries only when
hypotheses, observation distributions, and error costs are sufficiently fixed.
Information-foraging and empirical stopping-rule studies describe useful cost
pressure and Human behavior but do not prove a universal Agent policy.

## Research Findings

| Source | Relevant finding | Consequence for Explore |
| --- | --- | --- |
| Howard, *Information Value Theory* (1966) | information has economic value through the improvement it can cause in a decision, rather than through its quantity or entropy alone | “Enough” must be relative to what additional information could change and the consequence of that change |
| Russell and Wefald, *Principles of Metareasoning* (1991) | the utility of computation derives from its potential effect on an Agent's external action under resource bounds | more reasoning/search is justified by expected downstream improvement, not by a generic instruction to be thorough |
| Simon, *A Behavioral Model of Rational Choice* (1955) | limited decision makers simplify and satisfice rather than optimize over an unbounded world | an aspiration boundary is necessary, but “feels good enough” is not by itself a defensible boundary |
| Wald, *Sequential Tests of Statistical Hypotheses* (1945) | fixed hypotheses and error tolerances can support explicit sequential stopping thresholds | confidence thresholds are powerful specialized rules for Discriminate-like cases, not a universal Explore rule |
| Pirolli and Card, *Information Foraging* (1999) | seekers adapt to maximize the rate of valuable information obtained from an environment | declining yield may justify leaving the current source/method, but does not by itself prove the whole Explore is complete |
| Browne and Pitts, *Stopping Rule Use During Information Search in Design Problems* (2004) | design-oriented information gathering seeks sufficient problem structure and alternatives rather than only convergence; observed stopping rules materially affected information quality | different information purposes need different sufficiency tests; one quantity, checklist, novelty, or stable-model heuristic is unsafe as the universal rule |
| Browne, Pitts, and Wetherbe, *Cognitive Stopping Rules for Terminating Information Search in Online Tasks* (2007) | observed stopping rules vary with task type | a repertoire may help, but selection must follow the current Frame rather than Agent habit |

Primary and author/publication sources:

- [Information Value Theory](https://doi.org/10.1109/TSSC.1966.300074)
- [Principles of Metareasoning](https://doi.org/10.1016/0004-3702(91)90015-C)
- [A Behavioral Model of Rational Choice](https://doi.org/10.2307/1884852)
- [Sequential Tests of Statistical Hypotheses](https://doi.org/10.1214/aoms/1177731118)
- [Information Foraging](https://doi.org/10.1037/0033-295X.106.4.643)
- [Stopping Rule Use During Information Search in Design Problems](https://doi.org/10.1016/j.obhdp.2004.05.001)
- [Cognitive Stopping Rules for Terminating Information Search in Online Tasks](https://aisel.aisnet.org/misq/vol31/iss1/7/)

## Core Correction — Sufficiency and Stopping Are Not One Test

Two questions must remain distinct:

1. **Return adequacy** — does the currently supported result enable the Frame's
   purpose at its material scope, with residual uncertainty below the loss or
   decision tolerance applicable to this return?
2. **Continuation value** — is there a feasible, authorized next exploration
   move whose plausible outcomes could improve the return enough to justify
   acquisition, delay, attention, side-effect, and opportunity cost?

```text
                     Worthwhile next exploration move?
                         yes                    no
Return adequate?  +----------------------+----------------------+
yes               | continue if the      | satisfied return     |
                  | incremental value is |                      |
                  | material to the Task |                      |
                  +----------------------+----------------------+
no                | continue / reroute / | bounded-incomplete   |
                  | reframe              | return               |
                  +----------------------+----------------------+
```

This separates **information is enough** from **the Agent must stop anyway**.
Bounded-incomplete is justified stopping under a constraint, not epistemic
sufficiency. Conversely, satisfying a minimum answer does not imply immediate
exit when one cheap observation can prevent material downstream loss.

## Proposed Operational Test — Next Discriminator

At a non-obvious exit, ask only:

1. What material uncertainty remains, and what downstream answer, decision,
   action, or risk could it still change?
2. What is the best currently known next observation or exploration move for
   reducing that uncertainty?
3. Across its plausible outcomes, which would materially change or secure the
   current return?
4. Is that possible improvement worth the move's total cost, and is the move
   within applicable authority?

Return satisfied when the current result is adequate and no known next move has
material positive net value. Continue, reroute, or reframe when such a move
exists. Return bounded-incomplete when the result is inadequate but no feasible,
authorized, proportionate move remains.

This is a qualitative value-of-information judgment, not a demand to invent
probabilities or utility numbers. Externalize the reasoning only when the stop
is consequential or non-obvious.

## What “Adequate” Means

Adequacy is relative to the Frame and downstream loss, not a global confidence
score. It has three minimum parts:

- **purpose enablement**: the caller can now make the intended judgment or next
  move rather than merely possessing more context
- **scope validity**: the answer is supported at the material boundary,
  resolution, environment, and freshness needed by that use
- **residual consequence**: remaining plausible uncertainty would not alter the
  required distinction beyond the applicable tolerance; material residuals
  are explicit

Verification owns proof of the resulting claims and Inquiry owns persistent
evidence/freshness state when needed. Explore uses those interfaces to judge its
return; it does not absorb them.

The tolerance changes with downstream conditions:

- high-loss, irreversible, widely propagated, or hard-to-observe effects
  justify stronger counterpressure and more independent evidence
- cheap, reversible actions that quickly produce discriminating feedback may
  justify earlier Explore return and a controlled switch to action
- product value, ethical tolerance, and material risk acceptance remain Human
  authority; the Agent supplies evidence, expected consequence, and cost rather
  than silently selecting those values

## Guarding Against Premature Closure

Common Human stopping heuristics are useful diagnostics but unsafe as solitary
success criteria:

| Heuristic | Useful signal | Characteristic failure |
| --- | --- | --- |
| mental list complete | known required facets are covered | the list encodes the original blind spot |
| enough volume/confidence | a threshold supports routine repeated work | source count or subjective confidence substitutes for relevance |
| no recent novelty | the current information patch is exhausted | the Route is poor while another source/method remains valuable |
| representation stable | a coherent model exists | confirmation bias stabilizes the wrong Frame |

When downstream loss is material or the candidate space is open, apply
proportionate **counterpressure** before satisfied return: seek the strongest
plausible counter-frame, a materially different source/method, a boundary case,
or a discriminating observation. This is conditional risk control, not one
mandatory “find a counterexample” Step.

Unknown unknowns cannot be proven absent. Explore can only demonstrate why the
current coverage and remaining opportunity make further discovery low value,
or return that open-world residual explicitly.

## Strategy-relative Sufficiency Exposes a Catalog Problem

Applying the model to the provisional contrasts shows real differences:

| Provisional contrast | Characteristic adequacy question |
| --- | --- |
| Retrieve | has the authoritative, applicable answer for the specified target/version been obtained? |
| Map | are the relevant parts, boundaries, owners, and relations clear enough for the intended navigation/change? |
| Discriminate | have material competing explanations/options become separable, or at least action-equivalent within the loss tolerance? |
| Discover | does the candidate set cover materially different families, with low expected value from another genuinely different search route? |
| Probe | is the produced observation valid at the needed environment/resolution and strong enough to change or secure the return? |

But this comparison also falsifies a clean one-axis catalog:

- Map, Discriminate, and Discover mostly describe the **epistemic job**.
- Probe describes an **evidence-acquisition mechanism** and can be used to map,
  discriminate, or discover.
- Retrieve is often a compressed known-answer case rather than a strategy that
  needs a substantial progressively loaded SOP.

The likely next design therefore separates:

```text
what information transformation is needed?
  retrieve known answer / map structure / generate candidates / discriminate

how can evidence be accessed or produced?
  inspect/query existing sources / observe / ask / bounded probe or experiment
```

This is not yet an accepted two-axis taxonomy. Its value must be tested by
whether it creates clearer methods and stopping rules with less overlap than
the original five-item list.

## Review Disposition

Sir accepted the sufficiency model and requested continuation. `D-054` records
return adequacy plus continuation value, the qualitative Next Discriminator
test, and the satisfied/bounded-incomplete distinction. The next design step
compares the one-axis five-strategy list with a lighter epistemic-job ×
evidence-path composition, then decides which methods deserve progressive SOP
depth.
