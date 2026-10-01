# TUI, Installed-Wheel Harness, and Release Non-Subsumption Inventory

> Historical only. The list records failure-mode uniqueness at the pytest
> migration cut-over; it is superseded as an ROI decision by
> [`../90-test-topology-convergence/roi-reassessment.md`](../90-test-topology-convergence/roi-reassessment.md).
> Some listed source tests are deliberately removed there because uniqueness
> alone did not justify their cost.

## `test_telemetry_tui.py`

- `test_constructor_and_document_repr_are_structural` — retain: constructor shape and redacted structural representation.
- `test_lazy_tree_markup_control_escape_and_unavailable_selection` — retain: lazy tree, control escaping, unavailable selection, and available-node loading.
- `test_analysis_views_keyboard_filter_resize_and_quit` — retain: keyboard lifecycle, archive filters, analysis views, resize, and quit.
- `test_stale_inventory_and_analysis_results_are_ignored` — retain: stale concurrent results cannot replace new state.
- `test_error_and_cancel_do_not_leak_loader_values` — retain: error/cancel behavior does not leak loader values.
- `test_truncated_five_thousand_inventory_is_lazy_and_explicit` — retain: 5,000-row cap, truncation notice, and lazy materialization.
- `test_selected_marker_survives_filter_reload_and_lazy_materialization` — retain: selection marker survives filter/reload/materialization.
- `test_partial_loss_views_tools_pairing_timeline_filter_jump_and_escape` — retain: partial-loss views, tool pairing, timeline/filter/jump, escaping, and sensitive-output boundary.

## `test_accept_agent_thread.py`

- `test_argument_failures_emit_bounded_json_and_stable_code` — retain: argument failure exit code, bounded JSON, and no usage leakage.
- `test_digest_mismatch_is_validation_failure_without_temp_creation` — retain: digest failure happens before temporary creation.
- `test_sha_bound_staging_keeps_original_bytes_when_source_replaced_after_copy` — retain: source-replacement race and SHA-bound staging bytes.
- `test_wheelhouse_must_contain_binary_wheels_only` — retain: wheelhouse rejects non-wheel members.
- `test_command_runner_can_execute_a_fake_executable_without_a_shell` — retain: shell-free command execution and stdout JSON.
- `test_fake_executable_covers_each_isolated_slice` — retain: isolated inventory/bundle/analysis/UI slice result and privacy boundaries.
- `test_all_runs_inventory_bundle_analysis_then_ui` — retain: all-slice command ordering.
- `test_bundle_rejects_an_extra_archive_member_with_generic_case_failure` — retain: extra archive member rejection.
- `test_bundle_rejects_stdout_sentinel_with_generic_case_failure` — retain: stdout sentinel/private leak rejection.
- `test_bundle_requires_schema_v1_probe_to_open_only_the_manifest` — retain: schema-v1 probe opens manifest only.
- `test_install_failure_returns_five_and_still_cleans_up` — retain: install failure code, redaction, and cleanup.
- `test_installed_distribution_whitelist_rejects_workspace_leakage` — retain: installed-wheel whitelist rejects editable workspace leakage.
- `test_venv_precondition_returns_three_and_cleans_up` — retain: venv precondition failure and cleanup.
- `test_inventory_case_failure_returns_six_and_cleans_up` — retain: case failure code, cleanup, and redaction.
- `test_cleanup_failure_has_dedicated_exit_code` — retain: cleanup failure has a distinct code.

## `test_release.py`

- `test_behavioral_bumps_are_exact` — retain: major/minor/patch and illegal cross-level bump semantics.
- `test_fragments_reject_unknown_names_and_empty_content` — retain: fragment filename and empty-content validation.
- `test_repository_release_contract_is_consistent` — retain: real repository release base/target/impact smoke.
- `test_feature_pr_does_not_prebump_released_metadata` — retain: feature PR does not pre-bump released metadata.
- `test_pending_major_requires_a_separate_staged_migration_policy` — retain: major requires migration policy or reviewed non-applicability.
- `test_zero_known_adoption_exception_stages_only_the_exact_major_release` — retain: zero-known-adoption exception binds only exact target version.
- `test_zero_known_adoption_exception_rejects_patch_disguise_and_prebump` — retain: patch-disguise/pre-bump rejection.
- `test_zero_known_adoption_exception_rejects_missing_wrong_and_reused_values` — retain: missing, wrong, and reused exception values.
- `test_prepare_moves_pending_major_policy_into_the_release_and_removes_the_staging_field` — retain: prepare consumes staged migration policy.
- `test_prepare_consumes_the_zero_known_adoption_exception` — retain: prepare transfers exception into behavioral impact.
- `test_major_release_requires_packaged_guide_or_reviewable_non_applicability` — retain: major guide/non-applicability paths.
- `test_pypi_retry_accepts_only_identical_files` — retain: PyPI retry requires identical digests.
- `test_tag_plan_stays_on_the_prepared_commit_after_later_main_changes` — retain: tag plan stays bound to prepared commit.
- `test_tag_validation_rejects_wrong_tag_version_or_commit` — retain: wrong tag version/commit rejection.
- `test_release_bundle_binds_artifacts_to_the_tag_and_rejects_tampering` — retain: tag/commit/assets/digest binding and tamper detection.
- `test_pypi_bundle_plan_requires_none_or_all_matching_distributions` — retain: none/all matching distribution and mismatch/partial behavior.
- `test_prepared_release_has_no_fragments_and_has_release_notes` — retain: prepared release has no fragments and has notes.
- `test_prepared_zero_known_adoption_exception_is_immutable` — retain: prepared one-time exception cannot mutate.
- `test_pull_request_requires_fragment_or_release_none` — retain: PR release-fragment/release:none gate.
- `test_prepared_release_pr_does_not_require_a_second_pyproject_version_change` — retain: prepared release PR avoids duplicate version diff.
