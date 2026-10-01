"""Compare the admitted SVC matchers with a pinned external Pact suite checkout.

No Pact source or fixture is vendored. The caller supplies a checkout of
https://github.com/pact-foundation/pact-jvm at EXPECTED_COMMIT.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

from svc_cli.double.materialization import matcher_accepts
from svc_cli.double.model import ExactMatcher, RegexMatcher


EXPECTED_COMMIT = "97abd7bfcec15f3532109f984db37bcb5ccfb49c"


def main() -> None:
    arguments = _arguments()
    suite = arguments.suite_root.resolve()
    repository = _git(suite, "rev-parse", "--show-toplevel")
    commit = _git(suite, "rev-parse", "HEAD")
    assert commit == EXPECTED_COMMIT, commit

    license_text = (suite / "LICENSE").read_text(encoding="utf-8")
    assert "Apache License" in license_text and "Version 2.0" in license_text

    v2 = (suite / "features/V2/http_consumer.feature").read_text(encoding="utf-8")
    v3 = (suite / "features/V3/matching_rules.feature").read_text(
        encoding="utf-8"
    )
    body_rules = _json(suite / "fixtures/regex-matcher-v2.json")
    query_rules = _json(suite / "fixtures/regex-matcher-query-v2.json")
    header_rules = _json(suite / "fixtures/regex-matcher-header-v2.json")
    expected_body = _json(suite / "fixtures/3-level.json")

    body_pattern = body_rules["$.body.one"]["regex"]
    query_pattern = query_rules["$.query.a"]["regex"]
    header_pattern = header_rules["$.header.x-test"]["regex"]
    body_positive = _capture(
        v2,
        r"Scenario: Supports a regex matcher \(positive case\).*?"
        r'JSON: \{ "one": "([^"]+)"',
    )
    body_negative = _capture(
        v2,
        r"Scenario: Supports a regex matcher \(negative case\).*?"
        r"Expected '([^']+)' to match",
    )
    query_negative = _capture(
        v2,
        r'repeated request query parameters \(negative case\).*?Expected \'([^\']+)\'',
    )
    header_negative = _capture(
        v2,
        r'repeated request headers \(negative case\).*?Expected \'([^\']+)\'',
    )
    equality_actual = _capture(
        v3,
        r"equality matcher to reset cascading rules.*?Expected '([^']+)' .*?"
        r"equal to '([^']+)'",
        group=1,
    )
    equality_expected = expected_body["one"]["a"]["status"]

    facts = {
        "exact-positive": matcher_accepts(
            ExactMatcher(value=equality_expected), equality_expected
        ),
        "exact-negative": matcher_accepts(
            ExactMatcher(value=equality_expected), equality_actual
        ),
        "body-regex-positive": matcher_accepts(
            RegexMatcher(pattern=body_pattern), body_positive
        ),
        "body-regex-negative": matcher_accepts(
            RegexMatcher(pattern=body_pattern), body_negative
        ),
        "query-regex-positive": matcher_accepts(
            RegexMatcher(pattern=query_pattern), "9999"
        ),
        "query-regex-negative": matcher_accepts(
            RegexMatcher(pattern=query_pattern), query_negative
        ),
        "header-regex-positive": matcher_accepts(
            RegexMatcher(pattern=header_pattern), "1000"
        ),
        "header-regex-negative": matcher_accepts(
            RegexMatcher(pattern=header_pattern), header_negative
        ),
    }
    assert facts == {
        "exact-positive": True,
        "exact-negative": False,
        "body-regex-positive": True,
        "body-regex-negative": False,
        "query-regex-positive": True,
        "query-regex-negative": True,
        "header-regex-positive": True,
        "header-regex-negative": True,
    }

    print(f"repository: {repository}")
    print(f"commit: {commit}")
    print("license: Apache-2.0")
    for name, accepted in facts.items():
        pact_expected = not name.endswith("negative")
        status = "aligned" if accepted == pact_expected else "diverged"
        print(
            f"{name}: svc-accepted={str(accepted).lower()} "
            f"pact-accepted={str(pact_expected).lower()} status={status}"
        )


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite-root", type=Path, required=True)
    return parser.parse_args()


def _git(directory: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", "-C", str(directory), *arguments],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    ).stdout.strip()


def _json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _capture(text: str, pattern: str, *, group: int = 1) -> str:
    matched = re.search(pattern, text, re.DOTALL)
    assert matched is not None, pattern
    return matched.group(group)


if __name__ == "__main__":
    main()
