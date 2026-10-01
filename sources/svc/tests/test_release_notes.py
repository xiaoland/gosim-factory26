from __future__ import annotations

import pytest

from tools.release_notes import release_section


def test_release_section_requires_and_returns_the_latest_version() -> None:
    changelog = """# Changes

## [15.1.0] - 2026-09-19

- Current.

## [15.0.0] - 2026-09-01

- Previous.
"""

    assert release_section(changelog, "15.1.0").endswith("- Current.\n")
    with pytest.raises(ValueError, match="latest changelog version is 15.1.0"):
        release_section(changelog, "15.0.0")
