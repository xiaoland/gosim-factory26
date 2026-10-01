"""Build and verify packaged JSON Schemas for core SVC CLI output."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import tomllib
from pathlib import Path

from svc_cli.output_schema import OUTPUT_SCHEMA_KEYS, generate_output_schema


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_ROOT = ROOT / "cli" / "src" / "svc_cli" / "data" / "output-schemas"
SCHEMA_REPOSITORY_PREFIX = "cli/src/svc_cli/data/output-schemas"
LEGACY_SCHEMA_REPOSITORY_PREFIX = "svc_cli/src/svc_cli/data/output-schemas"


def _encoded(key: str) -> bytes:
    return (
        json.dumps(
            generate_output_schema(key),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def build(*, check: bool) -> list[str]:
    changed: list[str] = []
    for key in OUTPUT_SCHEMA_KEYS:
        path = SCHEMA_ROOT / f"{key}.json"
        expected = _encoded(key)
        actual = path.read_bytes() if path.is_file() else None
        if actual == expected:
            continue
        changed.append(path.relative_to(ROOT).as_posix())
        if not check:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(expected)
    return changed


def _package_version(ref: str | None = None) -> tuple[int, int, int]:
    if ref is None:
        raw = (ROOT / "cli/pyproject.toml").read_bytes()
    else:
        shown = subprocess.run(
            ("git", "show", f"{ref}:cli/pyproject.toml"),
            cwd=ROOT,
            capture_output=True,
            check=False,
        )
        if shown.returncode != 0:
            shown = subprocess.run(
                ("git", "show", f"{ref}:svc_cli/pyproject.toml"),
                cwd=ROOT,
                capture_output=True,
                check=True,
            )
        raw = shown.stdout
    version = tomllib.loads(raw.decode())["project"].get("version")
    if version is None and ref is not None:
        described = subprocess.run(
            ("git", "describe", "--tags", "--abbrev=0", "--match", "v[0-9]*", ref),
            cwd=ROOT,
            capture_output=True,
            check=True,
            text=True,
        )
        version = described.stdout.strip().removeprefix("v")
    if not isinstance(version, str):
        raise ValueError("package version is not static")
    parts = version.split(".")
    if len(parts) != 3 or any(not part.isdigit() for part in parts):
        raise ValueError(f"invalid package version: {version}")
    return int(parts[0]), int(parts[1]), int(parts[2])


def compare_ref(ref: str) -> list[str]:
    failures = []
    result_schema_advanced = False
    for key in OUTPUT_SCHEMA_KEYS:
        previous = subprocess.run(
            ("git", "show", f"{ref}:{SCHEMA_REPOSITORY_PREFIX}/{key}.json"),
            cwd=ROOT,
            capture_output=True,
            check=False,
        )
        if previous.returncode != 0:
            previous = subprocess.run(
                (
                    "git",
                    "show",
                    f"{ref}:{LEGACY_SCHEMA_REPOSITORY_PREFIX}/{key}.json",
                ),
                cwd=ROOT,
                capture_output=True,
                check=False,
            )
            if previous.returncode != 0:
                continue
        before = json.loads(previous.stdout)
        after = generate_output_schema(key)
        if before == after:
            continue
        old_version = before.get("x-svc-result-schema-version")
        new_version = after.get("x-svc-result-schema-version")
        if (
            not isinstance(old_version, int)
            or not isinstance(new_version, int)
            or new_version <= old_version
        ):
            failures.append(
                f"{key} output changed without advancing x-svc-result-schema-version"
            )
        else:
            result_schema_advanced = True
    if result_schema_advanced and _package_version()[0] <= _package_version(ref)[0]:
        failures.append(
            "result schema advancement requires a package major advancement"
        )
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--compare-ref")
    args = parser.parse_args()

    changed = build(check=args.check)
    if args.check and changed:
        for path in changed:
            print(f"outdated generated output schema: {path}")
        return 1
    compare = args.compare_ref or os.environ.get("SVC_BASE_REF")
    if compare:
        failures = compare_ref(compare)
        for failure in failures:
            print(failure)
        if failures:
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
