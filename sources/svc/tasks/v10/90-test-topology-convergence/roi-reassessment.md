# Cost–Value Reassessment

## Correction

The earlier family ledger used “not fully subsumed by another test” as its
deletion bar. That is necessary evidence for a safety-sensitive dynamic test,
but it is not ROI. A unique test can still be too cheap a defect, too coupled
to an internal representation, or too expensive to maintain to justify its
existence.

The decision unit is one source test function, not pytest's parametrized
execution-item count.

## Rubric

Keep a test only when the expected value of catching its defect before a user
or release exceeds all of these costs:

1. likelihood and blast radius of the defect;
2. detection advantage over type checking, packaging, a mature static gate,
   or an already-run operational command;
3. local/CI time, fixture size, nondeterminism, and maintenance coupling; and
4. diagnostic clarity when it fails.

Static gates own only generic structural rules. They cannot replace dynamic
privacy, path-race, archive, transaction, installed-wheel, or terminal proofs.

## Audited Result

| Decision | Source functions | Meaning |
| --- | ---: | --- |
| Retain current behavioral proof | 123 | High consequence dynamic or public-contract evidence with proportionate cost. |
| Reshape when its owner next changes | 71 | The behavior is valuable, but the current fixture, internal assertion, or multiple-contract shape is needlessly costly. |
| Remove or transfer now | 14 | Low-value text/layout/snapshot checks, or a generic structural rule now owned by a mature gate. |
| **Original total** | **208** | |

The 14 removals/transfers are:

1. `test_src_is_canonical_content_and_metadata_only`;
2. `test_embedded_runtime_replaced_the_old_consumer_file_model`;
3. `test_no_live_runtime_or_canonical_source_claims_the_removed_commands_or_state`;
4. `test_release_metadata_is_not_a_consumer_file_inventory`;
5. `test_task_minimum_has_exactly_five_fields`;
6. `test_pdm_exposes_runtime_and_repository_tools_from_their_new_locations`;
7. `test_root_template_and_review_budgets_remain_bounded`;
8. `test_mutation_gate_has_one_canonical_heading`;
9. `test_query_result_boundary_accepts_an_independent_ranker`;
10. `test_analyze_help_exposes_input_json_and_archive_state`;
11. `test_list_help_exposes_archive_state_filter`;
12. `test_navigation_source_has_no_ui_provider_or_filesystem_imports`;
13. `test_every_external_action_is_pinned_to_a_commit`;
14. `test_repository_release_contract_is_consistent`.

Items 12 and 13 transfer their structural/security authority to Import Linter
and zizmor respectively. The other twelve do not protect a sufficiently
consequential runtime or consumer behavior to justify their maintenance cost;
they are not replaced with a home-grown checker.

The exact per-function mapping—including the 123 retained and 71 deferred
reshape decisions—is in [`roi-decision-ledger.md`](roi-decision-ledger.md).

## Measured Cost

Before the cut, `pdm run pytest -q --durations=0` completed 268 execution
items in 12.46 seconds. The eight Textual tests consumed about 9.1 seconds;
their scenarios remain because they cover a real human interaction boundary.
The core and telemetry portions are fast (about 1.30 and 0.24 seconds
respectively), so their ROI failures are mostly brittle implementation coupling
and cognitive cost, not runtime.

## Reshape Boundary

The 71 reshape entries do not become automatic deletion candidates. Examples
include table-driven parser and error-envelope cases, release state-machine
fixtures, provider shape matrices, and TUI tests that currently inspect private
widgets. Their behavioral contracts remain valuable; a future edit must improve
their proof shape only when it has a positive marginal return.
