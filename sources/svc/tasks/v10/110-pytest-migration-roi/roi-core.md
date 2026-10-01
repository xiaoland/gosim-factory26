# Core, Framework, Build, and Workflow Non-Subsumption Inventory

> Historical only. The list records failure-mode uniqueness at the pytest
> migration cut-over; it is superseded as an ROI decision by
> [`../90-test-topology-convergence/roi-reassessment.md`](../90-test-topology-convergence/roi-reassessment.md).
> Some listed source tests are deliberately removed there because uniqueness
> alone did not justify their cost.

## `test_build_monolith.py`

- `test_depth_first_traversal_and_anchor_rewrite` — retain: depth-first source order and anchor rewrite.
- `test_reference_style_links_ignore_code_fences` — retain: fenced text is not parsed as a reference link.
- `test_missing_local_markdown_target_fails` — retain: missing local target boundary.
- `test_missing_local_markdown_fragment_fails` — retain: cross-document missing fragment boundary.
- `test_same_document_missing_fragment_fails` — retain: same-document missing fragment boundary.
- `test_reference_style_missing_target_fails` — retain: reference-style missing target boundary.
- `test_undefined_reference_label_fails` — retain: undefined reference-label rejection.
- `test_local_markdown_target_cannot_escape_root` — retain: local-link root-escape safety.
- `test_percent_encoded_local_markdown_path_resolves` — retain: percent-encoded local-path resolution.

## `test_catalog.py`

- `test_catalog_is_deterministic_and_covers_every_canonical_markdown_document` — retain: deterministic catalog, corpus coverage, digest, and no-body projection.
- `test_wheel_projection_contains_catalog_and_one_copy_of_each_document` — retain: wheel has exactly one projected copy of each resource.
- `test_pdm_hook_projects_only_runtime_catalog_resources_for_a_wheel` — retain: PDM hook runtime-resource boundary.
- `test_src_is_canonical_content_and_metadata_only` — retain: canonical source/runtime code separation.

## `test_cli.py`

- `test_lookup_machine_output_uses_source_relative_path_identity` — retain: public lookup JSON path/content identity.
- `test_init_cli_is_plan_first_and_requires_its_exact_digest_to_apply` — retain: plan-first digest binding.
- `test_dev_identity_and_missing_configuration_status_are_machine_readable` — retain: machine-readable identity and invalid-configuration contract.
- `test_dev_setup_cli_is_plan_then_exact_apply` — retain: setup plan/apply and consumer-content retention.

## `test_config.py`

- `test_complete_strict_base_and_stable_declaration_digests` — retain: strict fields, profile/version, and declaration digest.
- `test_parser_rejects_duplicate_nonfinite_invalid_utf8_and_null` — retain: hostile/invalid configuration bytes are rejected.
- `test_sparse_overlay_merges_objects_and_replaces_scalars_and_arrays` — retain: overlay merge semantics and digest.
- `test_absent_overlay_is_noop_and_effective_config_is_not_written` — retain: no-overlay no-write behavior.
- `test_overlay_refuses_adoption_authority_unknown_paths_and_invalid_effective_values` — retain: overlay authority and effective-value validation.
- `test_non_files_and_symlinks_are_refused` — retain: non-file and symlink refusal.
- `test_scope_and_discriminated_models_enforce_bounded_contract` — retain: scope, discriminator, and timeout bounds.

## `test_dev_identity.py`

- `test_linked_worktrees_are_distinct_but_share_common_repository_identity` — retain: worktree and common-repository identity distinction.
- `test_non_git_fallback_and_scope_specific_lock_identity` — retain: non-git fallback and scope-specific locking identity.
- `test_interpolation_is_constrained_and_provenance_requires_resolved_instance` — retain: constrained interpolation and fail-closed provenance.

## `test_dev_runtime.py`

- `test_http_probe_enforces_loopback_and_treats_redirect_as_an_observation` — retain: loopback/SSRF boundary and redirect observation.
- `test_http_probe_pins_the_validated_address_instead_of_resolving_again` — retain: validated-address pinning against a second DNS resolution.
- `test_tcp_and_exec_probes_have_bounded_declared_behavior` — retain: declared TCP/exec probe bounds.
- `test_worktree_scope_refuses_static_probe_and_manual_never_provisions` — retain: scope, static-probe, and manual-provisioning policy.
- `test_owned_early_exit_reports_only_attempt_cleanup` — retain: owned-process early-exit cleanup report.
- `test_concurrent_ensure_starts_once_then_reuses_the_declared_server` — retain: concurrent exactly-once launch and reuse.
- `test_keyboard_interrupt_cleans_up_only_the_current_launch` — retain: interrupt cleanup ownership.
- `test_activation_timeout_is_structured_and_cleans_its_owned_group` — retain: structured timeout and owned process-group cleanup.

## `test_dev_setup.py`

- `test_vscode_jsonc_insert_is_surgical_idempotent_and_leaves_launch_untouched` — retain: surgical JSONC edit, idempotence, and launch preservation.
- `test_vscode_edited_marker_or_reserved_label_blocks_without_writing` — retain: modified marker/reserved-label fail-closed behavior.
- `test_npm_is_root_only_surgical_conflict_safe_and_preserves_mode` — retain: root-only npm update, conflict safety, and mode preservation.
- `test_plan_digest_binds_config_and_destination_bytes` — retain: plan binds configuration and destination bytes.
- `test_vscode_parent_symlink_swap_after_planning_is_stale_and_writes_nothing` — retain: parent-symlink TOCTOU rejection.

## `test_framework_contract.py`

- `test_all_canonical_markdown_links_resolve` — retain: every canonical Markdown link resolves.
- `test_embedded_runtime_replaced_the_old_consumer_file_model` — retain: old consumer-file model removal and runtime locations.
- `test_no_live_runtime_or_canonical_source_claims_the_removed_commands_or_state` — retain: no stale command/state claim remains in live source.
- `test_release_metadata_is_not_a_consumer_file_inventory` — retain: release metadata shape boundary.
- `test_task_minimum_has_exactly_five_fields` — retain: task packet’s exact five-field contract.
- `test_pdm_exposes_runtime_and_repository_tools_from_their_new_locations` — retain: PDM projection of runtime/repository tools.
- `test_root_template_and_review_budgets_remain_bounded` — retain: required headings and bounded review text.
- `test_mutation_gate_has_one_canonical_heading` — retain: one canonical Mutation Gate heading.

## `test_lookup.py`

- `test_name_is_full_path_regex_and_ambiguity_requires_all` — retain: full-path regex identity and ambiguity policy.
- `test_keyword_is_deterministic_and_returns_paths_not_copied_bodies` — retain: deterministic keyword result and path-only privacy projection.
- `test_query_result_boundary_accepts_an_independent_ranker` — retain: independent ranker boundary.
- `test_invalid_regex_and_tampered_corpus_are_explicit_failures` — retain: invalid regex and tampered-corpus failures.

## `test_project.py`

- `test_init_is_deterministic_plan_first_and_idempotent` — retain: deterministic, plan-first, idempotent initialization.
- `test_init_preserves_unmarked_consumer_content_and_creates_docs_index` — retain: consumer-owned content preservation and docs index creation.
- `test_modified_skill_or_navigation_blocks_without_overwrite` — retain: modified generated block is not overwritten.
- `test_unowned_existing_skill_is_never_replaced` — retain: unowned existing skill refusal.
- `test_stale_plan_and_commit_or_postcondition_failure_leave_no_partial_project_tree` — retain: stale/commit/postcondition atomic rollback.
- `test_rollback_does_not_overwrite_an_intervening_consumer_change` — retain: rollback does not clobber an intervening consumer change.
- `test_status_distinguishes_adoption_and_adopt_updates_only_project_metadata` — retain: status/adopt metadata authority boundary.
- `test_init_manages_only_a_clean_local_config_ignore_section` — retain: bounded `.gitignore` ownership.
- `test_schema_v1_blocks_writes_and_v2_adopt_preserves_consumer_bytes` — retain: schema-v1 fail-closed and v2 byte-preserving adoption.
- `test_invalid_local_overlay_blocks_init_without_rewriting_it` — retain: invalid local overlay blocks without rewrite.
- `test_apply_preserves_existing_consumer_file_mode_and_rejects_mode_drift` — retain: consumer file-mode preservation and drift rejection.

## `test_update.py`

- `test_pip_plan_is_explicit_and_editable_or_unknown_installers_block` — retain: installer trust policy.
- `test_apply_requires_exact_unchanged_plan_and_verifies_in_a_fresh_interpreter` — retain: exact plan binding and fresh-interpreter verification.

## `test_workflows.py`

- `test_every_external_action_is_pinned_to_a_commit` — retain: immutable action SHA pinning.
- `test_ci_is_read_only_locks_before_install_and_smokes_the_embedded_runtime_wheel` — retain: CI ordering, lock, read-only, and wheel-smoke contract.
- `test_release_pr_uses_builtin_token_and_prepares_a_checked_lockfile` — retain: release-PR token and checked-lock preparation.
- `test_release_tag_binds_only_a_merged_release_candidate_to_its_merge_sha` — retain: tag binding to merged candidate SHA.
- `test_publish_is_tag_bound_builds_once_and_hands_the_bundle_to_downstream_jobs` — retain: tag-bound single build and downstream bundle handoff.
