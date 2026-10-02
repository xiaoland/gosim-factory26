---
name: svc-verification
description: Choose evidence that can distinguish a product requirement from a plausible but wrong implementation, then interpret the result and its limits.
metadata:
  version: "16.0.0"
---

# Verification

Use this skill when a requirement, check, or result may be misleading.
Before implementation, decide what observation and conditions could support or challenge the intended behavior.
After execution, decide what the actual result establishes and what should change next.

Requirements, implementation, checks, and observations are different expressions of the intended product, and each can be wrong.
A passing check supports only the behavior and conditions it actually examined.
Because feedback cost shapes what can be learned and changed next, technical design and verification design should consider observation boundaries, setup, delay, and maintenance together.

Keep four questions connected:

- What requirement or decision must the evidence support?
- What observable result and judgment rule would distinguish it from a plausible failure?
- Which inputs, state, history, boundary, and failure conditions matter?
- What does this result support, and what remains for the next decision?

Connect every conclusion to the artifact, inputs, conditions, and original evidence.
Distinguish promised outcome from diagnostic signal, and state what remains unknown when a check is interrupted, partial, stale, or narrower than the claim.

Read [check design](references/check-design.md) to turn a requirement into a discriminating judgment.
Read [evidence design](references/evidence-design.md) to choose conditions, measurement, and observation boundaries.
Read [repeatable checks](references/repeatable-checks.md) to make setup, execution, waiting, reset, and failure recording reproducible.
Read [interpreting results](references/interpreting-results.md) to decide what the result supports and what should change next.
