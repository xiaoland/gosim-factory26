"""Physical Docker run control; Braid object changes remain CLI operations."""

from contextlib import contextmanager
import json
from pathlib import Path, PurePosixPath
import re
import select
import subprocess


AGENT_ENV = ("BRAID_AGENT_RUNTIME", "BRAID_STATE", "BRAID_CLI_BINDING_ID")
INSPECT_FORMAT = '{"id":{{json .Id}},"state":{{json .State}},"mounts":{{json .Mounts}},"mount_options":{{json .HostConfig.Mounts}},"labels":{{json .Config.Labels}}}'


class ControlError(RuntimeError):
    def __init__(self, detail, *, uncertain):
        super().__init__(detail)
        self.uncertain = uncertain


def configuration(value):
    if not isinstance(value, dict):
        raise ValueError("docker 必须是对象")
    for key in ("runtime_container", "cli_container"):
        if not isinstance(value.get(key), str) or not re.fullmatch("[0-9a-f]{64}", value[key]):
            raise ValueError(f"docker.{key} 需要容器完整 ID")
    if value["runtime_container"] == value["cli_container"]:
        raise ValueError("生成容器与 CLI 访问容器必须分离")
    for key in ("binary", "state"):
        path = value.get(key)
        if not isinstance(path, str) or not PurePosixPath(path).is_absolute() or ".." in PurePosixPath(path).parts:
            raise ValueError(f"docker.{key} 需要容器内绝对路径")
    result = {key: value[key] for key in ("runtime_container", "cli_container", "binary", "state")}
    if value.get("context") is not None:
        if not isinstance(value["context"], str) or not value["context"]:
            raise ValueError("docker.context 必须是固定非空名称")
        result["context"] = value["context"]
    if value.get("mounts") is not None:
        if not isinstance(value["mounts"], list) or not value["mounts"]:
            raise ValueError("docker.mounts 需要实际宿主挂载列表")
        result["mounts"] = []
        for mount in value["mounts"]:
            if (not isinstance(mount, dict) or not isinstance(mount.get("source"), str)
                    or not PurePosixPath(mount["source"]).is_absolute()
                    or ".." in PurePosixPath(mount["source"]).parts
                    or not isinstance(mount.get("destination"), str)
                    or not PurePosixPath(mount["destination"]).is_absolute()
                    or ".." in PurePosixPath(mount["destination"]).parts):
                raise ValueError("docker.mounts 需要宿主source与容器destination绝对路径")
            result["mounts"].append({"source": mount["source"], "destination": mount["destination"]})
    if value.get("access_owner") is not None:
        if value["access_owner"] != "console":
            raise ValueError("docker.access_owner 仅接受 console")
        result["access_owner"] = "console"
    if value.get("exp") is not None:
        binding = value["exp"]
        if (not isinstance(binding, dict) or set(binding) != {"experiment", "attempt_id"}
                or not isinstance(binding["experiment"], str) or not Path(binding["experiment"]).is_absolute()
                or not isinstance(binding["attempt_id"], str)
                or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", binding["attempt_id"])):
            raise ValueError("docker.exp 需要绝对 experiment 路径及固定 attempt_id")
        result["exp"] = dict(binding)
    return result


def base_command(config=None):
    return ["docker", "--context", config["context"]] if config and config.get("context") else ["docker"]


def cli_command(config):
    command = base_command(config) + ["exec", "-i", config["cli_container"], "env"]
    for name in AGENT_ENV:
        command.extend(["-u", name])
    return command + [config["binary"], "--state", config["state"]]


def docker(args, config=None):
    command = base_command(config) + args
    try:
        result = subprocess.run(command, text=True, capture_output=True, timeout=10, check=False)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise RuntimeError(f"Docker 执行未确认：{error}") from error
    if result.returncode:
        raise RuntimeError(f"Docker 退出码 {result.returncode}: {result.stderr.strip()}\n{result.stdout.strip()}")
    return result.stdout


def inspect(container, config=None):
    if config and config.get("context"):
        context = json.loads(docker(["context", "inspect", config["context"]], config))[0]
        endpoint = context["Endpoints"]["docker"]["Host"]
        if not endpoint.startswith("unix://"):
            raise RuntimeError("受管理Console仅支持本宿主Unix socket Docker context；远端挂载路径尚不可核实")
    value = json.loads(docker(["inspect", "--format", INSPECT_FORMAT, container], config))
    if value["id"] != container:
        raise RuntimeError("Docker 返回的容器身份与登记不一致")
    return value


def confirm_mounts(config, value):
    for expected in config.get("mounts", []):
        if not any(mount_source(value, mount) == expected["source"] and mount["Destination"] == expected["destination"] for mount in value["mounts"]):
            raise RuntimeError(f"访问容器挂载与登记不匹配：{expected}")
    if config.get("mounts"):
        declared = {"id": "registered", "mounts": [{"Source": mount["source"], "Destination": mount["destination"]}
                                                    for mount in config["mounts"]]}
        for path in (config["binary"], config["state"] + "/braid.sqlite3"):
            if mounted_database(value, path) != mounted_database(declared, path):
                raise RuntimeError(f"容器实际嵌套挂载改变执行文件来源：{path}")


def state_view(value):
    state = value["state"]
    return {"status": state["Status"], "running": state["Running"], "paused": state["Paused"],
            "pid": state["Pid"], "started_at": state["StartedAt"]}


def status(config):
    return state_view(inspect(config["runtime_container"], config))


def mount_source(value, mount):
    source = PurePosixPath(mount["Source"])
    if mount.get("Type") == "volume":
        options = [option for option in value.get("mount_options") or []
                   if option.get("Type") == "volume" and option.get("Target") == mount["Destination"]
                   and option.get("Source") == mount.get("Name")]
        if len(options) > 1:
            raise RuntimeError("Docker volume 挂载选项有歧义：" + mount["Destination"])
        subpath = (options[0].get("VolumeOptions") or {}).get("Subpath", "") if options else ""
        if not isinstance(subpath, str) or (subpath and (subpath.startswith("/") or any(part in ("", ".", "..") for part in subpath.split("/")))):
            raise RuntimeError("Docker volume Subpath 无效：" + repr(subpath))
        source /= subpath
    return str(source)


def mounted_database(value, database):
    path = PurePosixPath(database)
    mounts = [mount for mount in value["mounts"] if path.is_relative_to(mount["Destination"])]
    if not mounts:
        raise RuntimeError(f"容器 {value['id']} 的数据库未位于共享挂载中：{database}")
    mount = max(mounts, key=lambda entry: len(PurePosixPath(entry["Destination"]).parts))
    return str(PurePosixPath(mount_source(value, mount)) / path.relative_to(mount["Destination"]))


def execution_binding(config):
    binding = config.get("exp")
    if not binding:
        raise ValueError("缺少新 exp attempt 绑定；旧现场保留原冻结服务")
    root = Path(binding["experiment"])
    manifest = json.loads((root / "experiment.json").read_text())
    if manifest.get("kind") != "factory26.exp.experiment" or manifest.get("schema_version") != 1:
        raise ValueError("Console 需要新 experiment 合同")
    command = [manifest["controller_runtime"]["launcher"], "-B", "-m", "lab.exp.controller"]
    import os
    environment = dict(os.environ, PYTHONPATH=str(root / "source"), PYTHONDONTWRITEBYTECODE="1")
    result = subprocess.run(command + ["internal_observe", str(root), binding["attempt_id"]],
                            cwd=root / "source", env=environment, capture_output=True, text=True, check=True)
    observed = json.loads(result.stdout)
    identity = observed.get("backend_identity") or {}
    resources = [identity] + identity.get("external_resources", [])
    matches = [row for row in resources if row.get("container_id") == config["runtime_container"]]
    if len(matches) != 1:
        raise ValueError("Console 显示容器与 exp attempt 实际资源不同")
    physical = inspect(config["runtime_container"], config)
    match = matches[0]
    if physical["state"].get("StartedAt") != match.get("started_at") or any(
            physical["labels"].get(key) != value for key, value in match.get("labels", {}).items()):
        raise ValueError("Console 容器出生身份或 owner 与执行回执不同")
    return command, environment, root, observed


def control(config, action):
    if action == "pause":
        raise ControlError("当前 Harness 尚无公开静止协调合同，Console 不暂停可能持有写事务的进程", uncertain=False)
    try:
        command, environment, root, observed = execution_binding(config)
        binding = config["exp"]
        result = subprocess.run(command + ["internal_control", str(root), binding["attempt_id"], action,
                            json.dumps({"parameters": {"consumer": "console", "expected_incarnation": observed["incarnation_id"]}})],
                            cwd=root / "source", env=environment, capture_output=True, text=True, check=True)
        value = json.loads(result.stdout)
        if value.get("status") != "applied":
            raise ControlError("执行器尚未确认物理效果：" + json.dumps(value, ensure_ascii=False), uncertain=True)
        return {"runtime": status(config), "effect": value, "changed": True}
    except (RuntimeError, OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        raise ControlError(str(error), uncertain=True) from error
