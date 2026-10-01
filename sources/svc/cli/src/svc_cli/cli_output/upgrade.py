"""Public Corpus-upgrade output projections."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from ..plans import PlanAction
from ..upgrade import CorpusGuideReference as ServiceCorpusGuideReference
from ..upgrade import CorpusRelease as ServiceCorpusRelease
from ..upgrade import UpgradeApplyResult, UpgradeCorpusDetails as ServiceDetails
from ..upgrade import UpgradeMigration as ServiceMigration
from ..upgrade import UpgradeOperation, UpgradePlan
from .common import BlockerOutput, FileStateOutput, project_blocker, project_file_state
from .model import MachineModel


class CorpusGuideReference(MachineModel):
    path: str
    sha256: str


class CorpusReleaseOutput(MachineModel):
    version: str
    migration: Literal["guide", "not-required"]
    guides: tuple[CorpusGuideReference, ...] | None = Field(
        default=None, exclude_if=lambda value: value is None
    )


class UpgradeCorpusDetails(MachineModel):
    project_version: str | None = Field(
        default=None, exclude_if=lambda value: value is None
    )
    available_version: str | None = Field(
        default=None, exclude_if=lambda value: value is None
    )
    status: Literal["current"] | None = Field(
        default=None, exclude_if=lambda value: value is None
    )
    from_version: str | None = Field(
        default=None, exclude_if=lambda value: value is None
    )
    to_version: str | None = Field(default=None, exclude_if=lambda value: value is None)
    releases: tuple[CorpusReleaseOutput, ...] | None = Field(
        default=None, exclude_if=lambda value: value is None
    )


class UpgradeOperationOutput(MachineModel):
    path: str
    action: PlanAction
    reason: str
    before: FileStateOutput
    after: FileStateOutput
    surface: Literal["project-corpus-baseline"]
    extent: Literal["json-field"]


class UpgradePlanOutput(MachineModel):
    schema_version: Literal[2] = 2
    command: Literal["upgrade"] = "upgrade"
    mode: Literal["plan"] = "plan"
    status: Literal["noop", "blocked", "ready", "migration-required"]
    repo: str
    operations: tuple[UpgradeOperationOutput, ...]
    corpus: UpgradeCorpusDetails
    blockers: tuple[BlockerOutput, ...] | None = Field(
        default=None, exclude_if=lambda value: value is None
    )
    plan_digest: str | None = Field(
        default=None, exclude_if=lambda value: value is None
    )


class UpgradeMigrationOutput(MachineModel):
    disposition: Literal["caller-asserted", "not-required"]
    guidance: tuple[CorpusGuideReference, ...]


class UpgradeApplyOutput(MachineModel):
    schema_version: Literal[2] = 2
    command: Literal["upgrade"] = "upgrade"
    mode: Literal["apply"] = "apply"
    status: Literal["applied"] = "applied"
    repo: str
    plan_digest: str
    changed: int
    operations: tuple[UpgradeOperationOutput, ...]
    corpus: UpgradeCorpusDetails
    migration: UpgradeMigrationOutput
    verification: Literal["passed"] = "passed"


def project_upgrade_plan(plan: UpgradePlan) -> UpgradePlanOutput:
    return UpgradePlanOutput(
        status=plan.status,
        repo=str(plan.repo),
        operations=tuple(_operation(value) for value in plan.operations()),
        corpus=_corpus(plan.corpus),
        blockers=tuple(project_blocker(value) for value in plan.blockers) or None,
        plan_digest=plan.digest,
    )


def project_upgrade_apply(result: UpgradeApplyResult) -> UpgradeApplyOutput:
    return UpgradeApplyOutput(
        repo=result.repo,
        plan_digest=result.plan_digest,
        changed=result.changed,
        operations=tuple(_operation(value) for value in result.operations),
        corpus=_corpus(result.corpus),
        migration=_migration(result.migration),
    )


def _corpus(value: ServiceDetails) -> UpgradeCorpusDetails:
    return UpgradeCorpusDetails(
        project_version=value.project_version,
        available_version=value.available_version,
        status=value.status,
        from_version=value.from_version,
        to_version=value.to_version,
        releases=(
            None
            if value.releases is None
            else tuple(_release(item) for item in value.releases)
        ),
    )


def _release(value: ServiceCorpusRelease) -> CorpusReleaseOutput:
    return CorpusReleaseOutput(
        version=value.version,
        migration=value.migration,
        guides=(
            None
            if value.guides is None
            else tuple(_guide(item) for item in value.guides)
        ),
    )


def _operation(value: UpgradeOperation) -> UpgradeOperationOutput:
    return UpgradeOperationOutput(
        path=value.path,
        action=value.action,
        reason=value.reason,
        before=project_file_state(value.before),
        after=project_file_state(value.after),
        surface=value.surface,
        extent=value.extent,
    )


def _migration(value: ServiceMigration) -> UpgradeMigrationOutput:
    return UpgradeMigrationOutput(
        disposition=value.disposition,
        guidance=tuple(_guide(item) for item in value.guidance),
    )


def _guide(value: ServiceCorpusGuideReference) -> CorpusGuideReference:
    return CorpusGuideReference(path=value.path, sha256=value.sha256)
