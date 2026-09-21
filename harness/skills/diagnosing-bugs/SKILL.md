---
name: diagnosing-bugs
description: Build a discriminating feedback loop for a concrete failure, minimize its trigger, and repair the cause.
license: See LICENSE.
---

Start with the reported symptom, its expected behavior, and the closest available evidence. Build a feedback loop that can distinguish the failure from correct behavior: an existing test, HTTP/CLI invocation, browser journey, replay, small reproduction, property check or differential run. Choose the cheapest boundary that preserves the relevant semantics. Diagnostic signals and final acceptance may require different observations; use SVC V&V for that distinction.

Improve a noisy loop by narrowing the trigger, controlling relevant state and observing the specific symptom. For intermittent failures, identify and exercise the conditions that change its frequency. When reproduction is unavailable, state the uncertainty and use targeted evidence; an already-red test is not permission to understand the system, nor a prerequisite for investigation.

Minimize the reproduction while preserving the failure. Form competing explanations when uncertainty warrants them. Each probe should distinguish predictions: what observation would support or refute the suspected cause? Inspect relevant callers and real data paths before changing a shared function. Prefer a breakpoint or targeted boundary observation to logging everything.

Fix the cause at the meaningful shared boundary. Add a reusable regression check when it captures a real behavior/invariant worth maintaining; otherwise retain the runnable temporary evidence with its limits. Recheck the original symptom as well as the narrowed reproduction. Remove temporary instrumentation, preserve useful evidence, and report the causal finding. Keep credentials out of commands and captured output.
