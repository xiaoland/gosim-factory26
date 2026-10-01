"""Browse, search, and read the packaged SVC Corpus."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Callable, Literal, Sequence, cast

from .catalog import Catalog, CatalogEntry, normalized_document_path, sha256_bytes
from .errors import SvcError
from .resources import read_document


TOKEN_RE = re.compile(r"\w+", re.UNICODE)
LIST_GUIDANCE_COMMAND = "svc lookup --list"
READ_GUIDANCE_COMMAND = "svc lookup --path <document-or-directory>"
LOOKUP_DISCOVERY_HINT = (
    "Use `svc lookup --help` to browse, search, or read the SVC Corpus."
)


@dataclass(frozen=True)
class LookupQuery:
    mode: Literal["list", "path", "keyword", "regex"]
    value: str | None = None
    scope: Literal["path", "both"] = "both"
    limit: int = 10

    def __post_init__(self) -> None:
        if self.mode not in {"list", "path", "keyword", "regex"}:
            raise ValueError(f"Unsupported lookup mode: {self.mode}")
        if self.mode == "path" and not isinstance(self.value, str):
            raise ValueError("Path lookup needs one document path")
        if self.mode in {"keyword", "regex"} and (
            not isinstance(self.value, str) or not self.value.strip()
        ):
            raise ValueError("Search query must not be empty")
        if self.scope not in {"path", "both"}:
            raise ValueError("Lookup scope must be path or both")
        if not 1 <= self.limit <= 50:
            raise ValueError("Lookup limit must be between 1 and 50")


@dataclass(frozen=True)
class CorpusDocument:
    entry: CatalogEntry
    content: str


@dataclass(frozen=True)
class ListEntry:
    kind: str
    path: str
    title: str | None = None
    sha256: str | None = None
    document_count: int | None = None


@dataclass(frozen=True)
class KeywordCandidate:
    entry: CatalogEntry
    matched_in: tuple[Literal["path", "content"], ...]
    excerpt: str | None
    score: int


@dataclass(frozen=True)
class RegexMatch:
    entry: CatalogEntry
    surface: str
    line: int | None = None
    column: int | None = None
    excerpt: str | None = None


@dataclass(frozen=True)
class LookupResponse:
    corpus_version: str
    query: LookupQuery
    entries: tuple[ListEntry, ...] = ()
    document: CorpusDocument | None = None
    candidates: tuple[KeywordCandidate, ...] = ()
    matches: tuple[RegexMatch, ...] = ()
    truncated: bool = False
    prefix: str | None = None


class CorpusLookup:
    def __init__(
        self,
        catalog: Catalog,
        reader: Callable[[str], bytes] = read_document,
    ) -> None:
        self.catalog = catalog
        self.reader = reader

    def lookup(self, query: LookupQuery) -> LookupResponse:
        if query.mode == "list":
            return self._lookup_list(query)
        if query.mode == "path":
            return self._lookup_path(query)
        if query.mode == "keyword":
            return self._lookup_keyword(query)
        return self._lookup_regex(query)

    def _lookup_list(self, query: LookupQuery) -> LookupResponse:
        prefix = _normalize_prefix(query.value)
        matching = [
            entry
            for entry in self.catalog.entries
            if entry.path.startswith(prefix or "")
        ]
        if prefix is not None and not matching:
            raise SvcError(
                "lookup-directory-not-found",
                "No packaged SVC Corpus directory has that prefix.",
                {"prefix": prefix},
            )
        directories: dict[str, int] = {}
        documents: list[ListEntry] = []
        for entry in matching:
            relative = entry.path[len(prefix or "") :]
            head, separator, _ = relative.partition("/")
            if separator:
                directory = f"{prefix or ''}{head}/"
                directories[directory] = directories.get(directory, 0) + 1
            else:
                documents.append(
                    ListEntry("document", entry.path, entry.title, entry.sha256)
                )
        entries = [
            ListEntry("directory", path, document_count=count)
            for path, count in directories.items()
        ] + documents
        entries.sort(key=lambda item: item.path)
        return LookupResponse(
            self.catalog.corpus_version,
            query,
            entries=tuple(entries),
            prefix=prefix,
        )

    def _lookup_path(self, query: LookupQuery) -> LookupResponse:
        assert query.value is not None
        try:
            path = _resolve_document_path(query.value)
        except ValueError as error:
            raise SvcError(
                "invalid-document-path", str(error), {"path": query.value}
            ) from error
        entry = next((item for item in self.catalog.entries if item.path == path), None)
        if entry is None:
            raise SvcError(
                "lookup-not-found",
                "No packaged SVC document resolves from that path.",
                {"path": query.value, "resolved_path": path},
            )
        return LookupResponse(
            self.catalog.corpus_version,
            query,
            document=self._document(entry),
        )

    def _lookup_keyword(self, query: LookupQuery) -> LookupResponse:
        assert query.value is not None
        phrase = query.value.casefold().strip()
        terms = tuple(dict.fromkeys(TOKEN_RE.findall(phrase)))
        ranked: list[KeywordCandidate] = []
        for entry in self.catalog.entries:
            path = entry.path.casefold()
            path_matches = _lexical_match(path, phrase, terms)
            document = self._document(entry) if query.scope == "both" else None
            body = document.content.casefold() if document is not None else ""
            content_matches = _lexical_match(body, phrase, terms)
            if not path_matches and not content_matches:
                continue
            matched_in = cast(
                tuple[Literal["path", "content"], ...],
                tuple(
                    surface
                    for surface, matched in (
                        ("path", path_matches),
                        ("content", content_matches),
                    )
                    if matched
                ),
            )
            score = _keyword_score(path, body, phrase, terms)
            excerpt = (
                _excerpt(document.content, phrase, terms)
                if document is not None and content_matches
                else None
            )
            ranked.append(KeywordCandidate(entry, matched_in, excerpt, score))
        ranked.sort(key=lambda item: (-item.score, item.entry.path))
        truncated = len(ranked) > query.limit
        return LookupResponse(
            self.catalog.corpus_version,
            query,
            candidates=tuple(ranked[: query.limit]),
            truncated=truncated,
        )

    def _lookup_regex(self, query: LookupQuery) -> LookupResponse:
        assert query.value is not None
        try:
            pattern = re.compile(query.value)
        except re.error as error:
            raise SvcError(
                "invalid-lookup-regex",
                f"Invalid --regex expression: {error}",
                {"query": query.value},
            ) from error
        matches: list[RegexMatch] = []
        for entry in self.catalog.entries:
            if pattern.search(entry.path):
                matches.append(RegexMatch(entry, "path"))
            if query.scope == "both":
                document = self._document(entry)
                for found in pattern.finditer(document.content):
                    line, column, excerpt = _match_location(document.content, found)
                    matches.append(RegexMatch(entry, "content", line, column, excerpt))
        truncated = len(matches) > query.limit
        return LookupResponse(
            self.catalog.corpus_version,
            query,
            matches=tuple(matches[: query.limit]),
            truncated=truncated,
        )

    def _document(self, entry: CatalogEntry) -> CorpusDocument:
        content = self.reader(entry.path)
        actual = sha256_bytes(content)
        if actual != entry.sha256:
            raise SvcError(
                "invalid-corpus",
                "Packaged SVC document digest does not match its catalog entry.",
                {
                    "path": entry.path,
                    "expected_sha256": entry.sha256,
                    "actual_sha256": actual,
                },
            )
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError as error:
            raise SvcError(
                "invalid-corpus",
                "Packaged SVC document is not UTF-8 Markdown.",
                {"path": entry.path},
            ) from error
        return CorpusDocument(entry, text)


def _resolve_document_path(value: str) -> str:
    """Resolve one CLI document reference to its canonical catalog identity."""

    if "\\" in value:
        raise ValueError("--path must use normalized POSIX separators")
    if value.endswith(".md"):
        return normalized_document_path(value, "--path")

    directory = value.removesuffix("/")
    path = PurePosixPath(directory)
    if (
        not directory
        or value.endswith("//")
        or path.is_absolute()
        or "." in path.parts
        or ".." in path.parts
        or any(part.startswith(".") for part in path.parts)
        or path.as_posix() != directory
        or path.suffix == ".md"
    ):
        raise ValueError(
            "--path must be a visible normalized Markdown path or Corpus directory"
        )
    return f"{directory}/index.md"


def _normalize_prefix(value: str | None) -> str | None:
    if value in {None, ""}:
        return None
    assert value is not None
    if "\\" in value or value.startswith("/"):
        raise SvcError(
            "invalid-directory-prefix",
            "--list prefix must be a normalized relative Corpus directory.",
            {"prefix": value},
        )
    stripped = value.removesuffix("/")
    path = PurePosixPath(stripped)
    if (
        not stripped
        or "." in path.parts
        or ".." in path.parts
        or any(part.startswith(".") for part in path.parts)
        or path.as_posix() != stripped
    ):
        raise SvcError(
            "invalid-directory-prefix",
            "--list prefix must be a normalized relative Corpus directory.",
            {"prefix": value},
        )
    return f"{stripped}/"


def _lexical_match(text: str, phrase: str, terms: Sequence[str]) -> bool:
    return phrase in text or bool(terms and all(term in text for term in terms))


def _keyword_score(path: str, body: str, phrase: str, terms: Sequence[str]) -> int:
    return (
        path.count(phrase) * 1000
        + body.count(phrase) * 100
        + sum(path.count(term) * 120 + body.count(term) * 10 for term in terms)
    )


def _excerpt(content: str, phrase: str, terms: Sequence[str]) -> str:
    compact = re.sub(r"\s+", " ", content).strip()
    haystack = compact.casefold()
    needle = (
        phrase
        if phrase in haystack
        else next((term for term in terms if term in haystack), "")
    )
    start = max(haystack.find(needle), 0)
    left = max(start - 70, 0)
    right = min(start + max(len(needle), 1) + 120, len(compact))
    return (
        ("…" if left else "")
        + compact[left:right].strip()
        + ("…" if right < len(compact) else "")
    )


def _match_location(content: str, match: re.Match[str]) -> tuple[int, int, str]:
    start = match.start()
    line_start = content.rfind("\n", 0, start) + 1
    line_end = content.find("\n", start)
    if line_end == -1:
        line_end = len(content)
    line = content.count("\n", 0, start) + 1
    column = start - line_start + 1
    source_line = content[line_start:line_end]
    clip_left = max(column - 1 - 70, 0)
    clip_right = min(column - 1 + max(len(match.group()), 1) + 120, len(source_line))
    excerpt = (
        ("…" if clip_left else "")
        + source_line[clip_left:clip_right]
        + ("…" if clip_right < len(source_line) else "")
    )
    return line, column, excerpt
