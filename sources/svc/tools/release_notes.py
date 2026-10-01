"""Extract and validate one prepared Towncrier release section."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


HEADING = re.compile(r"^## \[([^]]+)](?: - .+)?$")


def release_section(changelog: str, version: str) -> str:
    lines = changelog.splitlines()
    releases = [index for index, line in enumerate(lines) if HEADING.match(line)]
    if not releases:
        raise ValueError("changelog has no release section")
    first = releases[0]
    match = HEADING.match(lines[first])
    if match is None or match.group(1) != version:
        actual = match.group(1) if match is not None else "missing"
        raise ValueError(f"latest changelog version is {actual}, expected {version}")
    end = releases[1] if len(releases) > 1 else len(lines)
    return "\n".join(lines[first:end]).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("changelog", type=Path)
    parser.add_argument("version")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    notes = release_section(args.changelog.read_text(encoding="utf-8"), args.version)
    if args.output is None:
        print(notes, end="")
    else:
        args.output.write_text(notes, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
