# Per-Case Cost–Value Decision Ledger

## Decision Rule

This is the authoritative disposition map for the 208 native-pytest migration
baseline functions. The three historical inventories under
[`../110-pytest-migration-roi/`](../110-pytest-migration-roi/) provide the
exact function name and failure mode for every row. This file supplies the
missing cost/value decision for each of those rows.

- **Retain** means the current test's expected prevention value already clears
  its runtime, fixture, flake, maintenance, and diagnostic cost.
- **Reshape** means the behavior remains worth proving, but the current test
  shape has avoidable coupling or multi-contract setup. It remains until a
  change to the same owner makes a clearer proof positive-ROI.
- **Transfer** means a mature, maintained static gate owns the generic rule.
- **Delete** means the asserted condition itself is too editorial, historical,
  snapshot-like, or private-seam-specific to justify ongoing test cost. It is
  not necessary for another test to replace it.

The disposition is per source function, not per parametrized pytest item.

## Reconciliation

| Historical ledger | Baseline functions | Retain | Reshape | Transfer / delete | Current functions |
| --- | ---: | ---: | ---: | ---: | ---: |
| Core, framework, build, workflow | 70 | 60 | 0 | 10 | 60 |
| Telemetry | 95 | 44 | 48 | 3 | 92 |
| TUI, installed-wheel harness, release | 43 | 19 | 23 | 1 | 42 |
| **Total** | **208** | **123** | **71** | **14** | **194** |

## Core, Framework, Build, and Workflow — 60 Retain; 10 Delete/Transfer

Every exact entry in
[`../110-pytest-migration-roi/roi-core.md`](../110-pytest-migration-roi/roi-core.md)
other than the ten rows below is **retain**. These are small deterministic
tests of an externally consumed CLI/build/config/release behavior or a
filesystem/process safety boundary. Their fixtures are local, their failures
name an actionable contract, and the defect blast radius exceeds their
maintenance cost.

| Function | Decision | Cost/value conclusion |
| --- | --- | --- |
| `test_src_is_canonical_content_and_metadata_only` | Delete | Source-tree layout is an editorial repository preference, not a consumer or release safety contract; the source-text assertion churns on harmless organization changes. |
| `test_embedded_runtime_replaced_the_old_consumer_file_model` | Delete | A one-time migration-history assertion has no continuing product defect to prevent. |
| `test_no_live_runtime_or_canonical_source_claims_the_removed_commands_or_state` | Delete | Broad source wording scans have low diagnostic precision and create documentation-edit coupling without proving a running command or data boundary. |
| `test_release_metadata_is_not_a_consumer_file_inventory` | Delete | Metadata phrasing is not release behavior; the operational release command validates the actual release inputs. |
| `test_task_minimum_has_exactly_five_fields` | Delete | Exact task-packet field count is an editorial convention, not a framework runtime or consumer safety property. |
| `test_pdm_exposes_runtime_and_repository_tools_from_their_new_locations` | Delete | PDM-script layout snapshots churn with development ergonomics; the invoked build/release commands are already exercised operationally. |
| `test_root_template_and_review_budgets_remain_bounded` | Delete | Heading/text-budget assertions have low defect impact and high false-change cost. |
| `test_mutation_gate_has_one_canonical_heading` | Delete | Duplicate Markdown heading detection is editorial hygiene, not a mechanically meaningful product defect. |
| `test_query_result_boundary_accepts_an_independent_ranker` | Delete | This proves a private injection seam rather than a public lookup behavior, constraining refactors without a proportionate user consequence. |
| `test_every_external_action_is_pinned_to_a_commit` | Transfer to zizmor | Hash pinning is a generic workflow-security invariant. Offline zizmor checks it more completely and reports the offending action rather than relying on a local regex. |

## Telemetry — 44 Retain; 48 Reshape; 3 Delete/Transfer

### Retain now — 44

All exact functions in these groups are **retain**:

- all 8 in `test_telemetry_analysis.py`: deterministic public analysis,
  adversarial schema, bounded output, and authority failures;
- all 8 in `test_telemetry_archive.py`: ZIP/private-output, publication, race,
  and collector-boundary failures;
- the 12 remaining functions in `test_telemetry_cli.py`: public command,
  redaction, schema cut-off, and safe-inventory behavior; and
- these 16 `test_telemetry_codex_rollout.py` functions:
  `test_codex_native_field_paths_map_to_canonical_records`,
  `test_malformed_record_is_dropped_with_partial_loss`,
  `test_response_item_types_map_to_reasoning_and_tool_records`,
  `test_conflicting_session_metadata_is_rejected`,
  `test_task_references_in_tools_and_reasoning_are_not_eligible`,
  `test_list_and_exact_state_resolution_are_metadata_only`,
  `test_state_snapshot_includes_rollback_journal`,
  `test_state_snapshot_identity_ignores_windows_ctime_read_noise`,
  `test_state_connection_closes_a_connection_rejected_by_sqlite`,
  `test_list_marks_a_missing_rollout_without_scanning_or_failing_all_metadata`,
  `test_list_is_metadata_only_and_defers_rollout_signature_to_export`,
  `test_list_omits_unsafe_rows_without_spending_the_safe_result_limit`,
  `test_list_reports_an_all_unsafe_inventory_as_degraded`,
  `test_list_uses_stable_descriptor_order_when_timestamps_tie`,
  `test_inventory_filters_lifecycle_before_limit_and_keeps_availability_independent`,
  and `test_inventory_recency_fallback_units_ranges_and_display_times_are_exact`.

Each has a bounded fixture and an observable privacy, filesystem, archive, or
CLI consequence. Static type/structure tooling cannot produce this evidence.

### Reshape with the next owner change — 48

The behavior in every function below remains valuable; the current test is
retained. The **reshape** decision concerns its proof shape: deep provider
fixture construction, SQL/textual internals, or several unrelated assertions
make a clean refactor unnecessarily expensive today. Do not rewrite these just
to lower the count.

| Source functions | Shared cost/value conclusion |
| --- | --- |
| `test_telemetry_codex_rollout.py`: `test_inventory_omits_invalid_ids_ambiguous_duplicates_and_unsafe_paths`, `test_inventory_path_open_is_zero_byte_and_denials_are_unavailable`, `test_inventory_rejects_reparse_and_descriptor_identity_changes`, `test_safe_inventory_sql_never_selects_recognition_columns`, `test_sensitive_inventory_is_separate_bounded_and_filter_before_limit`, `test_sensitive_inventory_preserves_controls_for_paint_only_escaping`, `test_sensitive_inventory_omits_unsafe_before_its_safe_cap`, `test_sensitive_inventory_query_selects_only_frozen_private_columns`, `test_safe_inventory_requires_exact_id_and_rollout_path_columns`, `test_symlink_and_nonregular_sources_are_rejected`, `test_native_source_read_error_has_a_stable_provider_code`, `test_malformed_final_record_is_refused`, `test_source_replacement_during_capture_is_detected` | Keep the privacy/race/source behavior, but split physical-source safety from SQL projection and display details when this provider changes. |
| All 12 functions in `test_telemetry_codex_trajectory.py` | Keep stream identity, ordering, linkage, and loss evidence, but replace oversized native-event matrices with smaller frozen fixtures when the adapter changes. |
| The 12 remaining functions in `test_telemetry_navigation.py` | Keep tree/filter/selection/escaping behavior, but make the public snapshot model the oracle instead of local render/layout details when navigation changes. |
| All 11 functions in `test_telemetry_trajectory.py` | Keep canonicalization, bounds, and schema rejection, but reduce multiple validator/collector implementation seams to independent golden/adversarial proofs when the core changes. |

### Delete/transfer — 3

| Function | Decision | Cost/value conclusion |
| --- | --- | --- |
| `test_analyze_help_exposes_input_json_and_archive_state` | Delete | Exact help-option text is low-impact discoverability polish and brittle argparse layout coupling; real analysis requests and invalid-argument behavior remain tested. |
| `test_list_help_exposes_archive_state_filter` | Delete | The same low-impact help-layout concern applies; safe filter behavior is still exercised through actual list requests. |
| `test_navigation_source_has_no_ui_provider_or_filesystem_imports` | Transfer to Import Linter | This is a generic module-dependency invariant. The forbidden-import contract is broader, declarative, and fails on the actual dependency edge. |

## TUI, Installed-Wheel Harness, and Release — 19 Retain; 23 Reshape; 1 Delete

### Retain now — 19

Every remaining exact function in
[`../110-pytest-migration-roi/roi-boundaries.md`](../110-pytest-migration-roi/roi-boundaries.md)
under `test_release.py` is **retain**. Those tests exercise release-state
transitions, artifact identity, immutable versioning, or publication safety.
Their controlled filesystem/git fixtures are proportionate to the consequences
of a faulty release.

### Reshape with the next owner change — 23

All 8 functions in `test_telemetry_tui.py` and all 15 functions in
`test_accept_agent_thread.py` are **reshape**. They remain because terminal
interaction and fresh-wheel installation are unique human/package boundaries.
Their current widget IDs, synthetic schema duplication, and fake-process setup
make them costly to modify; a future TUI or harness change should consolidate
around public screen state and a small frozen installed-wheel golden. Their
behavior is not currently deleted or delegated to static analysis.

### Delete — 1

| Function | Cost/value conclusion |
| --- | --- |
| `test_repository_release_contract_is_consistent` | A snapshot of this repository's current version/fragments has high release-state churn and weak failure localization. `pdm run release check` remains the direct operational release gate, while the retained release-state tests cover the durable failure modes. |

## Resulting Rule for Future Changes

When a retained owner changes, first consult this ledger. Preserve **retain**
proofs unless its own expected value falls below cost. Improve a **reshape**
proof only when that same edit can pay for the simplification. Do not recreate
the deleted text/layout checks or custom static scanners.
