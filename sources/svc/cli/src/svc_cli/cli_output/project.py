"""Public init/status output and projections from project services."""

from __future__ import annotations

from typing import Literal, TypeAlias, cast

from pydantic import Field

from ..integration import IntegrationInspectionStatus
from .model import MachineModel
from ..plans import PlanAction
from ..project import (
    ConfigurationCurrentStatus as ServiceConfigurationCurrentStatus,
    ConfigurationFileStatus as ServiceConfigurationFileStatus,
    ConfigurationStatus as ServiceConfigurationStatus,
    ConfigurationUnavailableStatus as ServiceConfigurationUnavailableStatus,
    CorpusBaseline,
    GuidanceKind,
    GuidanceStatus as ServiceGuidanceStatus,
    InitApplyResult,
    InitExtent,
    InitOperation,
    InitPlan,
    InitSurface,
    IntegrationAnomaly as ServiceIntegrationAnomaly,
    NextActionKind,
    ProjectInvalidStatus as ServiceProjectInvalidStatus,
    ProjectMissingStatus as ServiceProjectMissingStatus,
    ProjectSchemaBlockedStatus as ServiceProjectSchemaBlockedStatus,
    ProjectStatus as ServiceProjectStatus,
    ProjectStatusInspection,
    ProjectVersionStatus as ServiceProjectVersionStatus,
)
from ..workspace import WorkspaceIdentity
from .common import BlockerOutput, FileStateOutput, project_blocker, project_file_state


class CorpusBaselineOutput(MachineModel):
    disposition: Literal["create", "unchanged"]
    version: str | None


class InitOperationOutput(MachineModel):
    action: PlanAction
    path: str
    surface: InitSurface
    extent: InitExtent
    before: FileStateOutput
    after: FileStateOutput


class InitVerificationOutput(MachineModel):
    scope: Literal["planned-path-postconditions"] = "planned-path-postconditions"
    status: Literal["passed"] = "passed"


class InitPlanOutput(MachineModel):
    schema_version: Literal[3] = 3
    command: Literal["init"] = "init"
    mode: Literal["plan"] = "plan"
    status: Literal["blocked", "ready", "noop"]
    repo: str
    intent: Literal["establish", "repair"]
    corpus_version: str
    corpus_baseline: CorpusBaselineOutput
    operations: tuple[InitOperationOutput, ...]
    blockers: tuple[BlockerOutput, ...]
    plan_digest: str | None = Field(
        default=None, exclude_if=lambda value: value is None
    )


class InitApplyOutput(MachineModel):
    schema_version: Literal[3] = 3
    command: Literal["init"] = "init"
    mode: Literal["apply"] = "apply"
    status: Literal["noop", "applied"]
    repo: str
    intent: Literal["establish", "repair"]
    corpus_version: str
    corpus_baseline: CorpusBaselineOutput
    plan_digest: str
    operations: tuple[InitOperationOutput, ...]
    verification: InitVerificationOutput


class ProjectMissingStatus(MachineModel):
    path: str
    status: Literal["missing"] = "missing"
    corpus_version: None = None


class ProjectInvalidStatus(MachineModel):
    path: str
    status: Literal["invalid"] = "invalid"
    message: str


class ProjectSchemaBlockedStatus(MachineModel):
    path: str
    status: Literal["schema-write-blocked"] = "schema-write-blocked"
    schema_version: int
    corpus_version: str


class ProjectVersionStatus(MachineModel):
    path: str
    status: Literal["current", "corpus-behind", "corpus-ahead"]
    schema_version: int
    corpus_version: str


ProjectStatus: TypeAlias = (
    ProjectMissingStatus
    | ProjectInvalidStatus
    | ProjectSchemaBlockedStatus
    | ProjectVersionStatus
)


class ConfigurationUnavailableStatus(MachineModel):
    status: Literal["invalid", "not-configured", "not-inspected"]
    message: str | None = Field(default=None, exclude_if=lambda value: value is None)
    reason: str | None = Field(default=None, exclude_if=lambda value: value is None)


class ConfigurationFileStatus(MachineModel):
    path: str
    status: Literal["valid", "absent"]
    digest: str | None


class ConfigurationEffectiveStatus(MachineModel):
    status: Literal["valid"] = "valid"
    digest: str


class ConfigurationCurrentStatus(MachineModel):
    status: Literal["current"] = "current"
    base: ConfigurationFileStatus
    local: ConfigurationFileStatus
    effective: ConfigurationEffectiveStatus


ConfigurationStatus: TypeAlias = (
    ConfigurationUnavailableStatus | ConfigurationCurrentStatus
)


class DeclaredDevStatus(MachineModel):
    status: Literal["unavailable", "not-declared", "declared"]
    observation: Literal["declaration-only"] = "declaration-only"
    targets: tuple[str, ...]


class DeclaredRunStatus(MachineModel):
    status: Literal["unavailable", "not-declared", "declared"]
    observation: Literal["declaration-only"] = "declaration-only"
    entries: tuple[str, ...]


class GuidanceStatus(MachineModel):
    path: str
    kind: GuidanceKind
    status: IntegrationInspectionStatus
    message: str | None = Field(default=None, exclude_if=lambda value: value is None)


class NextActionOutput(MachineModel):
    action: NextActionKind
    reason: str
    command: tuple[str, ...] | None = Field(
        default=None, exclude_if=lambda value: value is None
    )


class CorpusStatusOutput(MachineModel):
    status: Literal["absent", "behind", "current", "ahead", "unavailable"]
    project_version: str | None
    available_version: str


class IntegrationAnomaly(MachineModel):
    path: str
    kind: GuidanceKind
    status: IntegrationInspectionStatus


class IntegrationStatusOutput(MachineModel):
    status: Literal["blocked", "repairable", "current"]
    anomalies: tuple[IntegrationAnomaly, ...]


class RuntimeStatusOutput(MachineModel):
    status: Literal["source-tree", "installed"]


class RootStatusOutput(MachineModel):
    schema_version: Literal[2] = 2
    status: Literal["unadopted", "malformed", "actionable", "healthy"]
    next: NextActionOutput
    installed_cli_version: str | None
    available_corpus_version: str
    resource_mode: Literal["source", "wheel"]
    runtime: RuntimeStatusOutput
    workspace: WorkspaceIdentity
    project: ProjectStatus
    corpus: CorpusStatusOutput
    configuration: ConfigurationStatus
    dev: DeclaredDevStatus
    run: DeclaredRunStatus
    managed_ignore: GuidanceStatus
    guidance: tuple[GuidanceStatus, ...]
    retired_skill: GuidanceStatus
    integration: IntegrationStatusOutput
    healthy: bool


def project_init_plan(plan: InitPlan) -> InitPlanOutput:
    return InitPlanOutput(
        status=cast(Literal["blocked", "ready", "noop"], plan.status),
        repo=str(plan.repo),
        intent=plan.intent,
        corpus_version=plan.corpus_version,
        corpus_baseline=_corpus_baseline(plan.corpus_baseline),
        operations=()
        if plan.blockers
        else tuple(_init_operation(value) for value in plan.operations),
        blockers=tuple(project_blocker(value) for value in plan.blockers),
        plan_digest=plan.digest,
    )


def project_init_apply(result: InitApplyResult) -> InitApplyOutput:
    return InitApplyOutput(
        status=result.status,
        repo=str(result.repo),
        intent=result.intent,
        corpus_version=result.corpus_version,
        corpus_baseline=_corpus_baseline(result.corpus_baseline),
        plan_digest=result.plan_digest,
        operations=tuple(_init_operation(value) for value in result.operations),
        verification=InitVerificationOutput(
            scope=result.verification.scope,
            status=result.verification.status,
        ),
    )


def project_status(result: ProjectStatusInspection) -> RootStatusOutput:
    return RootStatusOutput(
        status=result.status,
        next=NextActionOutput(
            action=result.next.action,
            reason=result.next.reason,
            command=result.next.command,
        ),
        installed_cli_version=result.installed_cli_version,
        available_corpus_version=result.available_corpus_version,
        resource_mode=result.resource_mode,
        runtime=RuntimeStatusOutput(status=result.runtime.status),
        workspace=result.workspace,
        project=_project_state(result.project),
        corpus=CorpusStatusOutput(
            status=result.corpus.status,
            project_version=result.corpus.project_version,
            available_version=result.corpus.available_version,
        ),
        configuration=_configuration(result.configuration),
        dev=DeclaredDevStatus(
            status=result.dev.status,
            observation=result.dev.observation,
            targets=result.dev.targets,
        ),
        run=DeclaredRunStatus(
            status=result.run.status,
            observation=result.run.observation,
            entries=result.run.entries,
        ),
        managed_ignore=_guidance(result.managed_ignore),
        guidance=tuple(_guidance(value) for value in result.guidance),
        retired_skill=_guidance(result.retired_skill),
        integration=IntegrationStatusOutput(
            status=result.integration.status,
            anomalies=tuple(_anomaly(value) for value in result.integration.anomalies),
        ),
        healthy=result.healthy,
    )


def _corpus_baseline(value: CorpusBaseline) -> CorpusBaselineOutput:
    return CorpusBaselineOutput(disposition=value.disposition, version=value.version)


def _init_operation(value: InitOperation) -> InitOperationOutput:
    return InitOperationOutput(
        action=value.action,
        path=value.path,
        surface=value.surface,
        extent=value.extent,
        before=project_file_state(value.before),
        after=project_file_state(value.after),
    )


def _project_state(value: ServiceProjectStatus) -> ProjectStatus:
    if isinstance(value, ServiceProjectMissingStatus):
        return ProjectMissingStatus(path=value.path)
    if isinstance(value, ServiceProjectInvalidStatus):
        return ProjectInvalidStatus(path=value.path, message=value.message)
    if isinstance(value, ServiceProjectSchemaBlockedStatus):
        return ProjectSchemaBlockedStatus(
            path=value.path,
            schema_version=value.schema_version,
            corpus_version=value.corpus_version,
        )
    assert isinstance(value, ServiceProjectVersionStatus)
    return ProjectVersionStatus(
        path=value.path,
        status=value.status,
        schema_version=value.schema_version,
        corpus_version=value.corpus_version,
    )


def _configuration(value: ServiceConfigurationStatus) -> ConfigurationStatus:
    if isinstance(value, ServiceConfigurationUnavailableStatus):
        return ConfigurationUnavailableStatus(
            status=value.status,
            message=value.message,
            reason=value.reason,
        )
    assert isinstance(value, ServiceConfigurationCurrentStatus)
    return ConfigurationCurrentStatus(
        base=_configuration_file(value.base),
        local=_configuration_file(value.local),
        effective=ConfigurationEffectiveStatus(digest=value.effective.digest),
    )


def _configuration_file(
    value: ServiceConfigurationFileStatus,
) -> ConfigurationFileStatus:
    return ConfigurationFileStatus(
        path=value.path,
        status=value.status,
        digest=value.digest,
    )


def _guidance(value: ServiceGuidanceStatus) -> GuidanceStatus:
    return GuidanceStatus(
        path=value.path,
        kind=value.kind,
        status=value.status,
        message=value.message,
    )


def _anomaly(value: ServiceIntegrationAnomaly) -> IntegrationAnomaly:
    return IntegrationAnomaly(path=value.path, kind=value.kind, status=value.status)
