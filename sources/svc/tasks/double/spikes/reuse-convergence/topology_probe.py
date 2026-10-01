"""Map every current double-related pytest case to exactly one proposed owner."""

from __future__ import annotations

import subprocess
import sys
from collections import Counter
from hashlib import sha256


CURRENT_TARGETS = (
    "svc_cli/tests/double",
    "svc_cli/tests/test_execution.py::test_publish_classifies_execution_directory_creation_failure",
    "svc_cli/tests/test_execution.py::test_double_execution_requires_merged_capture_and_can_be_released",
)

BASELINE_CASE_DIGEST = (
    "8c0b2e1b78328b5c4d46c5afecd578244d6e2b0bb1770650ca0348db27325231"
)
POST_MIGRATION_CASES = {
    "test_tagged_ir_rejects_cross_variant_and_missing_fields",
    "test_tagged_ir_round_trip_preserves_the_serialized_contract",
    "test_missing_local_openapi_pointer_is_rejected_by_registry",
    "test_unselected_remote_openapi_reference_is_not_scenario_authority",
    "test_cel_profile_inspection_freezes_the_dynamic_map_limitation",
    "test_cel_profile_compilation_evaluation_and_regex_share_one_environment",
}

INTERFACE = {
    "test_double_validate_json_human_and_exit_contract": "double/interface/test_cli.py",
    "test_double_start_rejects_non_rfc3339_fixed_clock_on_stderr": "double/interface/test_cli.py",
    "test_double_cli_preserves_typed_failures_and_safely_classifies_bugs": "double/interface/test_cli.py",
    "test_double_help_and_schemas_are_self_contained": "double/interface/test_cli.py",
    "test_double_emit_observe_and_stop_project_stable_machine_facts": "double/interface/test_cli.py",
    "test_validate_and_start_expose_identity_without_snapshot_content": "double/interface/test_output_models.py",
    "test_runtime_unavailable_and_event_acknowledgement_are_typed_results": "double/interface/test_output_models.py",
    "test_observe_distinguishes_active_sealed_and_last_unsealed_projection": "double/interface/test_output_models.py",
    "test_stop_is_idempotent_only_from_the_sealed_authority": "double/interface/test_output_models.py",
    "test_double_schemas_are_registered_packaged_and_verdict_free": "double/interface/test_output_schemas.py",
    "test_each_double_schema_rejects_an_unavailable_result_for_another_command": "double/interface/test_output_schemas.py",
    "test_observe_and_stop_schemas_reject_contradictory_authority": "double/interface/test_output_schemas.py",
    "test_double_output_schema_imports_without_optional_runtime": "double/interface/test_output_schemas.py",
}

LANGUAGE = {
    "test_compile_representative_module_to_normalized_ir": "double/language/test_compilation.py",
    "test_compiled_ir_drives_matching_captures_and_output_materialization": "double/language/test_compilation.py",
    "test_scenario_digest_ignores_physical_location_and_yaml_comments": "double/language/test_compilation.py",
    "test_explicit_yaml_tags_and_merge_keys_are_rejected": "double/language/test_yaml_surface.py",
    "test_parser_byte_depth_and_node_bounds_are_enforced": "double/language/test_yaml_surface.py",
    "test_runtime_json_boundary_rejects_non_finite_numbers": "double/language/test_yaml_surface.py",
    "test_query_and_header_typed_values_must_be_string_typed": "double/language/test_values.py",
    "test_form_urlencoded_request_fields_match_capture_and_preserve_repeats": "double/language/test_values.py",
    "test_form_urlencoded_is_request_only_and_string_typed": "double/language/test_values.py",
    "test_output_binding_is_available_to_later_derived_value": "double/language/test_values.py",
    "test_cross_interaction_binding_is_not_statically_available": "double/language/test_values.py",
    "test_literal_node_escapes_reserved_bsl_object": "double/language/test_values.py",
    "test_header_names_reject_case_insensitive_duplicates": "double/language/test_values.py",
    "test_project_and_provider_generators_are_outside_closed_registry": "double/language/test_values.py",
    "test_range_null_bound_and_generator_null_validator_are_rejected": "double/language/test_values.py",
    "test_cel_binding_text_inside_a_string_is_not_a_reference": "double/language/test_cel.py",
    "test_cel_json_collection_return_types_are_admitted": "double/language/test_cel.py",
    "test_cel_non_json_return_type_is_rejected": "double/language/test_cel.py",
    "test_cel_static_scan_ignores_comments_and_event_string_literals": "double/language/test_cel.py",
    "test_invalid_re2_pattern_is_a_stable_compile_error": "double/language/test_cel.py",
    "test_cel_profile_inspection_freezes_the_dynamic_map_limitation": "double/language/test_cel.py",
    "test_cel_profile_compilation_evaluation_and_regex_share_one_environment": "double/language/test_cel.py",
    "test_managed_assets_are_snapshotted_and_workspace_escape_is_rejected": "double/language/test_assets_and_materializers.py",
    "test_managed_raw_body_preserves_exact_bytes": "double/language/test_assets_and_materializers.py",
    "test_symlink_escape_is_rejected": "double/language/test_assets_and_materializers.py",
    "test_compile_inspects_materializer_without_executing_it": "double/language/test_assets_and_materializers.py",
    "test_event_materializer_owns_query_headers_and_body": "double/language/test_assets_and_materializers.py",
    "test_materializer_cwd_does_not_make_digest_workspace_address_dependent": "double/language/test_assets_and_materializers.py",
    "test_provider_capture_requires_explicit_sanitization": "double/language/test_assets_and_materializers.py",
    "test_remote_openapi_reference_is_rejected_without_retrieval": "double/language/test_openapi.py",
    "test_local_openapi_path_item_ref_and_canonical_dialect_are_admitted": "double/language/test_openapi.py",
    "test_cross_file_recursive_openapi_schema_uses_immutable_registry": "double/language/test_openapi.py",
    "test_openapi_profile_rejects_unsupported_versions_templates_and_dialects": "double/language/test_openapi.py",
    "test_yaml_reader_errors_and_symlink_loops_are_structured": "double/language/test_yaml_surface.py",
    "test_tagged_ir_rejects_cross_variant_and_missing_fields": "double/language/test_model.py",
    "test_tagged_ir_round_trip_preserves_the_serialized_contract": "double/language/test_model.py",
    "test_missing_local_openapi_pointer_is_rejected_by_registry": "double/language/test_openapi.py",
    "test_unselected_remote_openapi_reference_is_not_scenario_authority": "double/language/test_openapi.py",
}

RUNTIME = {
    "test_in_process_matching_capture_and_seed_replay": "double/runtime/test_matching.py",
    "test_json_null_capture_and_boolean_number_equality_are_type_safe": "double/runtime/test_matching.py",
    "test_in_process_fail_closed_matching_and_request_bounds": "double/runtime/test_matching.py",
    "test_unrelated_structured_route_does_not_parse_an_empty_request_body": "double/runtime/test_matching.py",
    "test_response_derived_value_receives_the_normalized_matched_request": "double/runtime/test_materialization.py",
    "test_external_materializer_stdout_is_enforced_while_reading": "double/runtime/test_materialization.py",
    "test_materialized_headers_cannot_escape_runtime_framing": "double/runtime/test_materialization.py",
    "test_recursive_local_openapi_registry_is_runtime_authority": "double/runtime/test_contract_validation.py",
    "test_service_detached_boundary_event_and_sealed_authority": "double/runtime/test_carrier.py",
    "test_event_consumer_can_reenter_the_responder_before_acknowledging": "double/runtime/test_carrier.py",
    "test_observe_classifies_a_concurrent_sealed_control_result_as_final_authority": "double/runtime/test_carrier.py",
    "test_control_failure_rereads_a_concurrently_sealed_snapshot": "double/runtime/test_carrier.py",
    "test_two_active_runs_keep_replay_bindings_and_stop_isolated": "double/runtime/test_carrier.py",
    "test_control_unavailable_preserves_files_without_pid_authority": "double/runtime/test_carrier.py",
    "test_black_box_consumer_owns_the_public_product_assertion": "double/runtime/test_consumer.py",
}

SHARED_EXECUTION = {
    "test_publish_classifies_execution_directory_creation_failure": "test_execution.py",
    "test_double_execution_requires_merged_capture_and_can_be_released": "test_execution.py",
}


def proposed_owner(node_id: str) -> str:
    function = node_id.split("::", 1)[1].split("[", 1)[0]
    if function == "test_invalid_fixture_corpus_has_stable_diagnostics":
        if "cel-macro" in node_id or "unavailable-binding" in node_id:
            return "double/language/test_cel.py"
        if "illegal-phase" in node_id:
            return "double/language/test_values.py"
        return "double/language/test_yaml_surface.py"
    owners = {**INTERFACE, **LANGUAGE, **RUNTIME, **SHARED_EXECUTION}
    try:
        return owners[function]
    except KeyError as error:
        raise AssertionError(f"unmapped case: {node_id}") from error


def main() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", *CURRENT_TARGETS],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    node_ids = [line for line in completed.stdout.splitlines() if "::" in line]
    assert len(node_ids) == 78 + len(POST_MIGRATION_CASES), len(node_ids)
    assert len(node_ids) == len(set(node_ids))
    assignments = [(node_id, proposed_owner(node_id)) for node_id in node_ids]
    assert len(assignments) == len(node_ids)
    for node_id, owner in assignments:
        actual_owner = node_id.split("svc_cli/tests/", 1)[1].split("::", 1)[0]
        assert actual_owner == owner, (node_id, owner)

    normalized = {node_id.split("::", 1)[1] for node_id in node_ids}
    assert normalized >= POST_MIGRATION_CASES
    baseline = sorted(normalized - POST_MIGRATION_CASES)
    case_digest = sha256("\n".join(baseline).encode()).hexdigest()
    assert case_digest == BASELINE_CASE_DIGEST, case_digest

    counts = Counter(owner for _, owner in assignments)
    print(f"current-cases: {len(node_ids)}")
    print(f"unique-current-cases: {len(set(node_ids))}")
    print(f"mapped-cases: {len(assignments)}")
    print(f"case-identity-digest: {case_digest}")
    for owner, count in sorted(counts.items()):
        print(f"{owner}: {count}")


if __name__ == "__main__":
    main()
