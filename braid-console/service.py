"""Prepare a stable Console artifact and manage only its explicitly owned resources."""

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import uuid

import archives
import docker_runtime


def stamp():
    return datetime.now(timezone.utc).isoformat()


def write_json(path, value):
    temporary = path.with_suffix(path.suffix + ".new")
    with temporary.open("w") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n"); stream.flush(); os.fsync(stream.fileno())
    temporary.replace(path)


@contextmanager
def service_lock(root):
    with (root / "http.lock").open("a") as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise ValueError("此服务 HTTP 实例正在运行；先停止该实例，不能并行修改配置") from error
        yield


def read(root):
    root = root.resolve(strict=True)
    record = json.loads((root / "manifest.json").read_text())
    if record.get("record_type") != "factory26.exp-console-service" or record.get("schema_version") != 1 or record.get("state") != "registered":
        raise ValueError("不支持此 Console 服务制品")
    if record.get("host") != socket.gethostname():
        raise ValueError("服务登记在另一宿主；需要在目标宿主重新准备，不猜测路径空间")
    python = record["interpreter"]
    if archives.identity(Path(python["executable"])) != python["sha256"]:
        raise ValueError("登记 Python 身份已改变；重新准备服务制品")
    for relative, expected in record["artifact_files"].items():
        if archives.identity(archives.within(root, relative)) != expected:
            raise ValueError(f"Console 制品身份已改变：{relative}")
    selected = archives.within(root, "app")
    for relative in record["artifact_files"]:
        if not archives.within(root, relative).is_relative_to(selected):
            raise ValueError("制品文件不属于当前所选程序")
    for required in ("service.py", "server.py", "web/dist/index.html"):
        if (selected / required).relative_to(root).as_posix() not in record["artifact_files"]:
            raise ValueError(f"所选程序缺少冻结身份：{required}")
    return record


def live_error(run):
    """A missing live dependency disables that run, without hiding the service Home."""
    try:
        binary = Path(run["binary"])
        if not binary.is_file() or not os.access(binary, os.X_OK):
            raise ValueError(f"binary 不可执行：{binary}")
        expected = run.get("binary_sha256")
        if not isinstance(expected, str) or len(expected) != 64:
            raise ValueError("live接入缺少binary SHA-256身份")
        if archives.identity(binary) != expected:
            raise ValueError(f"受管理 binary 身份已改变：{binary}")
        if not (Path(run["state"]) / "braid.sqlite3").is_file():
            raise ValueError(f"state 缺少数据库：{run['state']}")
        if not run.get("workspace") or not Path(run["workspace"]).is_dir():
            raise ValueError(f"workspace 不可达：{run['workspace']}")
    except (OSError, ValueError) as error:
        return f"{type(error).__name__}: {error}"
    return None


def interpreter(path):
    executable = path.resolve(strict=True)
    if any(part in {"runs", "prepared", ".factory26"} for part in executable.parts):
        raise ValueError("Console Python 不得来自临时运行目录")
    result = subprocess.run([str(executable), "-E", "-s", "-c",
                             "import json,sys; print(json.dumps({'executable':sys.executable,'prefix':sys.prefix,'base_prefix':sys.base_prefix,'version':sys.version,'version_info':list(sys.version_info[:3])}))"],
                            text=True, capture_output=True, timeout=10, check=False)
    if result.returncode:
        raise ValueError(f"Python 身份读取退出码 {result.returncode}: {result.stderr}")
    value = json.loads(result.stdout)
    if value["version_info"] < [3, 11, 0]:
        raise ValueError("Console 服务需要 Python 3.11 或更新版本")
    for key in ("prefix", "base_prefix"):
        if any(part in {"runs", "prepared", ".factory26"} for part in Path(value[key]).parts):
            raise ValueError("Console Python 环境不得依赖运行目录")
    value.update(executable=str(executable), sha256=archives.identity(executable))
    return value


def managed_binary(destination, source):
    binary = source.resolve(strict=True)
    if not binary.is_file() or not os.access(binary, os.X_OK):
        raise ValueError("live binary 必须是可执行文件")
    digest = archives.identity(binary)
    managed = destination / "binaries" / digest / "braid"
    managed.parent.mkdir(parents=True, exist_ok=True)
    if not managed.exists():
        shutil.copy2(binary, managed)
    if archives.identity(managed) != digest:
        raise ValueError("已有受管理 binary 身份不匹配")
    return managed, digest


def registrations(destination, entries):
    if not isinstance(entries, list):
        raise ValueError("registry 必须是运行列表")
    runs, seen = [], set()
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("id"), str) or not entry["id"] or entry["id"] in seen:
            raise ValueError("运行 id 必须非空且唯一")
        seen.add(entry["id"])
        mode = entry.get("mode")
        run = {"id": entry["id"], "label": str(entry.get("label") or entry["id"]), "mode": mode}
        if entry.get("harness", "braid") != "braid":
            raise ValueError("当前只支持 Braid 接入")
        run["harness"] = "braid"
        if entry.get("run_record"):
            source_record = Path(entry["run_record"]).resolve(strict=True)
            if not source_record.is_file():
                raise ValueError("run_record 必须是现存生产者 JSON 文件")
            run["run_record"] = str(source_record)
        if mode == "archive":
            if entry.get("writable", False) or entry.get("docker") or entry.get("cli_command"):
                raise ValueError("archive 不得登记写入权限、CLI 或容器控制")
            archive = archives.Archive(entry["archive"])
            run.update(writable=False, archive=str(archive.root), archive_files=archive.files)
        elif mode == "live":
            if type(entry.get("writable")) is not bool or entry.get("cli_command"):
                raise ValueError("live 需要明确 writable；受管理服务不接受自由 cli_command")
            state = Path(entry["state"]).resolve(strict=True)
            if not (state / "braid.sqlite3").is_file():
                raise ValueError("live state 必须包含现存 Braid 数据库")
            workspace = Path(entry["workspace"]).resolve(strict=True)
            if not workspace.is_dir():
                raise ValueError("live workspace 必须是原执行路径空间的宿主目录")
            managed, digest = managed_binary(destination, Path(entry["binary"]))
            run.update(writable=entry["writable"], state=str(state), workspace=str(workspace), binary=str(managed), binary_sha256=digest)
            if entry.get("docker"):
                config = docker_runtime.configuration(entry["docker"])
                if not config.get("context") or not config.get("mounts"):
                    raise ValueError("受管理 Docker 接入需要固定 context 与宿主 mounts")
                if not any(Path(mount["source"]).resolve() == workspace for mount in config["mounts"]):
                    raise ValueError("Docker mounts 必须明确包含登记的 workspace 宿主根")
                from pathlib import PurePosixPath
                state_in_container = PurePosixPath(config["state"])
                containing = [mount for mount in config["mounts"] if state_in_container.is_relative_to(mount["destination"])]
                if not containing:
                    raise ValueError("Docker state 未映射到登记的宿主挂载")
                mount = max(containing, key=lambda value: len(PurePosixPath(value["destination"]).parts))
                if (Path(mount["source"]) / state_in_container.relative_to(mount["destination"])).resolve() != state:
                    raise ValueError("Docker state 映射与宿主 state 不一致")
                # The deployer mounts this prepared binary at the declared container binary path.
                config["mounts"].append({"source": str(managed), "destination": config["binary"]})
                config["access_owner"] = "console"
                run["docker"] = config
        else:
            raise ValueError("每项 mode 必须是 live 或 archive")
        runs.append(run)
    return runs


def freeze_application(destination):
    source = Path(__file__).resolve().parent
    if not (source / "web/dist/index.html").is_file():
        raise ValueError("先构建前端 web/dist")
    destination.mkdir(parents=True)
    for path in sorted(source.glob("*.py")):
        shutil.copy2(path, destination / path.name)
    shutil.copytree(source / "web/dist", destination / "web/dist")


def prepare(destination, registry, python, *, development_output=False):
    # A prepared directory is never silently updated or installed over a live service.
    destination = destination.expanduser().absolute()
    if destination.exists():
        raise ValueError("目标已经存在；为新版本选择独立服务目录")
    if not development_output and any(part in {"runs", "prepared", ".factory26"} for part in destination.parts):
        raise ValueError("长期服务目录不得位于临时运行目录；本次独立开发材料核对可显式使用 --development-output")
    entries = json.loads(registry.read_text())
    if not isinstance(entries, list):
        raise ValueError("输入 registry 必须是运行列表；允许先准备空服务再登记实际接入")
    runtime = interpreter(python)
    destination.mkdir(parents=True)
    selected = destination / "app"
    freeze_application(selected)
    runs = registrations(destination, entries)
    record = {"schema_version": 1, "record_type": "factory26.exp-console-service", "service_id": str(uuid.uuid4()),
              "host": socket.gethostname(), "created_at": stamp(), "state": "registered", "interpreter": runtime,
              "deployment_scope": "development-output" if development_output else "service",
              "artifact_files": {path.relative_to(destination).as_posix(): archives.identity(path)
                                 for path in sorted(selected.rglob("*")) if path.is_file()},
              "runs": runs, "retired_run_ids": [], "resources": {"http": {"owner": "console", "bind": "127.0.0.1"},
                                          "ssh_forward": {"owner": "operator", "managed_by_http": False},
                                          "generation_containers": {"owner": "experiment", "managed_by_http": False}},
              "access_log": {"max_bytes": 5 * 1024 * 1024, "backups": 3},
              "journal": "console-actions.jsonl"}
    write_json(destination / "manifest.json", record)
    return {"service": str(destination), "service_id": record["service_id"], "runs": [run["id"] for run in runs]}


def access(record, run):
    config = run.get("docker")
    if run["mode"] != "live" or not config or config.get("access_owner") != "console":
        raise ValueError("此接入没有 Console 自有访问容器")
    value = docker_runtime.inspect(config["cli_container"], config)
    labels = value.get("labels") or {}
    if labels.get("factory26.console.service") != record["service_id"] or labels.get("factory26.console.run") != run["id"]:
        raise ValueError("访问容器所有权标签不匹配；不能操作或解除引用")
    docker_runtime.confirm_mounts(config, value)
    return config, value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("prepare", help="在新目录冻结程序、前端、Python身份、binary与接入配置")
    build.add_argument("--destination", required=True, type=Path)
    build.add_argument("--registry", required=True, type=Path)
    build.add_argument("--python", type=Path, default=Path(sys.executable))
    build.add_argument("--development-output", action="store_true", help="允许本次新输出目录中的独立开发制品；不作为现有用户服务迁移")
    for name in ("serve", "show", "binary", "register", "access-start", "access-stop", "release"):
        command = commands.add_parser(name)
        command.add_argument("--service", required=True, type=Path)
        if name == "binary":
            command.add_argument("--source", required=True, type=Path)
        if name == "register":
            command.add_argument("--registry", required=True, type=Path)
        if name == "serve":
            command.add_argument("--port", type=int, default=8765)
        if name in ("access-start", "access-stop", "release"):
            command.add_argument("--run", required=True)
        if name == "release":
            command.add_argument("--confirm-no-forward", action="store_true", required=True,
                                 help="操作方已关闭/确认无相关SSH转发；不据HTTP退出推断")
    args = parser.parse_args()
    if args.command == "prepare":
        result = prepare(args.destination, args.registry, args.python, development_output=args.development_output)
    else:
        root = args.service.resolve(strict=True)
        record = read(root)
        if args.command == "serve":
            os.execv(record["interpreter"]["executable"], [record["interpreter"]["executable"], "-E", "-s",
                     str(root / "app/server.py"), "--service", str(root), "--port", str(args.port)])
        if args.command == "show":
            result = record
        else:
            with service_lock(root):
                record = read(root)
                if args.command in ("binary", "register"):
                    from server import journal
                    event = {"at": stamp(), "action": args.command, "status": "started"}
                    journal(root / record["journal"], event)
                    try:
                        if args.command == "binary":
                            managed, digest = managed_binary(root, args.source)
                            result = {"binary": str(managed), "sha256": digest}
                        else:
                            additions = registrations(root, json.loads(args.registry.read_text()))
                            used = {run["id"] for run in record["runs"]} | set(record.get("retired_run_ids", []))
                            if {run["id"] for run in additions} & used:
                                raise ValueError("运行 id 已登记或已释放；禁止将旧身份重新指向新现场或归档")
                            record["runs"].extend(additions)
                            write_json(root / "manifest.json", record)
                            result = {"registered": [run["id"] for run in additions]}
                    except Exception as error:
                        journal(root / record["journal"], {**event, "at": stamp(), "status": "unconfirmed", "error": str(error)})
                        raise
                    journal(root / record["journal"], {**event, "at": stamp(), "status": "completed", "result": result})
                    print(json.dumps(result, ensure_ascii=False, indent=2))
                    return
                run = next((run for run in record["runs"] if run["id"] == args.run), None)
                if run is None:
                    raise ValueError("接入未登记")
                from server import journal
                event = {"at": stamp(), "run": args.run, "action": args.command, "status": "started"}
                journal(root / record["journal"], event)
                try:
                    if args.command == "release":
                        if run.get("docker"):
                            _, value = access(record, run)
                            if value["state"]["Running"]:
                                raise ValueError("访问容器仍在运行；先显式停止Console自有访问容器")
                        record["runs"] = [row for row in record["runs"] if row["id"] != args.run]
                        record.setdefault("retired_run_ids", []).append(args.run)
                        write_json(root / "manifest.json", record)
                        result = {"released": args.run, "removed_registration": run, "forward_confirmed_absent": True}
                    else:
                        config, _ = access(record, run)
                        output = docker_runtime.docker(["start" if args.command == "access-start" else "stop", config["cli_container"]], config)
                        value = docker_runtime.inspect(config["cli_container"], config)
                        expected = args.command == "access-start"
                        if value["state"]["Running"] != expected:
                            raise RuntimeError(f"访问容器终态未确认：{output}")
                        result = {"container": value["id"], "state": value["state"]}
                except Exception as error:
                    journal(root / record["journal"], {**event, "at": stamp(), "status": "unconfirmed", "error": str(error)})
                    raise
                journal(root / record["journal"], {**event, "at": stamp(), "status": "completed", "result": result})
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
