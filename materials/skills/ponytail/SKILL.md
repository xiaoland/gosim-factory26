---
name: ponytail
description: Reduce unnecessary implementation complexity while meeting the complete approved requirement.
license: MIT; see LICENSE.
---

Understand the requested behavior and trace the relevant consumers before simplifying. Ask whether a proposed mechanism is needed now, whether this codebase already owns it, and whether the standard library, native platform or an installed dependency solves the concrete problem. Choose the first adequate option.

Keep a fix at its cause and check all affected callers. Prefer a clear shared boundary over duplicating guards or creating a speculative framework. Helpers, configuration, dependencies and fallback paths must solve an observed problem. Remove obsolete machinery rather than layering around it.

Simplicity is measured by the effort to understand and change the result. Do not sacrifice complete requirements, correctness, accessibility, security, data integrity or coherent ownership to minimize line count. Do not reduce the assigned scope or replace the design/implementation workflow with an unsolicited smaller deliverable. Validate nontrivial behavior at its meaningful boundary and state material limitations.
