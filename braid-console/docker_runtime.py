"""Physical Docker run control; Braid object changes remain CLI operations."""

from contextlib import contextmanager
import json
from pathlib import PurePosixPath
import re
import select
import subprocess


AGENT_ENV = ("BRAID_AGENT_RUNTIME", "BRAID_STATE", "BRAID_CLI_BINDING_ID")
INSPECT_FORMAT = '{"id":{{json .Id}},"state":{{json .State}},"mounts":{{json .Mounts}},"labels":{{json .Config.Labels}}}'
WRITER_GATE = """
import json, pathlib, select, sqlite3, sys
connection = None
try:
    database = pathlib.Path(sys.argv[1])
    connection = sqlite3.connect(database.as_uri() + "?mode=rw", uri=True, timeout=5)
    mode = connection.execute("PRAGMA journal_mode").fetchone()[0]
    if mode != "wal":
        raise RuntimeError("暂停门闩要求现有数据库使用 WAL，实际为 " + str(mode))
    connection.execute("BEGIN IMMEDIATE")
    print(json.dumps({"acquired": True}), flush=True)
    if not select.select([sys.stdin], [], [], 30)[0]:
        raise TimeoutError("暂停控制方未在 30 秒内释放写者门闩")
    sys.stdin.readline()
    connection.rollback()
    print(json.dumps({"released": True}), flush=True)
except Exception as error:
    print(json.dumps({"error": type(error).__name__ + ": " + str(error)},
                     ensure_ascii=False), flush=True)
    sys.exit(1)
finally:
    if connection is not None:
        connection.close()
"""


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
                    or not isinstance(mount.get("destination"), str)
                    or not PurePosixPath(mount["destination"]).is_absolute()
                    or ".." in PurePosixPath(mount["destination"]).parts):
                raise ValueError("docker.mounts 需要宿主source与容器destination绝对路径")
            result["mounts"].append({"source": mount["source"], "destination": mount["destination"]})
    if value.get("access_owner") is not None:
        if value["access_owner"] != "console":
            raise ValueError("docker.access_owner 仅接受 console")
        result["access_owner"] = "console"
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
        if not any(mount["Source"] == expected["source"] and mount["Destination"] == expected["destination"] for mount in value["mounts"]):
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


def mounted_database(value, database):
    path = PurePosixPath(database)
    mounts = [mount for mount in value["mounts"] if path.is_relative_to(mount["Destination"])]
    if not mounts:
        raise RuntimeError(f"容器 {value['id']} 的数据库未位于共享挂载中：{database}")
    mount = max(mounts, key=lambda entry: len(PurePosixPath(entry["Destination"]).parts))
    return str(PurePosixPath(mount["Source"]) / path.relative_to(mount["Destination"]))


@contextmanager
def writer_gate(config):
    # The lock must share the runtime's Linux kernel and WAL file namespace.
    command = base_command(config) + ["exec", "-i", config["cli_container"], "python3", "-u", "-c",
               WRITER_GATE, config["state"] + "/braid.sqlite3"]
    try:
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, text=True)
    except OSError as error:
        raise RuntimeError(f"无法启动暂停门闩：{error}") from error
    acquired = False
    failure = None
    first = ""
    try:
        if not select.select([process.stdout], [], [], 10)[0]:
            raise RuntimeError("暂停门闩未在 10 秒内返回取得回执")
        first = process.stdout.readline()
        if first.strip() != '{"acquired": true}':
            raise RuntimeError(f"暂停门闩未取得：{first.strip()}")
        acquired = True
        yield process
        if process.poll() is not None:
            raise RuntimeError("确认暂停前，写者门闩已提前退出")
    except Exception as error:
        failure = error
    try:
        output, _ = process.communicate(input="\n", timeout=10)
        if process.returncode or (acquired and output.strip() != '{"released": true}'):
            raise RuntimeError(f"暂停门闩退出码 {process.returncode}：{first.strip()}\n{output.strip()}")
    except (OSError, subprocess.TimeoutExpired, RuntimeError) as error:
        process.kill()
        output, _ = process.communicate()
        detail = f"写者门闩释放未确认：{error}\n{output.strip()}"
        failure = RuntimeError(f"{failure}\n{detail}" if failure else detail)
    if failure:
        raise failure


def control(config, action):
    attempted = False
    try:
        before = inspect(config["runtime_container"], config)
        current = state_view(before)
        if not current["running"] or before["state"]["Restarting"]:
            raise RuntimeError(f"当前容器状态为 {current['status']}，不能暂停或恢复；不会启动或重建容器")
        if action == "resume":
            if current["paused"]:
                attempted = True
                docker(["unpause", config["runtime_container"]], config)
            after = status(config)
            if not after["running"] or after["paused"]:
                raise RuntimeError(f"恢复后实际状态未确认：{after}")
            return {"runtime": after, "changed": attempted}
        access = inspect(config["cli_container"], config)
        confirm_mounts(config, access)
        if not access["state"]["Running"] or access["state"]["Paused"]:
            raise RuntimeError("CLI 访问容器需要运行且未暂停")
        database = config["state"] + "/braid.sqlite3"
        if mounted_database(before, database) != mounted_database(access, database):
            raise RuntimeError("生成与 CLI 容器未共享同一数据库挂载，不能建立暂停门闩")
        with writer_gate(config):
            if not current["paused"]:
                attempted = True
                docker(["pause", config["runtime_container"]], config)
            after = status(config)
            if not after["running"] or not after["paused"]:
                raise RuntimeError(f"暂停后实际状态未确认：{after}")
        return {"runtime": after, "changed": attempted, "writer_lock": "available"}
    except (RuntimeError, OSError, ValueError, KeyError) as error:
        raise ControlError(str(error), uncertain=attempted) from error
