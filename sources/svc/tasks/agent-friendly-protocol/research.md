# Research Synthesis

This file records primary evidence, its limits, and candidate implications.
It is not a product specification.

## Evidence Questions

1. Which representations help language models identify state, errors,
   references, and available next moves reliably without unnecessary tokens?
2. When does a closed structured result outperform concise text, and when does
   it obscure the command's native evidence?
3. How should a command relate intent, progress, captured output, diagnostics,
   terminal state, and durable references across Agent and Human callers?
4. What truncation, pagination, or indirection preserves both bounded context
   and recoverable evidence?
5. Which protocol properties improve Human handoff instead of optimizing only
   an isolated Agent call?

## Research Standard

- Prefer papers, official specifications, official source, and directly
  observed SVC/consumer behavior.
- Record the study or tool setting, not only its conclusion.
- Separate observed fact, within-source claim, candidate mechanism, SVC
  hypothesis, and approved decision.
- Seek counterexamples before promoting a recurring protocol rule.

## Approved Common Contract

No primary evidence supports a universal "JSON is Agent-friendly" rule, and no
paper found performs a fair compact-JSON versus prettified-JSON comparison for
CLI observations. Sir approved semantic routing rather than one universal
envelope, then corrected the first formulation to include presentation itself.
The common contract has two inseparable layers:

1. **Information selection** decides what belongs inline, what is omitted, and
   what remains recoverable through a reference.
2. **Presentation shaping** decides the grammar, ordering, grouping, labels,
   density, framing, channels, and continuation form through which an Agent or
   Human perceives that information.

Presentation is not decoration. A semantically identical result can produce a
different Agent action when relationships are obscured, decisive facts appear
late, records are hard to compare, or framing resembles an unrelated familiar
format.

Each form is selected under three simultaneous pressures:

| Pressure | Questions that shape the form |
| --- | --- |
| Content semantics | Is this an atomic fact, comparable list, hierarchy, diff, diagnostic, receipt, exact native content, or live event sequence? Are order, fidelity, uncertainty, and provenance meaningful? |
| Agent characteristics | Will the result be scanned or parsed? What structures are familiar to the model? Can its shell/tool wrapper merge channels, truncate output, or add framing? Does the Agent have `jq`, `rg`, refs, cursors, or file reads for follow-up? How likely are positional loss, accidental inference, and model-specific format bias? |
| Information-service purpose | Is the caller meant to discover, select, compare, execute, continue, diagnose, verify, audit, or hand off? Which relationship must be recognized and which valid next move should become easier? |

The resulting topology remains:

```text
caller intent -> command/action -> observable effect -> terminal disposition
                                      |                    |
                                      +-> native evidence  +-> bounded result
                                              |                    |
                                              +---- stable reference +
```

The result needs enough information for the caller's intended information move.
Detailed or long-lived evidence should remain recoverable without being copied
into every result. The form must then make the decisive facts and relationships
easy for the intended consumer to perceive; selecting the right facts but
presenting them poorly is still a protocol failure.

## Presentation Dimensions

The three pressures may change any of these dimensions without requiring one
global output mode:

- **Grammar**: raw content, concise labeled text, delimiter-oriented rows,
  compact JSON, or JSONL events.
- **Linear layout**: fact order, grouping, repetition, indentation, and where
  summary, evidence, qualification, and continuation appear.
- **Salience**: which status, difference, error, identifier, or next operation
  is made immediately recognizable without decorative emphasis.
- **Framing and attribution**: boundaries between SVC facts, native child
  evidence, warnings, errors, progress, and terminal result.
- **Channel and lifecycle**: stdout, stderr, exit status, settled value, live
  stream, or referenced material.
- **Progressive detail**: inline value, preview, stable reference, cursor, or a
  separately addressable captured stream.

These are design dimensions, not features to expose indiscriminately. The
simplest form that satisfies the three pressures wins.

## Primary Research Evidence

### Interface design changes Agent performance

The NeurIPS 2024
[SWE-agent paper](https://proceedings.neurips.cc/paper_files/paper/2024/file/5a7c947568c1b1328ccc5230172e1e7c-Paper-Conference.pdf)
tested an Agent-computer interface on SWE-bench Lite. Its 18.0% baseline fell
to 12.0% with iterative search, 12.7% when a viewer returned a full file, 15.0%
without edit linting, and 15.0% with full rather than bounded observation
history. The paper also made silent command success explicit and returned
specific rejected-edit feedback. This supports informative, bounded,
action-adjacent observations and recoverable errors.

The boundary matters: SWE-agent's repository search and edit tools are not
evidence that SVC should replace `rg`, `ast-grep`, editors, or project tools.
Only the command/observation findings are relevant here, and the study used
2024 models and one software-engineering benchmark.

[ReAct](https://arxiv.org/abs/2210.03629) and
[Toolformer](https://arxiv.org/abs/2302.04761) likewise keep an action and its
observation/result explicitly adjacent. They support stable action-result
framing, but neither compares JSON with concise text or studies ordinary CLI
stdout/stderr.

### Complex JSON is not automatically easy for an LLM

The EACL 2026 study
[How Good Are LLMs at Processing Tool Outputs?](https://aclanthology.org/2026.eacl-long.134/)
evaluated 15 models over 1,298 questions derived from real API JSON responses.
The responses averaged roughly 24,000 to 74,000 characters. The best reported
GPT-4o accuracy was 77%; changing the processing strategy produced differences
from 3% to 50%; adding schema information improved some settings by up to 12%.
Direct answer generation worked better for simple extraction in many models,
while generated parsing code worked better for filtering and aggregation. An
oracle simplification of the JSON improved every tested model.

This is strong evidence that output nature, size, and required reasoning should
select the representation and processing path. It is not evidence that SVC's
small compact receipts are harmful: the study's inputs were much larger and it
isolated question-answering rather than end-to-end Agent work.

Research on models *producing* structured output is also deliberately treated
as a warning, not as direct CLI evidence. EMNLP 2024's
[Let Me Speak Freely?](https://aclanthology.org/2024.emnlp-industry.91/)
found reasoning degradation under stricter output restrictions, while a 2026
[causal re-analysis](https://aclanthology.org/2026.findings-eacl.91/) found no
causal effect in 43 of 48 tested scenarios and greater resilience in newer
reasoning models. These results reinforce that format effects are
model-, task-, and method-dependent.

### Stable structure helps only where structure is consumed

[XGrammar](https://arxiv.org/abs/2411.15100) shows that grammar-constrained
decoding can make JSON/function-call syntax reliable with low optimized
serving overhead. [API-Bank](https://aclanthology.org/2023.emnlp-main.187/)
shows that wrong tool names, parameters, order, and unparsable calls are
distinct failure modes. These support strict schemas and stable names at a
machine boundary. They do not imply that narrative evidence or native test
output should be wrapped in JSON.

The ICLR 2025 [tau-bench](https://arxiv.org/abs/2406.12045) found native
function calling more reliable than its text-formatted action variants in its
retail and airline environments, while repeated reliability dropped sharply
with `pass^k`. It also attributed 95.9% of measured model cost to input,
including prompt and function definitions, rather than completion. This is a
warning against large universal schemas and should not be misreported as a
compact-payload experiment.

### Current protocols preserve more than one representation

The current
[MCP 2026-07-28 Tools specification](https://modelcontextprotocol.io/specification/2026-07-28/server/tools)
allows text or other unstructured content alongside optional schema-validated
structured content. It also uses resource links, explicit state handles, and
actionable tool-execution errors. The specification says implementations may
choose their own interaction model. MCP therefore supplies useful protocol
precedents, not a reason for SVC to copy its feature set or JSON-RPC envelope.

The official
[Agent Skills integration guide](https://agentskills.io/client-implementation/adding-skills-support)
loads only name and description for discovery, then the selected `SKILL.md`,
then referenced resources on demand. It explicitly says XML, JSON, or a bullet
list can all represent the initial catalog. The useful idea is progressive
disclosure and a resolvable location, not one serialization format.

Microsoft's current
[Playwright CLI](https://github.com/microsoft/playwright-cli) is explicitly
designed for coding Agents. Its normal action result reports the current page
and links to a saved snapshot; the Agent can read or search that snapshot when
needed. It is distributed with a Skill and claims CLI+Skill avoids loading the
larger MCP tool schemas and accessibility trees. Vercel's
[agent-browser](https://github.com/vercel-labs/agent-browser) similarly uses
compact accessibility text and short element references by default, with JSON
as an option. These are relevant implemented precedents, but their token and
reliability claims are project-authored rather than independent evaluations.

Codex, Claude Code, and Gemini CLI all separate terminal text, one settled JSON
result, and/or a JSONL event stream by caller need. In particular,
[Codex non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode)
uses stderr for progress, stdout for the final answer, JSONL for the full event
stream, and a requested JSON Schema only for a downstream structured final
answer. This is evidence of semantic mode separation, not evidence that SVC
needs another global format switch.

## Real SVC and Consumer Evidence

- Current SVC CI parses only `plan_digest` from `svc init --json`, applies that
  exact plan, and then uses Human text for the final status
  (`.github/workflows/ci.yml:83-93`). This is a real consumer of a stable compact
  machine field; converting the plan to prose would make the flow worse.
- The SVC repository's direct `pdm run test` output was already useful native
  evidence: pytest supplied progress, failure locality, and a compact terminal
  summary. Wrapping that evidence would add no meaning. The completed run unit
  correctly keeps native output separate from the SVC receipt.
- Historical Beluna acceptance showed the opposite need: AIMock could fail
  before Beluna produced a case receipt, leaving the command evidence only in
  the initiating Agent's context and prose handoff. A shared SVC execution ID
  made that existing output addressable without interpreting Beluna artifacts.
- The eight-case Agent-thread audit repeatedly separated command/tool
  completion, local verification, external observation, Human acceptance, and
  missing terminal evidence. A completion marker without captured outcome had
  to remain `unknown`; output protocol must not turn transport completion into
  a semantic success claim.
- Direct 2026-08-06 dogfood on this worktree confirmed that different current
  outputs already have different useful shapes: `lookup --keyword` returned a
  compact path/title/score/excerpt list; `run --inspect` returned one concise
  text line or one compact receipt; `status` returned a Human checklist or one
  compact preflight object.

## Current SVC Friction Candidates

These are implementation facts and hypotheses for discussion, not an approved
scope:

1. JSON errors have three shapes: CLI grammar errors are flat
   `code/message`; ordinary `SvcError` uses `schema_version/error`; analysis
   protocol errors are another flat `code/message/details` shape. All are
   compact and on stderr, but a cross-command consumer cannot parse one common
   minimum.
2. Text errors can contain a prettified JSON details block between the concise
   error and hint. The hybrid is neither the smallest Human diagnostic nor the
   preferred compact JSON machine result.
3. The generic text emitter for several `dev` and apply results prints only
   `command/status/changed`, even when the underlying result contains the facts
   needed to understand or continue the operation.
4. `svc status` still exposes `requires_human_authorization` and makes
   authorization the first unadopted next action. This conflicts with the
   product direction recorded for this unit: SVC should improve Agent-Human
   collaboration but not own the Human-Agent permission protocol.
5. Command discovery is uneven. Lookup supplies a two-step path-oriented hint,
   analysis exposes schemas, but `svc run --help` gives no semantics for entry,
   follow, inspect, text/native channels, or receipt behavior. Loading the full
   corpus should not be required to recover any public CLI usage or result
   semantics: `svc lookup` serves SVC framework knowledge, not documentation
   for the CLI that delivers and operates it.

## Hypotheses to Test

- **H1 — three-pressure form fit**: content, a bounded receipt, a diagnostic,
  and a live/native stream should use forms shaped jointly by their semantics,
  Agent characteristics, and service purpose; a universal envelope would add
  complexity and bury native authority.
- **H2 — decision-sized primary result**: the default result should contain
  only the facts needed to interpret this action and select a next move, with a
  stable reference for evidence that is large, persistent, or independently
  owned.
- **H3 — explicit evidence horizon**: command settlement, SVC state, project
  result, and acceptance must remain distinguishable. Partial, unavailable, or
  missing observations must not be promoted to success.
- **H4 — recoverable failure**: a failure should expose a stable kind, the
  smallest relevant cause, and a valid correction or continuation when one is
  mechanically known; it should not emit generic advice when SVC does not know.
- **H5 — contextual efficiency, not character counting**: evaluate task
  success, recovery turns, unnecessary rereads, handoff quality, and repeated
  reliability. Token/byte counts are diagnostic measures, not the product
  outcome.
