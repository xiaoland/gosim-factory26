# Decision Register

## Role and Protocol

This entry owns decision routing, current state, and deterministic shard
addresses. A decision records the selected meaning, authority, rationale,
consequences, and reopen/supersession boundary; it does not prove implementation
or outcome.

States are `open`, `proposed`, `accepted`, `rejected`, `deferred`, and
`superseded`. Add a successor when evidence invalidates an accepted decision;
do not rewrite history into apparent consistency.

## Register

| ID | Subject | State | Authority | Affects |
| --- | --- | --- | --- | --- |
| `D-001` | Target Human collaboration unit | accepted | Sir | All questions |
| `D-002` | Meaning of large-software support | accepted | Sir | All design |
| `D-008` | Working outcome scales and inquiry topology | accepted | Sir | Exploration method |
| `D-009` | Gleaning-led, execution-evolved design | accepted | Sir | Design method |
| `D-010` | Personal and opinionated taste target | accepted | Sir | Product scope and taste |
| `D-011` | Six-cluster sequential discussion model | superseded | Sir | Replaced by `D-012` |
| `D-012` | Five functional clusters across coupled loops | accepted | Sir | Discussion topology |
| `D-013` | Task-packet organization-pattern requirement | accepted | Sir | Task-packet cluster |
| `D-014` | Progressive composable task-packet modules | accepted | Sir | Packet composition |
| `D-015` | Work actions and non-linear postures | accepted | Sir | Protocol interface |
| `D-016` | Plan scope and organization are distinct | accepted | Sir | Planning semantics |
| `D-017` | Stable planning primitives as common ground | accepted | Sir | Human legibility |
| `D-018` | `packet.md` is the Human default surface | accepted | Sir | Human-Agent surface |
| `D-019` | Coordination is a relation view | accepted | Sir | Work topology |
| `D-020` | `packet.md` uses collaboration language | accepted | Sir | Packet writing |
| `D-021` | Derive primitives before selecting them | accepted | Sir | Planning inquiry |
| `D-022` | Planning blocks need net management value | accepted | Sir | Admission |
| `D-023` | Semantic derivation and progressive activation | accepted | Sir | Planning model |
| `D-024` | Selective task-local cache and candidate deltas | accepted | Sir | Cache/authority |
| `D-025` | Promotion targets only in meaningful planned work | accepted | Sir | Consolidation |
| `D-026` | Linear Plan may stop honestly at TBC | accepted | Sir | Plan horizon |
| `D-027` | Global Task Plan retires with Track/Phase | accepted | Sir | Large-task topology |
| `D-028` | Phase instances may declare scope | accepted | Sir | Phase semantics |
| `D-029` | Phase exits through required Cells | accepted | Sir | Barrier/Cell ownership |
| `D-030` | Phase requires a real shared barrier | accepted | Sir | Phase admission |
| `D-031` | Discussion/design exploration proceeds autonomously | accepted | Sir | Collaboration protocol |
| `D-032` | Cell defaults to one Plan | accepted | Sir | Parallel returns |
| `D-033` | Bounded Phase reopening and overlap | accepted | Sir | Invalidation/overlap |
| `D-034` | Four packet object kinds and stable growth | accepted | Sir | Module grammar |
| `D-035` | Mechanical sharding is not semantic splitting | accepted | Sir | Storage partition |
| `D-036` | Shape stabilizes at topology admission | accepted | Sir | Early owner files |
| `D-037` | Inquiry/Diagnosis epistemic family | accepted, refined | Sir | Refined by `D-043` |
| `D-038` | Inquiry carries material freshness | accepted | Sir | Evidence validity |
| `D-039` | Slice scope follows its return | accepted | Sir | Slice common ground |
| `D-040` | Design and Decision are separate modules | accepted | Sir | Information topology |
| `D-041` | Implementation is a Slice contract | accepted | Sir | Implementation boundary |
| `D-042` | Verification module; acceptance disposition | accepted, refined | Sir | Refined by `D-043` |
| `D-043` | Diagnosis is Inquiry; verification is distributed | accepted | Sir | Final packet catalog |
| `D-044` | Working Protocol semantics and Task Packet control topology | accepted | Sir | Working Protocol / Task Packet seam |
| `D-045` | Task Packet as partial persistent per-Task substrate | accepted | Sir | Protocol state / persistence boundary |
| `D-046` | Three coupled Task Packet state views and event-relative write-back | accepted | Sir | Working Protocol / Task Packet state relations |
| `D-047` | Working Posture exists to supply reusable SOPs | accepted | Sir | Working Protocol posture model |
| `D-048` | Explore finds key information through an adaptive evidence loop | superseded | Sir | Replaced by `D-049` |
| `D-049` | Preserve Explore purpose and Frame; re-derive the remaining SOP | accepted | Sir | Explore posture SOP boundary |
| `D-050` | Frame provisionally defines relevance for Explore | accepted | Sir | Explore Frame method |
| `D-051` | Route is an Explore control point, not a universal posture step | accepted | Sir | Explore core SOP and later posture comparison |
| `D-052` | Explore core SOP complete at capability-model depth | accepted | Sir | Explore posture SOP |
| `D-053` | Every Working Posture supports bounded-incomplete return | accepted | Sir | Common posture design pattern |
| `D-054` | Explore sufficiency combines return adequacy and continuation value | accepted | Sir | Explore stopping judgment |
| `D-055` | Explore uses one composed Route and progressive job methods | accepted | Sir | Explore Route and method depth |
| `D-056` | Consolidated Explore topology is faithful | accepted | Sir | Explore posture synthesis |
| `D-057` | Working Postures are stateless methods, not work lifecycles | accepted, refined | Sir | Human projection refined by `D-064`; generalized by `D-066` |
| `D-058` | Prefer foundational composable methods over an exhaustive posture catalog | accepted | Sir | Working-method basis and composition |
| `D-059` | Minimize SVC-specific common ground required for collaboration | accepted, refined | Sir | Human projection refined by `D-064` |
| `D-060` | Use Working Method, progressive guidance, semantic bootstrap, and scoped Guardrails | accepted, refined | Sir | Human projection refined by `D-064` |
| `D-061` | Model is embedded Working-Method logic, not another foundational method | accepted | Sir | Modeling logic and method basis |
| `D-062` | Generate is embedded candidate-space logic with a set-level return | accepted | Sir | Candidate-space expansion and owner boundary |
| `D-063` | Discriminate is embedded candidate-separation logic | accepted | Sir | Candidate resolution and Verification boundary |
| `D-064` | Working Methods are Agent-facing; Human collaboration uses Task semantics | accepted | Sir | Working Method / Human surface boundary |
| `D-065` | Explore is a foundational Working Method for non-obvious information needs | accepted, refined | Sir | Non-lifecycle rule generalized by `D-066` |
| `D-066` | Every Working Method is stateless and non-ritual | accepted | Sir | Universal Working Method use model |
| `D-067` | Optimize SVC Corpus wording for semantic compression | accepted | Sir | Cross-corpus writing principle |
| `D-068` | Design consumes typed forces and returns one coupled solution distinct from implementation planning | accepted, refined | Sir | Plan relation refined by `D-069` |
| `D-069` | Design adequacy is consumer-relative; representation follows collaboration and memory | accepted | Sir | Design resolution and information carrier |
| `D-070` | Design is the second foundational Working Method | accepted | Sir | Foundational method basis |
| `D-071` | Design integrates progressive guidance and specialist taste through an ownership seam | accepted | Sir | Design guidance / Taste interface |
| `D-072` | Implementation boundary and realization-feedback core are accepted | accepted, foundation open | Sir | Implementation Working Method |
| `D-073` | Implementation is the third foundational Working Method | accepted | Sir | Working Method foundation |
| `D-074` | Verification is a capability, not a foundational Working Method | accepted | Sir | Verification / Working Method seam |
| `D-075` | Three foundations are provisionally complete; derive Retrospective as composed closing guidance | accepted | Sir | Working Method basis / closing route |
| `D-076` | Retrospective is composed, pressure-triggered closing guidance | accepted | Sir | Agent work-system adaptation |
| `D-077` | Project truth integrates continuously and closes through a residual check | accepted | Sir | Semantic integration / closure |
| `D-078` | Design routes by use case and gives Test Design an independent, claim-dependent projection | accepted | Sir | Design guidance / Test Design seam |
| `D-079` | Universal Working Control is connections and laws, not another SOP or method | accepted | Sir | Working Protocol control core |
| `D-080` | Working Protocol is an operational kernel and navigation entry, not a semantic umbrella | accepted | Sir | Working Protocol domain boundary |
| `D-081` | Human collaboration uses typed meaning, semantic control, and attention-value routing | accepted | Sir | Human-Agent collaboration guidance |
| `D-082` | Specialist guidance is method-owned; protocol owns navigation and capability seams | accepted | Sir | Working Method / capability / protocol boundary |
| `D-083` | Sub-agents use two surfaces, star ownership, self-loading context, and delegated-return validation | accepted, refined by `D-085`; depth open | Sir | Sub-agent capability model |
| `D-084` | Sub-agent causal levers require distinct economic judgments | accepted; formulas open | Sir | Delegation admission and cost model |
| `D-085` | Authority star is not candidate/evidence transport | accepted, refined by `D-087` | Sir | Candidate/effect data flow |
| `D-086` | Explorer is a candidate delegated information-work contract | accepted, refined by `D-087` | Sir | Explorer / Explore seam |
| `D-087` | Delegated results follow their consumer, not one universal validation route | accepted | Sir | Report versus candidate/effect route |
| `D-088` | Minimum Sub-agent surface uses Explorer and Executor contracts | accepted | Sir | Sub-agent capability and landing |
| `D-089` | Verification is claim-relative qualification with consumer-owned disposition | accepted | Sir | Verification capability and landing |
| `D-090` | Taste is progressive, use-case-routed Design judgment | accepted | Sir | Taste/Design capability and landing |
| `D-091` | Corpus navigation uses symmetric directory entries | accepted | Sir | Source layout and progressive depth |

IDs `D-003..D-007` were withdrawn before they acquired accepted meanings.

## Deterministic Shards

Every decision maps to one fixed ten-ID range. Shards lower bounded read/edit
cost but remain one semantic module; this entry owns routing and integrated
current state.

| Range | File |
| --- | --- |
| `D-001..D-010` | [`decisions/D001-D010.md`](decisions/D001-D010.md) |
| `D-011..D-020` | [`decisions/D011-D020.md`](decisions/D011-D020.md) |
| `D-021..D-030` | [`decisions/D021-D030.md`](decisions/D021-D030.md) |
| `D-031..D-040` | [`decisions/D031-D040.md`](decisions/D031-D040.md) |
| `D-041..D-050` | [`decisions/D041-D050.md`](decisions/D041-D050.md) |
| `D-051..D-060` | [`decisions/D051-D060.md`](decisions/D051-D060.md) |
| `D-061..D-070` | [`decisions/D061-D070.md`](decisions/D061-D070.md) |
| `D-071..D-080` | [`decisions/D071-D080.md`](decisions/D071-D080.md) |
| `D-081..D-090` | [`decisions/D081-D090.md`](decisions/D081-D090.md) |
| `D-091..D-100` | [`decisions/D091-D100.md`](decisions/D091-D100.md) |

Append a new decision to its deterministic shard and update the Register row.
Create the next shard only when its first decision exists.
