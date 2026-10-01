"""Public lookup machine output and service-result projection."""

from __future__ import annotations

from typing import Annotated, Literal, TypeAlias

from pydantic import Field

from ..catalog import CatalogEntry
from ..lookup import LookupResponse
from .model import MachineModel


class CorpusDocumentReference(MachineModel):
    path: str
    title: str
    sha256: str

    @classmethod
    def from_entry(cls, entry: CatalogEntry) -> "CorpusDocumentReference":
        return cls(path=entry.path, title=entry.title, sha256=entry.sha256)


class LookupDirectoryEntry(MachineModel):
    kind: Literal["directory"] = "directory"
    path: str
    document_count: int


class LookupDocumentEntry(CorpusDocumentReference):
    kind: Literal["document"] = "document"


LookupListEntry: TypeAlias = Annotated[
    LookupDirectoryEntry | LookupDocumentEntry, Field(discriminator="kind")
]


class LookupDocument(CorpusDocumentReference):
    content: str


class LookupKeywordCandidate(CorpusDocumentReference):
    matched_in: tuple[Literal["path", "content"], ...]
    excerpt: str | None = None


class LookupRegexMatch(MachineModel):
    machine_exclude_none = True

    path: str
    sha256: str
    surface: Literal["path", "content"]
    line: int | None = None
    column: int | None = None
    excerpt: str | None = None


class _LookupOutput(MachineModel):
    schema_version: Literal[2] = 2
    command: Literal["lookup"] = "lookup"
    corpus_version: str


class LookupListOutput(_LookupOutput):
    mode: Literal["list"] = "list"
    prefix: str | None
    entries: tuple[LookupListEntry, ...]


class LookupPathOutput(_LookupOutput):
    mode: Literal["path"] = "path"
    document: LookupDocument


class LookupKeywordOutput(_LookupOutput):
    machine_exclude_none = True

    mode: Literal["keyword"] = "keyword"
    query: str
    scope: Literal["path", "both"]
    limit: int
    truncated: bool
    candidates: tuple[LookupKeywordCandidate, ...]


class LookupRegexOutput(_LookupOutput):
    machine_exclude_none = True

    mode: Literal["regex"] = "regex"
    query: str
    scope: Literal["path", "both"]
    limit: int
    truncated: bool
    matches: tuple[LookupRegexMatch, ...]


LookupOutput: TypeAlias = Annotated[
    LookupListOutput | LookupPathOutput | LookupKeywordOutput | LookupRegexOutput,
    Field(discriminator="mode"),
]


def project_lookup(response: LookupResponse) -> LookupOutput:
    """Project a neutral lookup response onto the public command contract."""

    if response.query.mode == "list":
        entries: list[LookupListEntry] = []
        for entry in response.entries:
            if entry.kind == "directory":
                assert entry.document_count is not None
                entries.append(
                    LookupDirectoryEntry(
                        path=entry.path,
                        document_count=entry.document_count,
                    )
                )
            else:
                assert entry.title is not None and entry.sha256 is not None
                entries.append(
                    LookupDocumentEntry(
                        path=entry.path,
                        title=entry.title,
                        sha256=entry.sha256,
                    )
                )
        return LookupListOutput(
            corpus_version=response.corpus_version,
            prefix=response.prefix,
            entries=tuple(entries),
        )
    if response.query.mode == "path":
        assert response.document is not None
        document = response.document
        return LookupPathOutput(
            corpus_version=response.corpus_version,
            document=LookupDocument(
                path=document.entry.path,
                title=document.entry.title,
                sha256=document.entry.sha256,
                content=document.content,
            ),
        )
    assert response.query.value is not None
    scope: Literal["path", "both"] = response.query.scope
    if response.query.mode == "keyword":
        return LookupKeywordOutput(
            corpus_version=response.corpus_version,
            query=response.query.value,
            scope=scope,
            limit=response.query.limit,
            truncated=response.truncated,
            candidates=tuple(
                LookupKeywordCandidate(
                    path=item.entry.path,
                    title=item.entry.title,
                    sha256=item.entry.sha256,
                    matched_in=item.matched_in,
                    excerpt=item.excerpt,
                )
                for item in response.candidates
            ),
        )
    return LookupRegexOutput(
        corpus_version=response.corpus_version,
        query=response.query.value,
        scope=scope,
        limit=response.query.limit,
        truncated=response.truncated,
        matches=tuple(
            LookupRegexMatch(
                path=item.entry.path,
                sha256=item.entry.sha256,
                surface="path" if item.surface == "path" else "content",
                line=item.line,
                column=item.column,
                excerpt=item.excerpt,
            )
            for item in response.matches
        ),
    )
