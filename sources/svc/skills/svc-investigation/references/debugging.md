# Debugging

Use this guidance for a concrete failure whose cause is not yet established.

Start with the reported symptom, expected behavior, and closest available evidence. Build a feedback loop that distinguishes failure from correct behavior: an existing test, HTTP or CLI invocation, browser journey, replay, small reproduction, property check, or differential run. Choose the cheapest boundary that preserves the relevant semantics. Diagnostic signals and final acceptance may require different observations; use the verification skill for that distinction.

When the symptom is a check result, preserve the artifact, inputs, conditions, first concrete failure, and the assertion that was expected to run. Use the verification skill's result interpretation to decide whether the next discriminator targets the product, the check, the environment, or the requirement.

Preserve the original action’s exit status and first error before filtering its output.
An empty formatting or search result does not establish that the source object is absent or unchanged; inspect the unfiltered result or an available structured interface.

Improve a noisy loop by narrowing the trigger, controlling relevant state, and observing the specific symptom. For intermittent failures, identify and exercise the conditions that change its frequency. When reproduction is unavailable, state the uncertainty and use targeted evidence; an already-red check is neither permission to understand the system nor a prerequisite for investigation.

Minimize the reproduction while preserving the failure. Form competing explanations when uncertainty warrants them. Each probe should distinguish predictions: what observation would support or refute the suspected cause? Inspect relevant callers and real data paths before changing a shared function. Prefer a breakpoint or targeted boundary observation to logging everything.

Fix the cause at the meaningful shared boundary. Add a reusable regression check when it captures a real behavior or invariant worth maintaining; otherwise retain runnable temporary evidence with its limits. Recheck the original symptom as well as the narrowed reproduction. Remove temporary instrumentation, preserve useful evidence, and report the causal finding. Keep credentials out of commands and captured output.
