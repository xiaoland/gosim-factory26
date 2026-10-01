# Telemetry Non-Subsumption Inventory

> Historical only. The list records failure-mode uniqueness at the pytest
> migration cut-over; it is superseded as an ROI decision by
> [`../90-test-topology-convergence/roi-reassessment.md`](../90-test-topology-convergence/roi-reassessment.md).
> Some listed source tests are deliberately removed there because uniqueness
> alone did not justify their cost.

## `test_telemetry_analysis.py`

- `test_an_q1_to_q10_structured_fixture` — retain: complete Q1–Q10 available-path structured analysis golden.
- `test_an_q7_missing_terminal_and_an_q10_partial_loss` — retain: unavailable terminal evidence versus tail-loss partial semantics.
- `test_an_capability_missing_dimensions_are_explicit` — retain: missing capabilities must be explicit, not fabricated empty values.
- `test_an_per_dimension_cap_and_limit_unknown` — retain: per-dimension cap and analysis-limit diagnostics.
- `test_an_validator_adversarial_and_output_bound` — retain: hostile analysis-schema rejection and output-size bound.
- `test_exact_root_and_determinism` — retain: root-key allowlist, byte determinism, size limit, and task-reference projection.
- `test_schema_validator_rejects_wrong_ids_and_cross_bundle_refs` — retain: record/bundle identity and cross-bundle reference authority.
- `test_bare_trajectory_is_not_an_analysis_authority` — retain: unmanifested trajectory input is rejected.

## `test_telemetry_archive.py`

- `test_bundle_has_exact_private_deterministic_members` — retain: exact ZIP whitelist, deterministic private bundle, and restrictive members.
- `test_collector_limit_diagnostics_use_the_actual_policy_and_attempt` — retain: collector cap uses actual policy/attempt accounting.
- `test_core_limit_preserves_provider_diagnostic_cap_accounting` — retain: core cap does not swallow provider diagnostic accounting.
- `test_ephemeral_normalization_matches_export_without_publication` — retain: preview normalization equals export without writing output.
- `test_source_race_status_is_semantic_and_partial` — retain: source-race status/result partial semantics.
- `test_output_is_absent_outside_repository_and_never_overwritten` — retain: output stays in repository and never overwrites.
- `test_replaced_output_parent_is_rejected_before_publication` — retain: parent replacement/reparse rejection before publication.
- `test_provider_errors_publish_no_artifact` — retain: provider failure leaves no artifact.

## `test_telemetry_cli.py`

- `test_export_requires_acknowledgement_then_writes_a_local_zip` — retain: export acknowledgment gate plus ZIP/redaction/manifest contract.
- `test_export_failure_redacts_source_and_output_paths` — retain: export error removes private source/output paths.
- `test_analyze_json_is_provider_independent_and_matches_direct_input` — retain: direct/bundle analysis equivalence at public CLI boundary.
- `test_analyze_flag_and_tty_matrix_fails_before_input_access` — retain: flag/TTY failure before sensitive input access.
- `test_analyze_rejects_schema_v1_before_native_member_open` — retain: CLI schema-v1 early rejection/open discipline.
- `test_analyze_source_failure_redacts_private_provider_details` — retain: analysis source-error redaction.
- `test_analyze_help_exposes_input_json_and_archive_state` — retain: public analyze-help option contract.
- `test_list_uses_safe_state_metadata_without_reading_transcript_body` — retain: list path never reads transcript body.
- `test_list_passes_archive_filter_and_projects_inventory_safely` — retain: CLI filter/limit passage and safe inventory projection.
- `test_list_help_exposes_archive_state_filter` — retain: public list-help archive-state choices.
- `test_list_omits_unsafe_rows_with_a_redacted_warning` — retain: unsafe rows omitted with stable redacted warning.
- `test_list_human_output_marks_a_degraded_inventory` — retain: degraded human rendering without private paths.
- `test_list_missing_state_database_remains_a_failure` — retain: missing state DB has a stable public failure.
- `test_list_corrupt_state_database_remains_a_failure` — retain: corrupt state DB is distinct from missing DB.

## `test_telemetry_codex_rollout.py`

- `test_codex_native_field_paths_map_to_canonical_records` — retain: native session/response field-path authority mapping.
- `test_malformed_record_is_dropped_with_partial_loss` — retain: malformed event drop and partial-loss accounting.
- `test_response_item_types_map_to_reasoning_and_tool_records` — retain: response item to reasoning/tool canonical mapping.
- `test_conflicting_session_metadata_is_rejected` — retain: conflicting session identity metadata refusal.
- `test_task_references_in_tools_and_reasoning_are_not_eligible` — retain: task-reference eligibility excludes tool/reasoning text.
- `test_list_and_exact_state_resolution_are_metadata_only` — retain: list and exact resolution avoid transcript scanning.
- `test_state_snapshot_includes_rollback_journal` — retain: SQLite snapshot includes rollback-journal identity.
- `test_state_snapshot_identity_ignores_windows_ctime_read_noise` — retain: Windows read-noisy ctime does not change identity.
- `test_state_connection_closes_a_connection_rejected_by_sqlite` — retain: connection-close ownership after SQLite rejection.
- `test_list_marks_a_missing_rollout_without_scanning_or_failing_all_metadata` — retain: one missing rollout degrades only its row.
- `test_list_is_metadata_only_and_defers_rollout_signature_to_export` — retain: list defers source signature/open to export.
- `test_list_omits_unsafe_rows_without_spending_the_safe_result_limit` — retain: unsafe rows do not spend visible limit.
- `test_list_reports_an_all_unsafe_inventory_as_degraded` — retain: all-unsafe inventory has degraded state.
- `test_list_uses_stable_descriptor_order_when_timestamps_tie` — retain: deterministic tie-break ordering.
- `test_inventory_filters_lifecycle_before_limit_and_keeps_availability_independent` — retain: lifecycle-before-limit and availability independence.
- `test_inventory_recency_fallback_units_ranges_and_display_times_are_exact` — retain: recency units/ranges/display-time exactness.
- `test_inventory_omits_invalid_ids_ambiguous_duplicates_and_unsafe_paths` — retain: invalid/ambiguous IDs and unsafe paths excluded.
- `test_inventory_path_open_is_zero_byte_and_denials_are_unavailable` — retain: zero-byte metadata open and denial semantics.
- `test_inventory_rejects_reparse_and_descriptor_identity_changes` — retain: reparse/descriptor-identity race safety.
- `test_safe_inventory_sql_never_selects_recognition_columns` — retain: safe SQL never selects recognition/private columns.
- `test_sensitive_inventory_is_separate_bounded_and_filter_before_limit` — retain: acknowledged sensitive projection is separate, bounded, and filter-first.
- `test_sensitive_inventory_preserves_controls_for_paint_only_escaping` — retain: controls are escaped only for paint.
- `test_sensitive_inventory_omits_unsafe_before_its_safe_cap` — retain: unsafe sensitive rows are filtered before cap.
- `test_sensitive_inventory_query_selects_only_frozen_private_columns` — retain: private query uses frozen-column allowlist.
- `test_safe_inventory_requires_exact_id_and_rollout_path_columns` — retain: safe SQL column shape is exact.
- `test_symlink_and_nonregular_sources_are_rejected` — retain: symlink and nonregular source refusal.
- `test_native_source_read_error_has_a_stable_provider_code` — retain: native source-read error public code.
- `test_malformed_final_record_is_refused` — retain: malformed final JSONL-record boundary.
- `test_source_replacement_during_capture_is_detected` — retain: source replacement during capture is detected.

## `test_telemetry_codex_trajectory.py`

- `test_stream_emits_stable_source_refs_and_canonical_order` — retain: stream order, IDs, and source-reference baseline.
- `test_stream_preserves_orphan_result_order_and_deterministic_ids` — retain: orphan tool-result order and deterministic linkage.
- `test_codex_passthrough_relations_context_roles_and_known_ui_loss` — retain: context/relations/roles and known UI/rate-limit loss classification.
- `test_custom_search_web_calls_pair_and_completion_cache_supplies_status_relations` — retain: custom-search/web pairing and completion-cache relation projection.
- `test_current_settings_completion_and_tool_search_shapes_are_projected_safely` — retain: current-settings/completion/tool-search safe projection.
- `test_plaintext_reasoning_summary_remains_authority_when_full_reasoning_is_opaque` — retain: plaintext summary authority with opaque full reasoning.
- `test_opaque_reasoning_emits_no_fabricated_record` — retain: opaque reasoning cannot fabricate canonical data.
- `test_stream_sink_rejection_emits_record_limit_diagnostic` — retain: stream sink rejection record-limit diagnostic.
- `test_append_after_open_is_not_collected_and_is_reported_as_grew` — retain: append-after-open physical race semantics.
- `test_tool_linkage_modes_duplicate_results_and_parent_actor_refs` — retain: mixed linkage, duplicate-result loss, and parent actor references.
- `test_task_references_scan_full_message_and_enforce_global_cap` — retain: full-message task scan and global cap/truncation.
- `test_task_reference_roots_uri_invalid_and_oversize_are_classified` — retain: root/URI/invalid/oversize task-reference classification.

## `test_telemetry_navigation.py`

- `test_provider_bounds_are_validated_without_inspecting_discarded_suffixes` — retain: bounded provider-field validation without retained suffixes.
- `test_rows_are_immutable_and_invalid_thread_ids_are_rejected` — retain: frozen row model and thread-ID trust validation.
- `test_filter_precedes_limit_and_unknown_only_appears_in_all` — retain: filter ordering and unknown-state visibility.
- `test_listing_never_retains_more_than_the_interactive_cap` — retain: interactive memory cap.
- `test_workspace_flavors_are_lexical_and_do_not_resolve` — retain: POSIX/drive/UNC lexical parsing with no traversal.
- `test_tree_groups_provider_workspace_lifecycle_and_thread` — retain: snapshot hierarchy/group order and disabled leaves.
- `test_every_thread_label_shows_title_and_first_message` — retain: visible thread-label content.
- `test_duplicate_title_falls_back_to_first_message_and_final_duplicate_index` — retain: label disambiguation/fallback.
- `test_valid_workspace_roots_precede_truncated_and_unknown_groups` — retain: workspace group ordering.
- `test_control_escaping_is_paint_only` — retain: terminal escaping preserves model values.
- `test_stale_generation_cannot_replace_newer_snapshot` — retain: stale generation cannot replace newer state.
- `test_selection_is_kept_when_new_snapshot_contains_it` — retain: selection continuity across refresh.
- `test_navigation_source_has_no_ui_provider_or_filesystem_imports` — retain: navigation dependency-boundary static contract.

## `test_telemetry_trajectory.py`

- `test_collector_is_incremental_and_canonical` — retain: incremental collector canonical bytes/hash/counts.
- `test_internal_collector_returns_bytes_and_caps_without_throwing` — retain: bounded internal collector returns rather than throws.
- `test_malformed_record_raises_stable_error` — retain: malformed-record stable error code.
- `test_validate_rejects_duplicate_keys_noncanonical_and_depth` — retain: duplicate/noncanonical/depth input rejection.
- `test_validate_requires_leading_meta_and_contiguous_ids` — retain: leading-meta and contiguous-ID structure.
- `test_event_and_tool_shapes_are_validated` — retain: event/tool schema shapes and collector counters.
- `test_relationship_hash_starting_with_d_is_not_a_duplicate_suffix` — retain: hash collision edge case.
- `test_manifest_build_and_exact_bundle_round_trip` — retain: exact manifest/bundle round trip and output-exists refusal.
- `test_manifest_generated_at_requires_a_valid_utc_second_instant` — retain: UTC-second timestamp validation matrix.
- `test_manifest_diagnostics_require_refs_order_and_coalescing` — retain: diagnostic reference order/coalescing.
- `test_schema_v1_manifest_is_rejected_before_other_member_open` — retain: schema-v1 rejection before non-manifest member access.
