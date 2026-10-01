# Why v9.7 Needs Alignment Substrate

## The Failure Mode To Solve

Long-running human-agent collaboration does not usually drift because either side lacks raw intelligence. Drift happens because both sides stop sharing the same referential system at the right engineering granularity.

Natural language is useful for direction, but it is lossy for mutation. Phrases such as "this block", "move that logic out", "keep the API the same", or "simplify the flow" rely on visual context, local memory, and implicit scope. Those shortcuts work unevenly between humans and often fail badly between humans and agents.

The result is a recurring pattern:

- the object being discussed is underspecified
- the address is unstable or positional
- the operation verb hides side effects
- the invariant is implied rather than stated
- the context in which the request is valid is missing
- the evidence for the change is weak or absent
- the execution protocol is assumed instead of synchronized

SVC already has local answers to some of these problems, but v9.6 still treats them as separate fragments rather than one coordination model.

## Working Thesis

v9.7 should make alignment explicit as an invariant coordination grammar: the `Alignment Substrate`.

The substrate is not a new truth layer. It is a low-entropy interface between fuzzy human intent and deterministic engineering action.

The key move is not "write longer prompts." The key move is "compile intent into fields that constrain action, blast radius, and verification."

That is why the substrate is a better fit than the old "pack" framing:

- `pack` sounds like a static bundle of docs
- `substrate` better describes a reusable coordination base that can be applied across tasks, surfaces, and execution modes

## Why This Fits SVC Instead Of Fighting It

SVC already stands on several compatible ideas:

- typed input decides ownership
- tasks absorb volatility before promotion
- diagnosis must be evidence-first
- verification must be explicit
- stable anchors are justified only by real drift pressure
- progressive load is preferred over context dumping

The substrate does not replace those ideas. It gives them a common grammar.

This means v9.7 can stay source-first, minimal, and verifiable if it follows three constraints:

1. Keep durable ownership where it already belongs.
2. Load substrate detail only when drift or blast radius justifies it.
3. Bind alignment language to verification rather than rhetoric.

## Current Source Pressure

The source tree already shows why this release should be made explicit now:

- `/Users/lanzhijiang/Development/svc/src/index.md` already uses `Alignment Substrate` in part of the framework narrative.
- `/Users/lanzhijiang/Development/svc/src/sections/alignment.md` still presents the older `Alignment Pack` model.
- `/Users/lanzhijiang/Development/svc/build/monolith.md` already contains a more developed substrate-shaped draft than the source files that should own it.

That mismatch creates exactly the kind of coordination drift SVC is meant to reduce: source truth, generated artifact, and operative concept are no longer aligned.

## What The Substrate Must Not Become

### Not A New Truth Layer

`15-alignment/` should not become the place where product truth, system contracts, runtime evidence, or local invariants are duplicated.

Instead:

- PRD still owns product intent
- Product TDD still owns cross-unit technical truth
- Unit TDD and local `AGENTS.md` still own local technical boundaries and tripwires
- Tasks and Deployment still own evidence trails
- Meta Engine still owns reusable execution protocol

Alignment should own only the coordination grammar needed to point at those truths safely.

### Not Mandatory Bureaucracy

The seven coordination primitives are useful when reference drift is costly. They are harmful when forced onto every trivial task.

So v9.7 should keep MVT as the default lightweight frame, and treat substrate completion as a risk-triggered expansion path.

### Not Static Map Worship

The substrate should prefer calculable maps over hand-maintained diagrams. Stable anchors are justified when they reduce real ambiguity, not because every codebase must be pre-annotated.

## Release Intent

The release should make one durable claim:

When natural language alone is no longer enough to coordinate mutation safely, SVC provides a bounded, owner-safe substrate that turns fuzzy intent into verifiable engineering action.

## Success Conditions

v9.7 succeeds only if it does all of the following:

- gives SVC one coherent explanation for reference, mutation, boundary, and handshake discipline
- preserves existing durable owner boundaries
- upgrades alignment from a narrow helper pack into a reusable coordination grammar
- keeps the default path lightweight for ordinary tasks
- makes later source edits easier by clarifying which file owns which part of the theory
