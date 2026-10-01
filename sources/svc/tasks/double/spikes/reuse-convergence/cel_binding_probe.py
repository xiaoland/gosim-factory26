"""Probe whether the selected CEL binding can check BSL binding availability."""

from __future__ import annotations

from cel_expr_python import cel  # type: ignore[import-untyped]


def compiles(environment: cel.Env, expression: str) -> tuple[bool, str]:
    try:
        program = environment.compile(expression)
    except (RuntimeError, TypeError, ValueError) as error:
        return False, str(error).splitlines()[0]
    return True, program.return_type().name()


def main() -> None:
    map_environment = cel.NewEnv(
        variables={"bindings": cel.Type.Map(cel.Type.STRING, cel.Type.DYN)}
    )
    current_known = compiles(map_environment, "bindings.external_id")
    current_missing = compiles(map_environment, "bindings.missing")
    current_dynamic = compiles(map_environment, "bindings['computed_' + 'name']")

    explicit_environment = cel.NewEnv(variables={"external_id": cel.Type.DYN})
    explicit_known = compiles(explicit_environment, "external_id")
    explicit_missing = compiles(explicit_environment, "missing")

    expression = map_environment.compile("bindings.external_id")
    public_expression_api = sorted(
        name for name in dir(expression) if not name.startswith("_")
    )

    assert current_known[0]
    assert current_missing[0]
    assert current_dynamic[0]
    assert explicit_known[0]
    assert not explicit_missing[0]
    assert "ast" not in public_expression_api

    print(f"map-known: {current_known}")
    print(f"map-missing: {current_missing}")
    print(f"map-dynamic: {current_dynamic}")
    print(f"explicit-known: {explicit_known}")
    print(f"explicit-missing: {explicit_missing}")
    print(f"expression-public-api: {public_expression_api}")
    print(
        "finding: preserving bindings.NAME cannot eliminate source inspection "
        "with cel-expr-python 0.1.3's public Python API"
    )


if __name__ == "__main__":
    main()
