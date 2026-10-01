# Agent-Thread Audit

- **Objective**: Audit the selected eight private Codex-thread archives as a
  bounded multi-case study, producing evidence-backed human–Agent collaboration
  patterns, counterexamples, and SVC gap hypotheses that can later become
  measurable product experiments.
- **Guardrails**:
  - Keep the ZIPs and all raw transcript, reasoning, tool payload, attachment,
    path, and title data in the private evidence store. Task material records
    only non-quoting classifications, aggregate structure, and opaque evidence
    pointers.
  - Treat the archive format as evidence to diagnose before treating it as an
    analysis substrate. Do not assume a chat-like turn model, task boundary, or
    message-role mapping without checking the exported schema.
  - Default review scope is user/assistant dialogue plus tool *category* and
    outcome signals. Reasoning and attachments are out of scope unless the
    product owner explicitly broadens review for a named hypothesis.
  - Observe at several resolutions—corpus, case, episode, turn, and event—and
    preserve the distinction between a directly observed event, a within-case
    inference, a recurring pattern, and a product hypothesis.
  - A selected corpus is not a prevalence sample. Do not use occurrence counts
    as population statistics or treat a single vivid episode as a universal
    failure mode.
  - A thread is an observation window, not the complete project history.
    Absence from its exported records is never proof that a project artifact,
    decision, or control mechanism did not exist elsewhere.
  - The audit changes no SVC runtime behavior. Each supported SVC gap receives
    a separate owner and task packet before implementation.
- **Verification**:
  - Archive anatomy and segmentation affordances are documented for all eight
    archives without exposing content.
  - Every case card uses explicit non-quoting evidence pointers and records
    outcome/uncertainty, not only a narrative summary.
  - A reported pattern has at least two independent supporting cases, a stated
    boundary or counterexample search, and an evidence-strength label; an
    otherwise useful single case remains a candidate hypothesis.
  - Every proposed SVC gap states the affected collaboration mechanism, why
    SVC rather than a project-local practice owns it, a smallest intervention,
    and a measurable validation experiment.
  - Audit notes, task packets, and final handoff contain no raw excerpts or
    sensitive operational values.
- **Current Truth**:
  - The private corpus contains eight exact-thread ZIPs: three macOS, two
    WSL/Linux, and three Windows. Each passed exact-source consistency checks,
    has a matching SHA-256/size record, and is mode `0600` in the central
    evidence root.
  - All eight share a core layout: a provider-native rollout stream, a
    timestamped thread index, and a manifest. One SVC case additionally carries
    associated task-packet files; the other seven have no attached packet
    material.
  - All eight ZIP CRC checks pass; every manifest record count matches its
    rollout stream and its index length, no malformed JSONL line was found, and
    the native/index timestamps are non-decreasing. These facts make a bounded,
    reproducible structural pass possible before semantic review.
  - The index records line number, byte count, digest, timestamp, and record
    type for every native event. It supports chronology and structural
    segmentation but deliberately does not expose semantic message role/text;
    those require bounded raw-rollout review.
  - Native records include message, response-item, turn-context, compaction,
    world-state, session, tool-completion, and multi-agent coordination forms.
    Turn IDs, event IDs, role/status/phase, call IDs, and coordination triggers
    are candidate boundary signals. Their presence establishes candidate—not yet
    validated—episode boundaries.
  - The methodological synthesis selects a multi-resolution method stack:
    event-log navigation; within-case process traces; distributed-state maps of
    Human, Agent, Artifact, and Environment; recovery analysis where needed;
    and cross-case replication/counterexample reading. The stack is documented
    with explicit non-uses so that a selected eight-case corpus cannot become
    accidental prevalence or hidden-cognition research.
  - The product owner asked to evolve this protocol while discussing it. The
    archive anatomy and method lenses are therefore provisional working
    material, not a finished audit conclusion.
  - The product owner accepted the default unit boundaries, reading scope, and
    claim threshold on 2026-07-20. All eight cases have accepted anonymous
    cards. The pilot's outcome-evidence, packet-relation, and terminal-coverage
    discipline survived the maximum-variation wave after pointer/status review.
  - Cross-case synthesis distinguishes current SVC-aligned strengths from three
    experiment candidates. No claim currently reaches the threshold for a
    proposed SVC gap or runtime change.
- **Next Step**: Decide whether to close this audit at its evidence handoff or
  open one separately scoped experiment for `H1` (evidence status), `H2`
  (current-work state), or `H3` (telemetry terminal coverage).

## Supporting Material

- [Observed archive anatomy and segmentation questions](archive-anatomy.md)
- [Evidence-informed method stack](method-lenses.md)
- [Draft multi-resolution coding protocol](coding-protocol.md)
- [Two-case pilot design](pilot-plan.md)
- [Content-free structural corpus map](corpus-map.md)
- [Privacy-preserving case-card template](case-cards/case-card-template.md)
- [Accepted pilot case card: `SVC-A`](case-cards/svc-a.md)
- [Accepted pilot case card: `OPS-B`](case-cards/ops-b.md)
- [Accepted case card: `REC-E`](case-cards/rec-e.md)
- [Accepted case card: `NET-C`](case-cards/net-c.md)
- [Accepted case card: `DIAG-D`](case-cards/diag-d.md)
- [Accepted case card: `WIN-F`](case-cards/win-f.md)
- [Accepted case card: `WIN-G`](case-cards/win-g.md)
- [Accepted case card: `WIN-H`](case-cards/win-h.md)
- [Pilot retrospective and protocol changes](pilot-retrospective.md)
- [Case coverage and claim-status tracker](coverage.md)
- [Cross-case synthesis and candidate experiments](cross-case-synthesis.md)
