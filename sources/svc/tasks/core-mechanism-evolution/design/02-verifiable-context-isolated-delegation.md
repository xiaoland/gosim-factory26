# Working Note — Sub-Agent Delegation

- **State**: provisional-note
- **Source**: Sir's fallible gleanings plus bounded Lead synthesis
- **Use**: A compact heuristic when delegation is naturally relevant; not a
  protocol, schema, lifecycle, or acceptance plan

## Gleaning

Sub-agents can help long work by isolating context, but delegation has two
paradoxes:

- enough context improves the delegated result while reducing isolation value
- enough verification improves trust while reducing delegation value

The decision is therefore a cost comparison, not an Agent-utilization goal:

```text
C_total =
  C_delegate
  + C_verify
  + P(false accept) × L_error
  + P(false reject) × C_rework
```

A useful proof-carrying-code-inspired shape is:

```text
specification S + input snapshot X
  -> untrusted executor
  -> candidate Y + verification witness W
  -> independent V(S, X, Y, W)
  -> accept / reject / escalate
  -> bounded effect
```

## Current Synthesis

- Treat the sub-agent as an untrusted candidate producer, not someone to trust
  because of identity or confidence.
- Give it the smallest sufficient context and let it request a specific missing
  fact rather than copying the whole task or conversation.
- Ask for evidence tied to the returned claim. Use “proof” only when a property
  is actually mechanically checkable.
- Prefer a validator whose evidence path or oracle differs from the executor's;
  another identical-model opinion is still correlated review.
- Validation does not prove that the specification was right, the snapshot was
  complete, the result integrates, or Human product/technical taste is met.
- Limit what an unverified or partially verified result can change.
- Delegate only when context saved and useful independence exceed dispatch,
  verification, integration, and residual-error cost.

The original proof-carrying analogy is strongest for an artifact checked
against a predefined policy by a smaller checker, as in
[proof-carrying code](https://doi.org/10.1145/263699.263712). Research and design
usually carry evidence and counterexamples, not correctness certificates.

## Cost Boundary

This note also has a cost. Do not turn it into:

- mandatory packet fields or a universal delegation envelope
- new symbols, states, files, ceremonies, or validators without concrete need
- a predeclared real-task experiment or acceptance program
- a requirement to delegate simple work
- a claim that every returned result needs exhaustive independent verification

Keep this as a provisional scaffold. Preserve the parts that explain a real
design pressure, simplify parts whose complexity is not paying for itself, and
add detail only when a concrete decision needs it. Do not accept or discard the
model wholesale.
