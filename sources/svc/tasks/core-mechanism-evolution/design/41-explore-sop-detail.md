# Evolving Design — Explore SOP Detail

- **State**: not accepted as a whole; Step 1 preserved and the forced gleaning mapping superseded by [`design/42`](42-explore-sop-rederivation.md)
- **Consumer**: `WP × P1 / 08-DS`
- **Accepted core**: Explore finds key information through the adaptive loop in
  [`design/40`](40-explore-posture-sop.md)
- **Use**: integrate earlier gleanings, then refine one SOP step at a time
  without turning ordinary lookup into visible ceremony

## What “Key Information” Means

“Find key information” is the right coarse purpose. Information is key when it
can materially improve the current useful return, change the route toward it,
prevent a consequential false assumption, or establish that the return cannot
yet be supported.

This is deliberately broader than “answer the current question.” Exploration
may reveal that the question, vocabulary, owner, or expected return is wrong.
It is also narrower than “understand everything”: context whose absence cannot
plausibly change the return is not automatically worth loading.

## Earlier Gleanings Routed into the SOP

| Explore step | Relevant earlier gleanings | What survives provisionally |
| --- | --- | --- |
| 1. Frame | Explorer understands root purpose/motivation and may meta-plan complex retrieval; Task work is return-oriented; Human claims remain fallible | Frame the information need from the intended benefit/return, not merely the literal query; keep it revisable |
| 2. Locate authority/context | `what-rules-should-be-applied-now`; progressive loading; semantic owner resolution; semantic locality and Task Packet current truth | Resolve applicable rules and nearest authoritative neighborhood before broad loading, with extra grounding only under real risk/unknown pressure |
| 3. Seek observation | Explorer selects among `rg`, `grep`, `ast-grep`, code graph, `tree`, structured-data queries, docs, runtime probes, and other surfaces; filter noise; meta-plan retrieval | Route by question/evidence need rather than familiar tool or file volume; bound results before context import |
| 4. Test evidence | Inquiry freshness; observation versus inference; claim ladder; counterexamples/competing explanations; ablation; proposer-reviewer/independent path; product-level observation surfaces | Treat matches as navigation evidence, preserve freshness and coverage limits, and challenge consequential conclusions proportionally |
| 5. Update | Explorer is an adaptive query loop; diagnosis follows observed mismatch; forgetting is the subtraction half of learning; Plans can stop at TBC | Revise the problem model and next query, retire stale/irrelevant branches, and do not preserve the initial search plan after evidence invalidates it |
| 6. Return | compact evidence maps; proof-carrying delegation; one semantic owner with controlled Human/work projections; avoid raw evidence transfer to Human | Return synthesis, evidence horizon, material unknowns, and next discriminator to the consumer; integrate before continuing |

Several mechanisms stay outside the core SOP for now. A dedicated rules Agent,
Explorer sub-agent, fixed search-tool ladder, mandatory independent reviewer,
memory system, and ablation study are pressure-loaded realization candidates,
not universal Explore steps.

## Step 1 — Frame the Information Need

### Problem

Without a frame, the Agent commonly starts from a tool/query (“search for
`Foo`”), a broad topic (“understand authentication”), or a preferred
explanation. It then cannot distinguish a key finding from an interesting
match, cannot choose among evidence paths, and lacks a principled stopping
point.

The opposite failure is to freeze a detailed research plan before learning the
system's vocabulary and shape. The frame therefore has to guide the first
observation while remaining explicitly provisional.

### Proposed minimum move

Before non-trivial exploration, establish three things:

1. **Purpose** — what useful return, decision, or next move this information
   should enable.
2. **Material unknown** — what missing or disputed understanding currently
   makes that return unreliable.
3. **Route-changing evidence** — what kind of finding could confirm, reject,
   split, or reframe the present direction.

A compact expression is enough:

```text
To support <useful return>, find out <material unknown>;
<kind of observation> would change the current route.
```

Example:

```text
To decide where subscription-success behavior should be verified, find out
which externally observable effect consumes a subscription; evidence that the
button does not causally reach that effect would change the verification route.
```

When the domain is too unfamiliar to name route-changing evidence, the honest
first frame can be:

```text
Find the vocabulary, semantic owners, and system boundary needed to formulate
the first discriminating question.
```

That is bounded orientation, not permission to read the entire repository.

### Persistence and cost

The frame is a cognitive move, not a mandatory form or file section. Keep it
implicit for an obvious lookup. Externalize it in the applicable Plan/Inquiry
surface when exploration is long, delegated, easy to misread, expensive to
repeat, or likely to change a consequential decision.

### Step completion

Step 1 is complete when the Agent can choose a plausible first evidence path
and explain why its result could matter. It does not require a complete query
tree, fixed hypothesis set, or final stop threshold before Step 2/3 begins.

### Failure pressure

- restating the user's proposed search without recovering its intended benefit
- treating a Human/Agent solution claim as the fact to be confirmed
- naming a topic but not the uncertainty that matters
- forcing hypotheses when vocabulary and boundaries are not yet known
- planning every query before importing the first useful observation
- persisting the frame after evidence has invalidated it

## Current Review

Review only Step 1: should non-trivial Explore begin with a lightweight,
revisable frame of purpose, material unknown, and route-changing evidence, with
an orientation fallback when the domain is too unfamiliar to state a useful
discriminator?
