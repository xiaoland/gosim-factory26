from __future__ import annotations

import hashlib

import pytest

from svc_cli.catalog import Catalog, CatalogEntry, CorpusMigration, CorpusRelease
from svc_cli.errors import SvcError
from svc_cli.lookup import CorpusLookup, LookupQuery


def fixture_lookup() -> CorpusLookup:
    documents = {
        "index.md": b"# Sustainable Vibe Coding\n\nSource-first framework.\n",
        "methods/explore/index.md": b"# Explore\n\nFind key information.\n",
        "templates/AGENTS.local.template.md": (
            b"# Local Instructions\n\nA task packet local template.\n"
        ),
        "specs/alignment/index.md": (b"# Alignment\n\nKeep one alignment boundary.\n"),
        "taste/implementation/index.md": (
            b"# Implementation Taste\n\nUse measured design judgment.\n"
        ),
        "task-packet/index.md": (
            b"# Task Packet\n\nUse a task packet as the task control surface.\n"
        ),
    }
    entries = tuple(
        CatalogEntry(
            path,
            content.decode().splitlines()[0][2:],
            hashlib.sha256(content).hexdigest(),
        )
        for path, content in sorted(documents.items())
    )
    releases = (CorpusRelease("10.0.0", "9.0.0", CorpusMigration("not-required")),)
    return CorpusLookup(Catalog(2, "10.0.0", releases, entries), documents.__getitem__)


def test_list_browses_one_logical_level_without_reading_documents() -> None:
    fixture = fixture_lookup()

    def fail_reader(path: str) -> bytes:
        pytest.fail(f"list unexpectedly read {path}")

    lookup = CorpusLookup(fixture.catalog, fail_reader)
    root = lookup.lookup(LookupQuery("list"))
    nested = lookup.lookup(LookupQuery("list", "methods/"))

    assert [(entry.kind, entry.path) for entry in root.entries] == [
        ("document", "index.md"),
        ("directory", "methods/"),
        ("directory", "specs/"),
        ("directory", "task-packet/"),
        ("directory", "taste/"),
        ("directory", "templates/"),
    ]
    assert [entry.path for entry in nested.entries] == ["methods/explore/"]
    assert nested.prefix == "methods/"


def test_missing_or_invalid_directory_is_an_exact_selection_failure() -> None:
    with pytest.raises(SvcError) as missing:
        fixture_lookup().lookup(LookupQuery("list", "missing/"))
    assert missing.value.code == "lookup-directory-not-found"

    with pytest.raises(SvcError) as invalid:
        fixture_lookup().lookup(LookupQuery("list", "../methods"))
    assert invalid.value.code == "invalid-directory-prefix"


def test_path_reads_one_exact_normalized_document() -> None:
    response = fixture_lookup().lookup(LookupQuery("path", "task-packet/index.md"))

    assert response.document is not None
    assert response.document.entry.path == "task-packet/index.md"
    assert "task control surface" in response.document.content


@pytest.mark.parametrize("path", ("task-packet", "task-packet/"))
def test_path_resolves_a_directory_to_its_canonical_index(path: str) -> None:
    response = fixture_lookup().lookup(LookupQuery("path", path))

    assert response.document is not None
    assert response.document.entry.path == "task-packet/index.md"
    assert "task control surface" in response.document.content


@pytest.mark.parametrize(
    "path",
    (
        "",
        "../task-packet/index.md",
        "/task-packet/index.md",
        "task-packet//",
        "task-packet//index",
        "task-packet/index.md/",
        r"task-packet\index.md",
    ),
)
def test_path_rejects_non_normalized_non_markdown_identity(path: str) -> None:
    with pytest.raises(SvcError) as raised:
        fixture_lookup().lookup(LookupQuery("path", path))

    assert raised.value.code == "invalid-document-path"


def test_missing_directory_alias_reports_its_canonical_candidate() -> None:
    with pytest.raises(SvcError) as raised:
        fixture_lookup().lookup(LookupQuery("path", "task-packet/index"))

    assert raised.value.code == "lookup-not-found"
    assert raised.value.details == {
        "path": "task-packet/index",
        "resolved_path": "task-packet/index/index.md",
    }


def test_keyword_ranking_obeys_search_scope() -> None:
    lookup = fixture_lookup()
    both = lookup.lookup(
        LookupQuery("keyword", "task packet control surface", "both", 10)
    )
    path_only = lookup.lookup(LookupQuery("keyword", "task packet", "path", 10))

    assert both.candidates[0].entry.path == "task-packet/index.md"
    assert both.candidates[0].matched_in == ("content",)
    assert both.candidates[0].excerpt is not None
    assert path_only.candidates[0].matched_in == ("path",)
    assert path_only.candidates[0].excerpt is None


def test_regex_returns_stable_path_and_one_based_content_locations() -> None:
    response = fixture_lookup().lookup(
        LookupQuery("regex", r"alignment boundary|task-packet", "both", 10)
    )

    assert [(item.entry.path, item.surface) for item in response.matches] == [
        ("specs/alignment/index.md", "content"),
        ("task-packet/index.md", "path"),
    ]
    content = response.matches[0]
    assert (content.line, content.column) == (3, 10)
    assert "alignment boundary" in (content.excerpt or "")


def test_regex_limit_is_flat_and_reports_truncation() -> None:
    response = fixture_lookup().lookup(
        LookupQuery("regex", r"(?i)task|mutation", "both", 1)
    )

    assert len(response.matches) == 1
    assert response.truncated


def test_invalid_regex_is_an_explicit_usage_failure() -> None:
    with pytest.raises(SvcError) as raised:
        fixture_lookup().lookup(LookupQuery("regex", "["))
    assert raised.value.code == "invalid-lookup-regex"


@pytest.mark.parametrize("mode", ("keyword", "regex"))
def test_empty_search_is_a_settled_result(mode: str) -> None:
    response = fixture_lookup().lookup(
        LookupQuery(mode, "dev server readiness", "both", 10)
    )

    assert response.candidates == ()
    assert response.matches == ()
    assert not response.truncated


def test_tampered_corpus_is_an_explicit_integrity_failure() -> None:
    bad = CorpusLookup(
        Catalog(
            2,
            "10.0.0",
            (CorpusRelease("10.0.0", "9.0.0", CorpusMigration("not-required")),),
            (CatalogEntry("sections/example.md", "Example", "0" * 64),),
        ),
        lambda _: b"# Example\n",
    )
    with pytest.raises(SvcError, match="digest"):
        bad.lookup(LookupQuery("regex", "Example", "both"))
