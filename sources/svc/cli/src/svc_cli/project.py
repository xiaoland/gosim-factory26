"""Project-local SVC adoption state and bounded integration planning."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Literal, TypeAlias, cast

from semantic_version import Version  # type: ignore[import-untyped]

from .catalog import canonical_json, require_semver, sha256_bytes
from .config import (
    CONFIG_SCHEMA_VERSION,
    LOCAL_CONFIG_FILE,
    ConfigError,
    ProjectConfig,
    ResolvedConfig,
    load_config,
    parse_project_config,
)
from .errors import SvcError
from .integration import (
    DesiredIntegration,
    IntegrationInspection,
    IntegrationInspectionStatus,
    IntegrationProblem,
    desired_local_agent_instructions,
    desired_local_config_ignore,
    desired_navigation,
    inspect_local_config_ignore,
    inspect_navigation,
    inspect_retired_skill,
)
from .model import ValueModel
from .plans import (
    Blocker,
    FileState,
    LocalPlan,
    PlanAction,
    PlannedFileMutation,
    apply_local_plan,
    make_delete,
    make_write,
)
from .release import catalog, installed_distribution_version
from .resources import resource_mode
from .workspace import WorkspaceIdentity, resolve_workspace_identity


PROJECT_SCHEMA_VERSION = CONFIG_SCHEMA_VERSION
PROJECT_FILE = "svc.json"
CODEX_SKILL_FILE = ".agents/skills/svc/SKILL.md"
AGENTS_FILE = "AGENTS.md"
LOCAL_AGENTS_FILE = "AGENTS.local.md"
DOCS_INDEX_FILE = "docs/index.md"
GuidanceKind: TypeAlias = Literal[
    "agent-router", "docs-navigation", "legacy-cli-skill", "local-config-ignore"
]
NextActionKind: TypeAlias = Literal[
    "plan-integration-establishment",
    "repair-project-configuration",
    "plan-project-upgrade",
    "migrate-project-configuration",
    "plan-integration-repair",
    "install-compatible-corpus",
    "continue",
]
InitSurface: TypeAlias = Literal[
    "project-state",
    "local-config-ignore",
    "local-agent-instructions",
    "agent-router",
    "docs-navigation",
    "legacy-cli-skill",
]
InitExtent: TypeAlias = Literal["whole-file", "svc-managed-block"]


class CorpusBaseline(ValueModel):
    disposition: Literal["create", "unchanged"]
    version: str | None


class InitOperation(ValueModel):
    action: PlanAction
    path: str
    surface: InitSurface
    extent: InitExtent
    before: FileState
    after: FileState


class InitVerification(ValueModel):
    scope: Literal["planned-path-postconditions"] = "planned-path-postconditions"
    status: Literal["passed"] = "passed"


class InitApplyResult(ValueModel):
    status: Literal["noop", "applied"]
    repo: Path
    intent: Literal["establish", "repair"]
    corpus_version: str
    corpus_baseline: CorpusBaseline
    plan_digest: str
    operations: tuple[InitOperation, ...]
    verification: InitVerification


class ProjectMissingStatus(ValueModel):
    path: str
    status: Literal["missing"] = "missing"
    corpus_version: None = None


class ProjectInvalidStatus(ValueModel):
    path: str
    status: Literal["invalid"] = "invalid"
    message: str


class ProjectSchemaBlockedStatus(ValueModel):
    path: str
    status: Literal["schema-write-blocked"] = "schema-write-blocked"
    schema_version: int
    corpus_version: str


class ProjectVersionStatus(ValueModel):
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


class ConfigurationUnavailableStatus(ValueModel):
    status: Literal["invalid", "not-configured", "not-inspected"]
    message: str | None = None
    reason: str | None = None


class ConfigurationFileStatus(ValueModel):
    path: str
    status: Literal["valid", "absent"]
    digest: str | None


class ConfigurationEffectiveStatus(ValueModel):
    status: Literal["valid"] = "valid"
    digest: str


class ConfigurationCurrentStatus(ValueModel):
    status: Literal["current"] = "current"
    base: ConfigurationFileStatus
    local: ConfigurationFileStatus
    effective: ConfigurationEffectiveStatus


ConfigurationStatus: TypeAlias = (
    ConfigurationUnavailableStatus | ConfigurationCurrentStatus
)


class DeclaredDevStatus(ValueModel):
    status: Literal["unavailable", "not-declared", "declared"]
    observation: Literal["declaration-only"] = "declaration-only"
    targets: tuple[str, ...]


class DeclaredRunStatus(ValueModel):
    status: Literal["unavailable", "not-declared", "declared"]
    observation: Literal["declaration-only"] = "declaration-only"
    entries: tuple[str, ...]


class GuidanceStatus(ValueModel):
    path: str
    kind: GuidanceKind
    status: IntegrationInspectionStatus
    message: str | None = None


class NextActionDecision(ValueModel):
    action: NextActionKind
    reason: str
    command: tuple[str, ...] | None = None


class CorpusStatus(ValueModel):
    status: Literal["absent", "behind", "current", "ahead", "unavailable"]
    project_version: str | None
    available_version: str


class IntegrationAnomaly(ValueModel):
    path: str
    kind: GuidanceKind
    status: IntegrationInspectionStatus


class IntegrationStatus(ValueModel):
    status: Literal["blocked", "repairable", "current"]
    anomalies: tuple[IntegrationAnomaly, ...]


class RuntimeStatus(ValueModel):
    status: Literal["source-tree", "installed"]


class ProjectStatusInspection(ValueModel):
    status: Literal["unadopted", "malformed", "actionable", "healthy"]
    next: NextActionDecision
    installed_cli_version: str | None
    available_corpus_version: str
    resource_mode: Literal["source", "wheel"]
    runtime: RuntimeStatus
    workspace: WorkspaceIdentity
    project: ProjectStatus
    corpus: CorpusStatus
    configuration: ConfigurationStatus
    dev: DeclaredDevStatus
    run: DeclaredRunStatus
    managed_ignore: GuidanceStatus
    guidance: tuple[GuidanceStatus, ...]
    retired_skill: GuidanceStatus
    integration: IntegrationStatus
    healthy: bool


@dataclass(frozen=True)
class InitPlan:
    local_plan: LocalPlan
    intent: Literal["establish", "repair"]
    corpus_baseline: CorpusBaseline

    @property
    def repo(self) -> Path:
        return self.local_plan.repo

    @property
    def corpus_version(self) -> str:
        return self.local_plan.target_version

    @property
    def target_version(self) -> str:
        return self.corpus_version

    @property
    def mutations(self) -> tuple[PlannedFileMutation, ...]:
        return self.local_plan.mutations

    @property
    def blockers(self) -> tuple[Blocker, ...]:
        return self.local_plan.blockers

    @property
    def operations(self) -> tuple[InitOperation, ...]:
        return tuple(_init_operation(mutation) for mutation in self.mutations)

    @property
    def status(self) -> Literal["blocked", "ready", "noop"]:
        return self.local_plan.status

    @property
    def digest(self) -> str | None:
        if self.blockers:
            return None
        return sha256_bytes(canonical_json(self.signature()))

    def signature(self) -> dict[str, object]:
        return {
            "schema_version": 3,
            "command": "init",
            "repo": str(self.repo),
            "intent": self.intent,
            "corpus_version": self.corpus_version,
            "corpus_baseline": {
                "disposition": self.corpus_baseline.disposition,
                "version": self.corpus_baseline.version,
            },
            "operations": [
                _init_operation_signature(mutation) for mutation in self.mutations
            ],
            "blockers": [
                {"code": blocker.code, "path": blocker.path}
                for blocker in self.blockers
            ],
        }


def render_project_state(corpus_version: str) -> bytes:
    require_semver(corpus_version, "project corpus_version")
    return (
        json.dumps(
            {
                "schema_version": PROJECT_SCHEMA_VERSION,
                "corpus_version": corpus_version,
            },
            indent=2,
        )
        + "\n"
    ).encode("utf-8")


def parse_project_state(content: bytes) -> ProjectConfig:
    try:
        raw = json.loads(content)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("svc.json must be valid UTF-8 JSON") from error
    if not isinstance(raw, dict):
        raise ValueError("svc.json must contain a JSON object")
    schema = raw.get("schema_version")
    if schema != PROJECT_SCHEMA_VERSION:
        raise ValueError(f"Unsupported svc.json schema: {schema!r}")
    try:
        return parse_project_config(content)
    except ConfigError as error:
        raise ValueError(str(error)) from error


def plan_init(repo: Path) -> InitPlan:
    root = _require_repo(repo)
    target_version = catalog().corpus_version
    blockers: list[Blocker] = []
    writes = []
    state_content = _read_project_content(root, blockers)
    intent: Literal["establish", "repair"] = (
        "establish" if state_content is None else "repair"
    )
    baseline = CorpusBaseline(
        disposition="create" if state_content is None else "unchanged",
        version=target_version if state_content is None else None,
    )
    if state_content is None and not any(
        blocker.path == PROJECT_FILE for blocker in blockers
    ):
        try:
            orphan_local = _read_optional(root, LOCAL_CONFIG_FILE)
        except SvcError as error:
            blockers.append(Blocker(error.code, LOCAL_CONFIG_FILE, error.message))
        else:
            if orphan_local is not None:
                blockers.append(
                    Blocker(
                        "orphan-local-configuration",
                        LOCAL_CONFIG_FILE,
                        f"{LOCAL_CONFIG_FILE} exists while {PROJECT_FILE} is absent.",
                    )
                )
            else:
                writes.append(
                    make_write(
                        root,
                        PROJECT_FILE,
                        "create",
                        "record initial Corpus baseline",
                        render_project_state(target_version),
                    )
                )
    elif state_content is not None:
        try:
            state = parse_project_state(state_content)
        except ValueError as error:
            blockers.append(Blocker("invalid-project-state", PROJECT_FILE, str(error)))
        else:
            _block_noncurrent_schema(state, blockers)
            baseline = CorpusBaseline(
                disposition=baseline.disposition,
                version=_state_corpus_version(state),
            )
            if not blockers:
                try:
                    load_config(root)
                except ConfigError as error:
                    blockers.append(
                        Blocker(
                            "invalid-project-configuration", PROJECT_FILE, str(error)
                        )
                    )
                if Version(_state_corpus_version(state)) > Version(target_version):
                    blockers.append(
                        Blocker(
                            "corpus-baseline-ahead",
                            PROJECT_FILE,
                            "The project Corpus baseline is newer than the installed Corpus; init will not project older integration.",
                        )
                    )

    writes.extend(
        _plan_surface(root, ".gitignore", desired_local_config_ignore, blockers)
    )
    writes.extend(
        _plan_surface(
            root,
            LOCAL_AGENTS_FILE,
            desired_local_agent_instructions,
            blockers,
        )
    )

    writes.extend(_plan_retired_skill(root, blockers))
    writes.extend(
        _plan_surface(
            root,
            AGENTS_FILE,
            lambda content: desired_navigation(AGENTS_FILE, content),
            blockers,
        )
    )
    writes.extend(
        _plan_surface(
            root,
            DOCS_INDEX_FILE,
            lambda content: desired_navigation(DOCS_INDEX_FILE, content),
            blockers,
        )
    )
    return InitPlan(
        LocalPlan("init", root, target_version, tuple(writes), tuple(blockers)),
        intent,
        baseline,
    )


def apply_init(plan: InitPlan, approved_digest: str) -> InitApplyResult:
    if plan.digest is None:
        raise SvcError(
            "plan-blocked",
            "The init plan has unresolved blockers.",
            {
                "command": "init",
                "repo": str(plan.repo),
                "repository_effect": "none",
                "blockers": [blocker.as_dict() for blocker in plan.blockers],
            },
        )
    if approved_digest != plan.digest:
        raise SvcError(
            "plan-digest-mismatch",
            "The supplied digest no longer selects the current init plan.",
            {
                "command": "init",
                "repo": str(plan.repo),
                "selected_digest": approved_digest,
                "repository_effect": "none",
            },
        )
    try:
        result = apply_local_plan(plan.local_plan, plan.local_plan.digest)
    except SvcError as error:
        error.details = {
            "command": "init",
            "repo": str(plan.repo),
            "selected_digest": approved_digest,
            **error.details,
        }
        raise
    return InitApplyResult(
        status=result.status,
        repo=plan.repo,
        intent=plan.intent,
        corpus_version=plan.corpus_version,
        corpus_baseline=plan.corpus_baseline,
        plan_digest=approved_digest,
        operations=tuple(_init_operation(mutation) for mutation in plan.mutations),
        verification=InitVerification(),
    )


def inspect_status(repo: Path) -> ProjectStatusInspection:
    """Inspect one repository without probing or changing a dev capability."""

    root = _require_repo(repo)
    corpus = catalog()
    installed_cli_version = installed_distribution_version()
    runtime_status: Literal["source-tree", "installed"] = (
        "source-tree" if installed_cli_version is None else "installed"
    )
    project = _inspect_project(root, corpus.corpus_version)
    configuration, resolved = _inspect_configuration(root, project)
    dev = _inspect_dev_declaration(resolved)
    run = _inspect_run_declaration(resolved)
    guidance = (
        _inspect_guidance(
            root,
            AGENTS_FILE,
            "agent-router",
            lambda content: inspect_navigation(content, AGENTS_FILE),
        ),
        _inspect_guidance(
            root,
            DOCS_INDEX_FILE,
            "docs-navigation",
            lambda content: inspect_navigation(content, DOCS_INDEX_FILE),
        ),
    )
    retired_skill = _inspect_guidance(
        root,
        CODEX_SKILL_FILE,
        "legacy-cli-skill",
        inspect_retired_skill,
    )
    managed_ignore = _inspect_guidance(
        root, ".gitignore", "local-config-ignore", inspect_local_config_ignore
    )
    healthy = (
        project.status == "current"
        and configuration.status == "current"
        and managed_ignore.status == "current"
        and all(item.status == "current" for item in guidance)
        and retired_skill.status in {"missing", "unowned"}
    )
    status, next_action = _status_decision(
        root,
        project,
        configuration,
        guidance,
        managed_ignore,
        retired_skill,
    )
    corpus_status = _corpus_status(project, corpus.corpus_version)
    integration_status = _integration_status(guidance, managed_ignore, retired_skill)
    return ProjectStatusInspection(
        status=status,
        next=next_action,
        installed_cli_version=installed_cli_version,
        available_corpus_version=corpus.corpus_version,
        resource_mode=resource_mode(),
        runtime=RuntimeStatus(status=runtime_status),
        workspace=resolve_workspace_identity(root),
        project=project,
        corpus=corpus_status,
        configuration=configuration,
        dev=dev,
        run=run,
        managed_ignore=managed_ignore,
        guidance=guidance,
        retired_skill=retired_skill,
        integration=integration_status,
        healthy=healthy,
    )


def _require_repo(repo: Path) -> Path:
    root = repo.resolve()
    if not root.is_dir():
        raise SvcError(
            "repo-not-directory",
            "Project root is not a directory.",
            {"repo": str(repo)},
        )
    return root


def _path(root: Path, relative: str) -> Path:
    return root.joinpath(*relative.split("/"))


def _read_optional(root: Path, relative: str) -> bytes | None:
    path = _path(root, relative)
    if not path.exists() and not path.is_symlink():
        return None
    if path.is_symlink() or not path.is_file():
        raise SvcError(
            "path-not-file",
            "Integration target must be a regular file.",
            {"path": relative},
        )
    return path.read_bytes()


def _read_project_content(root: Path, blockers: list[Blocker]) -> bytes | None:
    try:
        return _read_optional(root, PROJECT_FILE)
    except SvcError as error:
        blockers.append(Blocker(error.code, PROJECT_FILE, error.message))
        return None


def _plan_surface(
    root: Path,
    relative: str,
    desired: Callable[[bytes | None], DesiredIntegration | None],
    blockers: list[Blocker],
) -> list[PlannedFileMutation]:
    try:
        current = _read_optional(root, relative)
        proposal = desired(current)
    except IntegrationProblem as error:
        blockers.append(Blocker(error.code, relative, error.message))
        return []
    except SvcError as error:
        blockers.append(Blocker(error.code, relative, error.message))
        return []
    if proposal is None:
        return []
    return [
        make_write(root, relative, proposal.action, proposal.reason, proposal.content)
    ]


def _plan_retired_skill(
    root: Path, blockers: list[Blocker]
) -> list[PlannedFileMutation]:
    try:
        current = _read_optional(root, CODEX_SKILL_FILE)
        inspection = inspect_retired_skill(current)
    except (IntegrationProblem, SvcError) as error:
        blockers.append(Blocker(error.code, CODEX_SKILL_FILE, str(error)))
        return []
    if inspection.status == "clean-generated":
        return [
            make_delete(
                root,
                CODEX_SKILL_FILE,
                "delete",
                "retire clean generated SVC CLI Skill",
            )
        ]
    if inspection.status == "modified":
        blockers.append(
            Blocker(
                "generated-skill-drift",
                CODEX_SKILL_FILE,
                "The recognizable SVC-generated Skill was modified and will not be deleted.",
            )
        )
    return []


def _init_operation(mutation: PlannedFileMutation) -> InitOperation:
    surfaces: dict[str, tuple[InitSurface, InitExtent]] = {
        PROJECT_FILE: ("project-state", "whole-file"),
        ".gitignore": ("local-config-ignore", "svc-managed-block"),
        LOCAL_AGENTS_FILE: ("local-agent-instructions", "whole-file"),
        AGENTS_FILE: ("agent-router", "svc-managed-block"),
        DOCS_INDEX_FILE: ("docs-navigation", "svc-managed-block"),
        CODEX_SKILL_FILE: ("legacy-cli-skill", "whole-file"),
    }
    surface, extent = surfaces[mutation.path]
    return InitOperation(
        action=mutation.action,
        path=mutation.path,
        surface=surface,
        extent=extent,
        before=mutation.before,
        after=mutation.after,
    )


def _init_operation_signature(mutation: PlannedFileMutation) -> dict[str, object]:
    operation = _init_operation(mutation)
    return {
        "action": operation.action,
        "path": operation.path,
        "surface": operation.surface,
        "extent": operation.extent,
        "before": operation.before.as_dict(),
        "after": operation.after.as_dict(),
        "parent_preconditions": [list(item) for item in mutation.parent_preconditions],
    }


def _inspect_project(root: Path, available_version: str) -> ProjectStatus:
    try:
        content = _read_optional(root, PROJECT_FILE)
    except SvcError as error:
        return ProjectInvalidStatus(path=PROJECT_FILE, message=error.message)
    if content is None:
        return ProjectMissingStatus(path=PROJECT_FILE)
    try:
        state = parse_project_state(content)
    except ValueError as error:
        return ProjectInvalidStatus(path=PROJECT_FILE, message=str(error))
    if state.schema_version != PROJECT_SCHEMA_VERSION:
        return ProjectSchemaBlockedStatus(
            path=PROJECT_FILE,
            schema_version=state.schema_version,
            corpus_version=_state_corpus_version(state),
        )
    status: Literal["current", "corpus-behind", "corpus-ahead"] = (
        "current"
        if _state_corpus_version(state) == available_version
        else (
            "corpus-behind"
            if Version(_state_corpus_version(state)) < Version(available_version)
            else "corpus-ahead"
        )
    )
    return ProjectVersionStatus(
        path=PROJECT_FILE,
        status=status,
        schema_version=state.schema_version,
        corpus_version=_state_corpus_version(state),
    )


def _inspect_configuration(
    root: Path,
    project: ProjectStatus,
) -> tuple[ConfigurationStatus, ResolvedConfig | None]:
    project_status = project.status
    if project_status == "missing":
        try:
            local = _read_optional(root, LOCAL_CONFIG_FILE)
        except SvcError as error:
            return ConfigurationUnavailableStatus(
                status="invalid", message=error.message
            ), None
        if local is None:
            return ConfigurationUnavailableStatus(status="not-configured"), None
        return ConfigurationUnavailableStatus(
            status="invalid",
            message=f"{LOCAL_CONFIG_FILE} exists while {PROJECT_FILE} is absent.",
        ), None
    if project_status not in {"current", "corpus-behind", "corpus-ahead"}:
        return ConfigurationUnavailableStatus(
            status="not-inspected", reason="project-state-not-current-schema"
        ), None
    try:
        resolved = load_config(root)
    except ConfigError as error:
        return ConfigurationUnavailableStatus(
            status="invalid", message=str(error)
        ), None
    return (
        ConfigurationCurrentStatus(
            base=ConfigurationFileStatus(
                path=PROJECT_FILE,
                status="valid",
                digest=resolved.base_digest,
            ),
            local=ConfigurationFileStatus(
                path=LOCAL_CONFIG_FILE,
                status="absent" if resolved.local is None else "valid",
                digest=resolved.local_digest,
            ),
            effective=ConfigurationEffectiveStatus(digest=resolved.effective_digest),
        ),
        resolved,
    )


def _inspect_dev_declaration(resolved: ResolvedConfig | None) -> DeclaredDevStatus:
    if resolved is None:
        return DeclaredDevStatus(status="unavailable", targets=())
    dev = resolved.effective.dev
    if dev is None:
        return DeclaredDevStatus(status="not-declared", targets=())
    return DeclaredDevStatus(status="declared", targets=tuple(sorted(dev.targets)))


def _inspect_run_declaration(resolved: ResolvedConfig | None) -> DeclaredRunStatus:
    if resolved is None:
        return DeclaredRunStatus(status="unavailable", entries=())
    entries = sorted(resolved.base.run)
    return DeclaredRunStatus(
        status="declared" if entries else "not-declared",
        entries=tuple(entries),
    )


def _status_decision(
    root: Path,
    project: ProjectStatus,
    configuration: ConfigurationStatus,
    guidance: tuple[GuidanceStatus, ...],
    managed_ignore: GuidanceStatus,
    retired_skill: GuidanceStatus,
) -> tuple[
    Literal["unadopted", "malformed", "actionable", "healthy"],
    NextActionDecision,
]:
    project_status = project.status
    configuration_status = configuration.status
    if project_status == "missing":
        if configuration_status == "not-configured":
            return "unadopted", _next_action(
                "plan-integration-establishment",
                "Project SVC integration is absent; inspect the non-mutating init plan.",
                command=("svc", "init", str(root)),
            )
        return "malformed", _next_action(
            "repair-project-configuration",
            "SVC will not overwrite an orphaned or invalid local configuration.",
        )
    if project_status == "invalid" or configuration_status == "invalid":
        return "malformed", _next_action(
            "repair-project-configuration",
            "Project configuration is invalid; repair the Consumer-owned file before continuing.",
        )
    if project_status == "schema-write-blocked":
        return "actionable", _next_action(
            "migrate-project-configuration",
            "Project configuration schema is unsupported by this CLI.",
        )
    integration = _integration_status(guidance, managed_ignore, retired_skill)
    if integration.status != "current":
        return "actionable", _next_action(
            "plan-integration-repair",
            "Managed SVC integration needs review; inspect the non-mutating init plan.",
            command=("svc", "init", str(root)),
        )
    if project_status == "corpus-behind":
        return "actionable", _next_action(
            "plan-project-upgrade",
            "The project Corpus baseline is behind the installed Corpus.",
            command=("svc", "upgrade", str(root)),
        )
    if project_status == "corpus-ahead":
        return "actionable", _next_action(
            "install-compatible-corpus",
            "The project Corpus baseline is newer than the installed Corpus; use the package manager to install a compatible CLI distribution.",
        )
    return "healthy", _next_action(
        "continue",
        "Configuration, Corpus baseline, and managed integration are current.",
    )


def _next_action(
    action: NextActionKind,
    reason: str,
    *,
    command: tuple[str, ...] | None = None,
) -> NextActionDecision:
    return NextActionDecision(action=action, reason=reason, command=command)


def _corpus_status(project: ProjectStatus, available_version: str) -> CorpusStatus:
    project_status = project.status
    version = (
        project.corpus_version
        if not isinstance(project, ProjectInvalidStatus)
        else None
    )
    relation = cast(
        Literal["absent", "behind", "current", "ahead", "unavailable"],
        {
            "missing": "absent",
            "corpus-behind": "behind",
            "current": "current",
            "corpus-ahead": "ahead",
        }.get(project_status, "unavailable"),
    )
    return CorpusStatus(
        status=relation,
        project_version=version,
        available_version=available_version,
    )


def _integration_status(
    guidance: tuple[GuidanceStatus, ...],
    managed_ignore: GuidanceStatus,
    retired_skill: GuidanceStatus,
) -> IntegrationStatus:
    surfaces = [managed_ignore, *guidance, retired_skill]
    blocked = [item for item in surfaces if item.status == "modified"]
    repairable = [
        item
        for item in surfaces
        if item.status in {"missing", "unanchored", "outdated", "clean-generated"}
        and not (item.kind == "legacy-cli-skill" and item.status == "missing")
    ]
    if blocked:
        status: Literal["blocked", "repairable", "current"] = "blocked"
        anomalies = blocked + repairable
    elif repairable:
        status = "repairable"
        anomalies = repairable
    else:
        status = "current"
        anomalies = []
    return IntegrationStatus(
        status=status,
        anomalies=tuple(
            IntegrationAnomaly(path=item.path, kind=item.kind, status=item.status)
            for item in anomalies
        ),
    )


def _block_noncurrent_schema(state: ProjectConfig, blockers: list[Blocker]) -> None:
    if state.schema_version == PROJECT_SCHEMA_VERSION:
        return
    blockers.append(
        Blocker(
            "schema-write-blocked",
            PROJECT_FILE,
            f"Unsupported svc.json schema: {state.schema_version}.",
        )
    )


def _state_corpus_version(state: ProjectConfig) -> str:
    return state.corpus_version


def replace_corpus_baseline(content: bytes, version: str, field: str) -> bytes:
    """Replace only one recognized root Corpus baseline JSON value."""

    require_semver(version, "project corpus_version")
    text = content.decode("utf-8")
    decoder = json.JSONDecoder()
    index = _skip_json_space(text, 0)
    if index >= len(text) or text[index] != "{":
        raise ValueError("svc.json must contain a JSON object")
    index += 1
    found: tuple[int, int] | None = None
    while True:
        index = _skip_json_space(text, index)
        if index < len(text) and text[index] == "}":
            break
        key, index = decoder.raw_decode(text, index)
        if not isinstance(key, str):
            raise ValueError("svc.json object keys must be strings")
        index = _skip_json_space(text, index)
        if index >= len(text) or text[index] != ":":
            raise ValueError("svc.json object entry is malformed")
        index = _skip_json_space(text, index + 1)
        value_start = index
        _, value_end = decoder.raw_decode(text, index)
        if key == field:
            if found is not None:
                raise ValueError(f"svc.json contains duplicate {field} entries")
            found = (value_start, value_end)
        index = _skip_json_space(text, value_end)
        if index < len(text) and text[index] == ",":
            index += 1
            continue
        if index < len(text) and text[index] == "}":
            break
        raise ValueError("svc.json object entry is malformed")
    if found is None:
        raise ValueError(f"svc.json has no {field} entry")
    start, end = found
    return (text[:start] + json.dumps(version) + text[end:]).encode("utf-8")


def _skip_json_space(text: str, index: int) -> int:
    while index < len(text) and text[index] in " \t\r\n":
        index += 1
    return index


def _inspect_guidance(
    root: Path,
    relative: str,
    kind: GuidanceKind,
    inspect: Callable[[bytes | None], IntegrationInspection],
) -> GuidanceStatus:
    try:
        content = _read_optional(root, relative)
        inspection = inspect(content)
    except (IntegrationProblem, SvcError) as error:
        return GuidanceStatus(
            path=relative,
            kind=kind,
            status="modified",
            message=str(error),
        )
    return GuidanceStatus(
        path=relative,
        kind=kind,
        status=cast(
            Literal[
                "clean-generated",
                "current",
                "missing",
                "modified",
                "outdated",
                "unanchored",
                "unowned",
            ],
            inspection.status,
        ),
    )
