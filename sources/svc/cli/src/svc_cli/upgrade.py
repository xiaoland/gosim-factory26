"""Plan and apply Corpus baseline adoption."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, cast

from semantic_version import Version  # type: ignore[import-untyped]

from .catalog import Catalog, canonical_json, sha256_bytes
from .errors import SvcError
from .model import ValueModel
from .plans import Blocker, FileState, LocalPlan, PlanAction, PlannedFileMutation
from .plans import apply_local_plan, make_write
from .project import PROJECT_FILE, parse_project_state, replace_corpus_baseline
from .release import catalog
from .resources import read_document


UPGRADE_SCHEMA_VERSION = 2


class CorpusGuideReference(ValueModel):
    path: str
    sha256: str


class CorpusRelease(ValueModel):
    version: str
    migration: Literal["guide", "not-required"]
    guides: tuple[CorpusGuideReference, ...] | None = None


class UpgradeCorpusDetails(ValueModel):
    project_version: str | None = None
    available_version: str | None = None
    status: Literal["current"] | None = None
    from_version: str | None = None
    to_version: str | None = None
    releases: tuple[CorpusRelease, ...] | None = None


class UpgradeOperation(ValueModel):
    path: str
    action: PlanAction
    reason: str
    before: FileState
    after: FileState
    surface: Literal["project-corpus-baseline"] = "project-corpus-baseline"
    extent: Literal["json-field"] = "json-field"


class UpgradeMigration(ValueModel):
    disposition: Literal["caller-asserted", "not-required"]
    guidance: tuple[CorpusGuideReference, ...]


class UpgradeVerification(ValueModel):
    scope: Literal["project-corpus-baseline"] = "project-corpus-baseline"
    status: Literal["passed"] = "passed"


class UpgradeApplyResult(ValueModel):
    status: Literal["applied"] = "applied"
    repo: str
    plan_digest: str
    changed: int
    operations: tuple[UpgradeOperation, ...]
    corpus: UpgradeCorpusDetails
    migration: UpgradeMigration
    verification: UpgradeVerification


@dataclass(frozen=True)
class UpgradePlan:
    repo: Path
    status: Literal["noop", "blocked", "ready", "migration-required"]
    mutations: tuple[PlannedFileMutation, ...]
    blockers: tuple[Blocker, ...]
    corpus: UpgradeCorpusDetails
    local_plan: LocalPlan | None = None

    @property
    def digest(self) -> str | None:
        if self.status not in {"ready", "migration-required"}:
            return None
        return sha256_bytes(canonical_json(self.signature()))

    def signature(self) -> dict[str, object]:
        return {
            "schema_version": UPGRADE_SCHEMA_VERSION,
            "command": "upgrade",
            "repo": str(self.repo),
            "status": self.status,
            "corpus": self.corpus.model_dump(exclude_none=True, mode="json"),
            "local_plan": None
            if self.local_plan is None
            else self.local_plan.signature(),
        }

    def operations(self) -> tuple[UpgradeOperation, ...]:
        return tuple(
            UpgradeOperation(
                path=item.path,
                action=item.action,
                reason=item.reason,
                before=item.before,
                after=item.after,
            )
            for item in self.mutations
        )


def plan_upgrade(repo: Path) -> UpgradePlan:
    root = repo.resolve()
    if not root.is_dir():
        raise SvcError(
            "repo-not-directory",
            "Project root is not a directory.",
            {"repo": str(repo)},
        )
    available = catalog()
    content, blocker = _read_regular(root, PROJECT_FILE)
    if blocker is not None:
        return _blocked(root, blocker, available)
    if content is None:
        return _blocked(
            root,
            Blocker(
                "project-not-initialized",
                PROJECT_FILE,
                "Project SVC integration is absent; run svc init first.",
            ),
            available,
        )
    try:
        state = parse_project_state(content)
    except ValueError as error:
        return _blocked(
            root,
            Blocker("invalid-project-configuration", PROJECT_FILE, str(error)),
            available,
        )

    baseline = state.corpus_version
    selected, blocker = _select_releases(baseline, available)
    if blocker is not None:
        return _blocked(root, blocker, available, baseline)
    if not selected:
        return UpgradePlan(
            root,
            "noop",
            (),
            (),
            UpgradeCorpusDetails(
                project_version=baseline,
                available_version=available.corpus_version,
                status="current",
                releases=(),
            ),
        )

    entry_hashes = {entry.path: entry.sha256 for entry in available.entries}
    releases: list[CorpusRelease] = []
    guided = False
    for release in selected:
        guides = None
        if release.migration.status == "guide":
            guided = True
            references = []
            for path in release.migration.paths:
                digest = sha256_bytes(read_document(path))
                if entry_hashes.get(path) != digest:
                    raise SvcError(
                        "invalid-corpus",
                        "Corpus guide content does not match the catalog.",
                        {"path": path},
                    )
                references.append(CorpusGuideReference(path=path, sha256=digest))
            guides = tuple(references)
        releases.append(
            CorpusRelease(
                version=release.version,
                migration=cast(
                    Literal["guide", "not-required"], release.migration.status
                ),
                guides=guides,
            )
        )

    details = UpgradeCorpusDetails(
        from_version=baseline,
        to_version=available.corpus_version,
        releases=tuple(releases),
    )
    mutation = make_write(
        root,
        PROJECT_FILE,
        "rewrite",
        f"record Corpus baseline {available.corpus_version}",
        replace_corpus_baseline(content, available.corpus_version, "corpus_version"),
    )
    local_plan = LocalPlan(
        "upgrade-corpus", root, available.corpus_version, (mutation,)
    )
    return UpgradePlan(
        root,
        "migration-required" if guided else "ready",
        (mutation,),
        (),
        details,
        local_plan,
    )


def apply_upgrade(plan: UpgradePlan, approved_digest: str) -> UpgradeApplyResult:
    if plan.digest is None or plan.local_plan is None:
        raise SvcError(
            "upgrade-plan-not-applicable",
            "The selected upgrade plan cannot be applied.",
            {
                "repo": str(plan.repo),
                "status": plan.status,
                "repository_effect": "none",
            },
        )
    if approved_digest != plan.digest:
        raise SvcError(
            "plan-digest-mismatch",
            "The supplied digest does not select the current upgrade plan.",
            {
                "repo": str(plan.repo),
                "received": approved_digest,
                "repository_effect": "none",
            },
        )
    result = apply_local_plan(plan.local_plan, plan.local_plan.digest)
    guides = tuple(
        guide
        for release in plan.corpus.releases or ()
        for guide in release.guides or ()
    )
    return UpgradeApplyResult(
        repo=str(plan.repo),
        plan_digest=approved_digest,
        changed=result.changed,
        operations=plan.operations(),
        corpus=plan.corpus,
        migration=UpgradeMigration(
            disposition="caller-asserted" if guides else "not-required",
            guidance=guides,
        ),
        verification=UpgradeVerification(),
    )


def _read_regular(root: Path, relative: str) -> tuple[bytes | None, Blocker | None]:
    path = root / relative
    if not path.exists() and not path.is_symlink():
        return None, None
    if path.is_symlink() or not path.is_file():
        return None, Blocker(
            "path-not-file", relative, "Upgrade target must be a regular file."
        )
    try:
        return path.read_bytes(), None
    except OSError as error:
        return None, Blocker("path-unreadable", relative, str(error))


def _blocked(
    root: Path,
    blocker: Blocker,
    available: Catalog,
    baseline: str | None = None,
) -> UpgradePlan:
    return UpgradePlan(
        root,
        "blocked",
        (),
        (blocker,),
        UpgradeCorpusDetails(
            project_version=baseline, available_version=available.corpus_version
        ),
    )


def _select_releases(baseline: str, available: Catalog):
    if baseline == available.corpus_version:
        return (), None
    by_previous = {release.previous_version: release for release in available.releases}
    selected = []
    current = baseline
    while current != available.corpus_version:
        release = by_previous.get(current)
        if release is None:
            relation = (
                "newer than"
                if Version(current) > Version(available.corpus_version)
                else "outside"
            )
            return (), Blocker(
                "unsupported-corpus-baseline",
                PROJECT_FILE,
                f"Project Corpus baseline {current} is {relation} the retained "
                f"upgrade chain ending at {available.corpus_version}.",
            )
        selected.append(release)
        current = release.version
    return tuple(selected), None
