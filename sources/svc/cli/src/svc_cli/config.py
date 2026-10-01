"""Strict current project configuration models.

``svc.json`` is complete and committed. ``svc.local.json`` is an optional,
schema-governed sparse overlay; it is never materialized into the base model.
Only the current schema is accepted.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Literal, Mapping, Self, TypeAlias, overload

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)

from .catalog import require_semver


CONFIG_SCHEMA_VERSION = 3
PROJECT_CONFIG_FILE = "svc.json"
LOCAL_CONFIG_FILE = "svc.local.json"

_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


class ConfigError(ValueError):
    """A configuration document cannot safely participate in resolution."""


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


class HttpProbe(_StrictModel):
    kind: Literal["http"]
    url: str
    method: Literal["GET", "HEAD"] = "GET"
    success_status: list[int] = Field(
        default_factory=lambda: [200, 299], min_length=2, max_length=2
    )
    timeout: float = Field(default=5.0, gt=0, le=60)
    network_scope: Literal["loopback", "remote"] = "loopback"
    insecure_tls: bool = False

    @model_validator(mode="after")
    def validate_status_and_tls(self) -> Self:
        lower, upper = self.success_status
        if not 100 <= lower <= upper <= 599:
            raise ValueError("success_status must be an inclusive HTTP status interval")
        if self.insecure_tls and self.network_scope != "loopback":
            raise ValueError("insecure_tls is allowed only for loopback HTTP probes")
        return self


class TcpProbe(_StrictModel):
    kind: Literal["tcp"]
    host: str
    port: int = Field(ge=1, le=65535)
    timeout: float = Field(default=5.0, gt=0, le=60)
    network_scope: Literal["loopback", "remote"] = "loopback"


class ExecProbe(_StrictModel):
    kind: Literal["exec"]
    argv: list[str] = Field(min_length=1)
    cwd: str | None = None
    timeout: float = Field(default=5.0, gt=0, le=60)
    output_limit: int = Field(default=16_384, ge=1, le=1_048_576)


Probe: TypeAlias = Annotated[
    HttpProbe | TcpProbe | ExecProbe, Field(discriminator="kind")
]


class ExecProvision(_StrictModel):
    kind: Literal["exec"]
    mode: Literal["run", "activate"]
    argv: list[str] = Field(min_length=1)
    cwd: str | None = None
    env: dict[str, str] = Field(default_factory=dict)

    @field_validator("env")
    @classmethod
    def validate_env(cls, value: dict[str, str]) -> dict[str, str]:
        _validate_environment(value)
        return value


class ManualProvision(_StrictModel):
    kind: Literal["manual"]


Provision: TypeAlias = Annotated[
    ExecProvision | ManualProvision, Field(discriminator="kind")
]


class ExecStop(_StrictModel):
    kind: Literal["exec"]
    argv: list[str] = Field(min_length=1)
    cwd: str | None = None
    env: dict[str, str] = Field(default_factory=dict)
    timeout: float = Field(default=300.0, gt=0, le=3_600)

    @field_validator("env")
    @classmethod
    def validate_env(cls, value: dict[str, str]) -> dict[str, str]:
        _validate_environment(value)
        return value


class ManualStop(_StrictModel):
    kind: Literal["manual"]


StopAction: TypeAlias = Annotated[ExecStop | ManualStop, Field(discriminator="kind")]


class _TargetBase(_StrictModel):
    scope: Literal["worktree", "repository", "host"] = "worktree"
    host_key: str | None = None
    probe: Probe
    provision: Provision
    access: list[str] = Field(default_factory=list)
    readiness_timeout: float = Field(default=60.0, gt=0, le=3_600)
    poll_interval: float = Field(default=0.5, gt=0, le=60)

    @model_validator(mode="after")
    def validate_scope(self) -> Self:
        if self.scope == "host" and not self.host_key:
            raise ValueError("host scope requires a non-empty host_key")
        if self.scope != "host" and self.host_key is not None:
            raise ValueError("host_key is valid only for host scope")
        if self.poll_interval > self.readiness_timeout:
            raise ValueError("poll_interval cannot exceed readiness_timeout")
        return self


class TargetConfig(_TargetBase):
    stop: StopAction | None = None


class DevConfig(_StrictModel):
    targets: dict[str, TargetConfig] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_target_names(self) -> Self:
        _validate_names(self.targets, "target")
        return self


class RunEntry(_StrictModel):
    argv: list[str] = Field(min_length=1)
    cwd: str = "."
    env_files: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)

    @field_validator("argv")
    @classmethod
    def validate_argv(cls, value: list[str]) -> list[str]:
        if not value[0]:
            raise ValueError("argv[0] must be non-empty")
        if any("\0" in item for item in value):
            raise ValueError("argv must not contain NUL")
        return value

    @field_validator("cwd")
    @classmethod
    def validate_cwd(cls, value: str) -> str:
        if not value or "\0" in value:
            raise ValueError("cwd must be non-empty and NUL-free")
        return value

    @field_validator("env_files")
    @classmethod
    def validate_env_files(cls, value: list[str]) -> list[str]:
        if any(not item or "\0" in item for item in value):
            raise ValueError("env_files entries must be non-empty and NUL-free")
        return value

    @field_validator("env")
    @classmethod
    def validate_env(cls, value: dict[str, str]) -> dict[str, str]:
        _validate_environment(value)
        return value


class ProjectConfig(_StrictModel):
    schema_version: Literal[3]
    corpus_version: str = Field(min_length=1)
    dev: DevConfig | None = None
    run: dict[str, RunEntry] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_corpus_version(self) -> Self:
        require_semver(self.corpus_version, "corpus_version")
        _validate_names(self.run, "run entry")
        return self


@dataclass(frozen=True)
class ResolvedConfig:
    """Validated current configuration views and declaration digests."""

    base: ProjectConfig
    local: dict[str, Any] | None
    effective: ProjectConfig
    base_digest: str
    local_digest: str | None
    effective_digest: str


def load_config(repo: Path) -> ResolvedConfig:
    """Load one runnable schema-v3 base and optional v3 overlay."""

    root = repo.resolve()
    base_data = _load_required_json(root / PROJECT_CONFIG_FILE, PROJECT_CONFIG_FILE)
    base = _validate_project(base_data, PROJECT_CONFIG_FILE)
    base_digest = declaration_digest(base)

    local_path = root / LOCAL_CONFIG_FILE
    if not local_path.exists() and not local_path.is_symlink():
        return ResolvedConfig(base, None, base, base_digest, None, base_digest)

    local = _load_required_json(local_path, LOCAL_CONFIG_FILE)
    _validate_local_overlay(local, committed_run_entries=set(base.run))
    effective_data = _merge(base_data, local)
    effective = _validate_project(effective_data, "effective configuration")
    return ResolvedConfig(
        base,
        local,
        effective,
        base_digest,
        declaration_digest_value(local),
        declaration_digest(effective),
    )


def parse_project_config(
    content: bytes, source: str = PROJECT_CONFIG_FILE
) -> ProjectConfig:
    return _validate_project(_parse_json_bytes(content, source), source)


def parse_local_overlay(
    content: bytes, source: str = LOCAL_CONFIG_FILE
) -> dict[str, Any]:
    value = _parse_json_bytes(content, source)
    _validate_local_overlay(value)
    return value


def render_config_value(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
        + "\n"
    ).encode("utf-8")


def declaration_digest(config: ProjectConfig) -> str:
    return declaration_digest_value(config.model_dump(mode="json"))


def declaration_digest_value(value: object) -> str:
    canonical = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _validate_environment(value: Mapping[str, str]) -> None:
    for key, item in value.items():
        if not key or "=" in key or "\0" in key:
            raise ValueError(
                "environment keys must be non-empty and contain neither '=' nor NUL"
            )
        if "\0" in item:
            raise ValueError("environment values must not contain NUL")


def _validate_names(values: Mapping[str, object], kind: str) -> None:
    invalid = sorted(name for name in values if not _NAME.fullmatch(name))
    if invalid:
        raise ValueError(f"invalid {kind} name: {invalid[0]!r}")


def _load_required_json(path: Path, label: str) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        kind = "symlink" if path.is_symlink() else "regular file"
        expected = (
            "regular file" if kind == "regular file" else "non-symlink regular file"
        )
        raise ConfigError(f"{label} must be a {expected}")
    try:
        return _parse_json_bytes(path.read_bytes(), label)
    except OSError as error:
        raise ConfigError(f"cannot read {label}: {error}") from error


def _parse_json_bytes(content: bytes, source: str) -> dict[str, Any]:
    try:
        value = json.loads(
            content.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_non_finite,
        )
    except UnicodeDecodeError as error:
        raise ConfigError(f"{source} must be UTF-8 JSON") from error
    except json.JSONDecodeError as error:
        raise ConfigError(f"{source} must be valid JSON: {error.msg}") from error
    except ValueError as error:
        raise ConfigError(f"{source} is invalid: {error}") from error
    if not isinstance(value, dict):
        raise ConfigError(f"{source} must contain a JSON object")
    _reject_nulls(value, source)
    return value


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate key {key!r}")
        result[key] = value
    return result


def _reject_non_finite(value: str) -> None:
    raise ValueError(f"non-finite JSON value {value!r}")


def _reject_nulls(value: object, source: str, path: str = "$") -> None:
    if value is None:
        raise ConfigError(f"{source} does not support null values ({path})")
    if isinstance(value, dict):
        for key, child in value.items():
            _reject_nulls(child, source, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_nulls(child, source, f"{path}[{index}]")


def _validate_project(value: dict[str, Any], source: str) -> ProjectConfig:
    try:
        return ProjectConfig.model_validate(value)
    except ValidationError as error:
        raise ConfigError(
            f"{source} does not match schema v{CONFIG_SCHEMA_VERSION}: {error}"
        ) from error


def _validate_local_overlay(
    value: dict[str, Any], *, committed_run_entries: set[str] | None = None
) -> None:
    _validate_overlay_object(value, {"schema_version", "dev", "run"}, "$")
    if value.get("schema_version") != CONFIG_SCHEMA_VERSION:
        raise ConfigError(
            f"{LOCAL_CONFIG_FILE} must declare schema_version {CONFIG_SCHEMA_VERSION}"
        )
    if "dev" in value:
        _validate_overlay_dev(value["dev"], "$.dev")
    if "run" in value:
        _validate_overlay_run(value["run"], "$.run", committed_run_entries)


def _validate_overlay_run(
    value: object, path: str, committed_entries: set[str] | None
) -> None:
    if not isinstance(value, dict):
        return
    try:
        _validate_names(value, "run entry")
    except ValueError as error:
        raise ConfigError(str(error)) from error
    if committed_entries is not None:
        local_only = sorted(set(value) - committed_entries)
        if local_only:
            raise ConfigError(
                f"{LOCAL_CONFIG_FILE} cannot create run entry {local_only[0]!r}"
            )
    for name, entry in value.items():
        if isinstance(entry, dict):
            _validate_overlay_object(
                entry, {"argv", "cwd", "env_files", "env"}, f"{path}.{name}"
            )


def _validate_overlay_dev(value: object, path: str) -> None:
    if not isinstance(value, dict):
        return
    _validate_overlay_object(value, {"targets"}, path)
    if "targets" in value and isinstance(value["targets"], dict):
        for name, target in value["targets"].items():
            _validate_overlay_target(target, f"{path}.targets.{name}")


def _validate_overlay_target(value: object, path: str) -> None:
    if not isinstance(value, dict):
        return
    _validate_overlay_object(
        value,
        {
            "scope",
            "host_key",
            "probe",
            "provision",
            "stop",
            "access",
            "readiness_timeout",
            "poll_interval",
        },
        path,
    )
    if "probe" in value and isinstance(value["probe"], dict):
        kind = value["probe"].get("kind")
        allowed = {
            "http": {
                "kind",
                "url",
                "method",
                "success_status",
                "timeout",
                "network_scope",
                "insecure_tls",
            },
            "tcp": {"kind", "host", "port", "timeout", "network_scope"},
            "exec": {"kind", "argv", "cwd", "timeout", "output_limit"},
        }
        if kind in allowed:
            _validate_overlay_object(value["probe"], allowed[kind], f"{path}.probe")
    if "provision" in value and isinstance(value["provision"], dict):
        kind = value["provision"].get("kind")
        allowed = {
            "exec": {"kind", "mode", "argv", "cwd", "env"},
            "manual": {"kind"},
        }
        if kind in allowed:
            _validate_overlay_object(
                value["provision"], allowed[kind], f"{path}.provision"
            )
    if "stop" in value and isinstance(value["stop"], dict):
        kind = value["stop"].get("kind")
        allowed = {
            "exec": {"kind", "argv", "cwd", "env", "timeout"},
            "manual": {"kind"},
        }
        if kind in allowed:
            _validate_overlay_object(value["stop"], allowed[kind], f"{path}.stop")


def _validate_overlay_object(
    value: dict[str, Any], allowed: set[str], path: str
) -> None:
    unexpected = sorted(set(value) - allowed)
    if unexpected:
        raise ConfigError(
            f"{LOCAL_CONFIG_FILE} contains a non-overrideable or unknown field "
            f"at {path}: {unexpected[0]}"
        )


@overload
def _merge(base: dict[str, Any], local: dict[str, Any]) -> dict[str, Any]: ...


@overload
def _merge(base: object, local: object) -> object: ...


def _merge(base: object, local: object) -> object:
    if isinstance(base, dict) and isinstance(local, dict):
        merged = dict(base)
        for key, value in local.items():
            merged[key] = _merge(merged[key], value) if key in merged else value
        return merged
    return local
