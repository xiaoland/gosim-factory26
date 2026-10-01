"""Read registered workspace files and shared origin objects without materializing Git trees."""

import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys

import docker_runtime
import redaction
import service


# This fixed source executes in the same namespace as the registered Braid CLI.
READER = Path(redaction.__file__).read_text() + r'''
import json, stat, subprocess, sys
from datetime import datetime, timezone

MAX_FILE = 1024 * 1024
MAX_ENTRIES = 2000
DIRECTORY_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW


def relative_parts(path):
    if not isinstance(path, str):
        raise ValueError("文件路径须为安全相对路径")
    path.encode("utf-8")
    parts = path.split("/") if path else []
    if any(part in ("", ".", "..") or part.lower() == ".git" or "\\" in part or any(ord(c) < 32 or ord(c) == 127 for c in part) for part in parts):
        raise ValueError("文件路径须为安全相对路径，且不能浏览 .git")
    return parts


def open_root(root):
    if not root.startswith("/"):
        raise ValueError("登记读取根须为绝对路径")
    descriptor = os.open("/", DIRECTORY_FLAGS)
    try:
        for part in root.split("/")[1:]:
            if not part or part in (".", ".."):
                raise ValueError("登记读取根包含无效路径段")
            child = os.open(part, DIRECTORY_FLAGS, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        return descriptor
    except Exception:
        os.close(descriptor)
        raise


def text_content(data, result):
    result["size"] = len(data)
    if b"\0" in data:
        result["notice"] = "二进制内容无法预览"
        return result
    try:
        result["content"] = data.decode("utf-8")
    except UnicodeDecodeError as error:
        result["notice"] = "内容不是 UTF-8 文本，无法预览：" + str(error)
    return result


def file_kind(mode):
    if stat.S_ISDIR(mode):
        return "directory"
    if stat.S_ISREG(mode):
        return "file"
    if stat.S_ISLNK(mode):
        return "symlink"
    return "unsupported"


def workspace_entries(descriptor, path):
    entries = []
    with os.scandir(descriptor) as children:
        for child in children:
            if child.name.lower() == ".git":
                continue
            try:
                child.name.encode("utf-8")
            except UnicodeEncodeError as error:
                raise ValueError(f"目录条目名称不是 UTF-8，无法表示：{child.name!r}") from error
            info = child.stat(follow_symlinks=False)
            kind = file_kind(info.st_mode)
            entry = {"name": child.name, "path": path + "/" + child.name if path else child.name, "kind": kind}
            if kind != "directory":
                entry["size"] = info.st_size
            if kind == "unsupported":
                entry["notice"] = "非普通文件不读取：" + stat.filemode(info.st_mode)
            entries.append(entry)
            if len(entries) > MAX_ENTRIES:
                raise ValueError(f"目录 {path!r} 超过 2000 项读取边界；未截断或分页")
    return sorted(entries, key=lambda entry: (entry["kind"] != "directory", entry["name"]))


def workspace(root, path, parts):
    descriptor = open_root(root)
    try:
        for part in parts[:-1]:
            child = os.open(part, DIRECTORY_FLAGS, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        if not parts:
            return {"kind": "directory", "entries": workspace_entries(descriptor, path)}
        name = parts[-1]
        info = os.stat(name, dir_fd=descriptor, follow_symlinks=False)
        kind = file_kind(info.st_mode)
        if kind == "symlink":
            target = os.readlink(os.fsencode(name), dir_fd=descriptor)
            result = text_content(target, {"kind": kind})
            result["notice"] = "符号链接仅显示目标路径，不读取目标" + ("；" + result["notice"] if result.get("notice") else "")
            return result
        if kind == "directory":
            child = os.open(name, DIRECTORY_FLAGS, dir_fd=descriptor)
            try:
                return {"kind": kind, "entries": workspace_entries(child, path)}
            finally:
                os.close(child)
        if kind != "file":
            raise ValueError("非普通文件不读取：" + stat.filemode(info.st_mode))
        # O_NONBLOCK prevents a concurrent replacement with a FIFO from blocking before fstat.
        child = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=descriptor)
        with os.fdopen(child, "rb") as stream:
            current = os.fstat(stream.fileno())
            if not stat.S_ISREG(current.st_mode):
                raise ValueError("读取时文件类型已改变；非普通文件不读取：" + stat.filemode(current.st_mode))
            if current.st_size > MAX_FILE:
                raise ValueError(f"文件 {path!r} 为 {current.st_size} 字节，超过 1MiB 读取边界；未截断")
            data = stream.read(MAX_FILE + 1)
            if len(data) > MAX_FILE:
                raise ValueError(f"文件 {path!r} 读取时超过 1MiB 边界；未截断")
        return text_content(data, {"kind": kind})
    finally:
        os.close(descriptor)


def git(*args, data=None):
    environment = {name: value for name, value in os.environ.items() if not name.startswith("GIT_")}
    environment.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull, GIT_NO_REPLACE_OBJECTS="1",
                       GIT_OPTIONAL_LOCKS="0", GIT_TERMINAL_PROMPT="0", GIT_NO_LAZY_FETCH="1")
    try:
        result = subprocess.run(["git", "--git-dir=.", *args], input=data, capture_output=True,
                                timeout=20, env=environment, check=False)
    except subprocess.TimeoutExpired as error:
        raise RuntimeError(f"Git 读取超时：{error}；stderr={(error.stderr or b'').decode('utf-8', 'replace')}") from error
    if result.returncode:
        raise RuntimeError(f"Git 读取退出码 {result.returncode}: {result.stderr.decode('utf-8', 'replace').strip()}\n{result.stdout.decode('utf-8', 'replace').strip()}")
    return result.stdout


def tree_entries(tree, path):
    entries = []
    for raw in git("ls-tree", "-z", tree).split(b"\0"):
        if not raw:
            continue
        metadata, raw_name = raw.split(b"\t", 1)
        mode, object_type, oid = metadata.decode("ascii").split(" ")
        name = raw_name.decode("utf-8")
        if name.lower() == ".git":
            continue
        kind = {"040000": "directory", "100644": "file", "100755": "file", "120000": "symlink", "160000": "submodule"}.get(mode, "unsupported")
        entry = {"name": name, "path": path + "/" + name if path else name, "kind": kind, "oid": oid, "mode": mode}
        if kind == "unsupported":
            entry["notice"] = "不支持读取此 Git tree 类型：" + mode + " " + object_type
        entries.append(entry)
        if len(entries) > MAX_ENTRIES:
            raise ValueError(f"目录 {path!r} 超过 2000 项读取边界；未截断或分页")
    return entries


def require_full_origin(descriptor):
    # Braid creates a full bare origin. Older Git can fetch missing objects from partial clones.
    for key in git("config", "--includes", "--null", "--name-only", "--list").split(b"\0"):
        if re.fullmatch(rb"extensions\.partialclone|remote\..*\.(?:promisor|partialclonefilter)", key, re.IGNORECASE):
            raise ValueError("origin 仅支持完整裸仓库；发现 partial clone/promisor 配置：" + key.decode("utf-8", "replace"))
    objects = os.open("objects", DIRECTORY_FLAGS, dir_fd=descriptor)
    try:
        packs = os.open("pack", DIRECTORY_FLAGS, dir_fd=objects)
        try:
            with os.scandir(packs) as children:
                for child in children:
                    if child.name.lower().endswith(".promisor"):
                        raise ValueError(f"origin 仅支持完整裸仓库；发现 promisor pack 标记：{child.name!r}")
        finally:
            os.close(packs)
    finally:
        os.close(objects)


def origin(root, request, parts):
    descriptor = open_root(root)
    try:
        # The isolated reader pins the opened repository inode; Git never resolves a browser path.
        os.fchdir(descriptor)
        if git("rev-parse", "--is-bare-repository").strip() != b"true":
            raise ValueError("登记 state/origin.git 不是裸 Git 仓库")
        require_full_origin(descriptor)
        if request["action"] == "refs":
            refs = []
            for line in git("for-each-ref", "--format=%(refname)%00%(objectname)", "refs/heads/").splitlines():
                ref, commit = line.decode("utf-8").split("\0")
                refs.append({"ref": ref, "commit": commit})
            return {"refs": refs}
        commit = request.get("commit")
        if not isinstance(commit, str) or not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", commit):
            raise ValueError("origin 阅读需要完整的小写 commit SHA")
        identity = git("cat-file", "--batch-check=%(objectname) %(objecttype)", data=(commit + "\n").encode()).decode("ascii").strip()
        if identity != commit + " commit":
            raise ValueError(f"origin 中不是完整 commit 身份：请求={commit}，Git={identity}")
        tree = git("rev-parse", "--verify", commit + "^{tree}").decode("ascii").strip()
        current_path = ""
        entry = {"kind": "directory", "oid": tree}
        for part in parts:
            if entry["kind"] != "directory":
                raise ValueError(f"不能穿过 {entry['kind']} 读取子路径：{current_path}")
            entry = next((child for child in tree_entries(entry["oid"], current_path) if child["name"] == part), None)
            if entry is None:
                raise FileNotFoundError(f"commit {commit} 中没有路径：{request['path']}")
            current_path = current_path + "/" + part if current_path else part
        kind = entry["kind"]
        if kind == "directory":
            entries = [{key: value for key, value in child.items() if key not in ("oid", "mode")}
                       for child in tree_entries(entry["oid"], current_path)]
            return {"kind": kind, "entries": sorted(entries, key=lambda child: (child["kind"] != "directory", child["name"])), "commit": commit}
        if kind == "submodule":
            return {"kind": kind, "content": entry["oid"], "notice": "子模块仅显示保存的 commit 身份，不读取外部仓库", "commit": commit}
        if kind not in ("file", "symlink"):
            raise ValueError(entry["notice"])
        size = int(git("cat-file", "-s", entry["oid"]).strip())
        if size > MAX_FILE:
            raise ValueError(f"文件 {request['path']!r} 为 {size} 字节，超过 1MiB 读取边界；未截断")
        content = git("cat-file", "blob", entry["oid"])
        if len(content) > MAX_FILE:
            raise ValueError(f"文件 {request['path']!r} 超过 1MiB 读取边界；未截断")
        result = text_content(content, {"kind": kind, "commit": commit})
        if kind == "symlink":
            result["notice"] = "符号链接仅显示保存的目标路径，不读取目标" + ("；" + result["notice"] if result.get("notice") else "")
        return result
    finally:
        os.close(descriptor)


try:
    request = json.load(sys.stdin)
    path = request.get("path", "")
    parts = relative_parts(path)
    result = origin(request["root"], request, parts) if request["source"] == "origin" else workspace(request["root"], path, parts)
    result.update(root=request["root"], observed_at=datetime.now(timezone.utc).isoformat())
    if request["action"] != "refs":
        result["path"] = path
    print(json.dumps(redact(result), ensure_ascii=False))
except Exception as error:
    print(redact(type(error).__name__ + ": " + str(error)), file=sys.stderr)
    sys.exit(1)
'''


def _read(run, source, path="", *, record=None, commit=None, action="read"):
    if run["mode"] == "archive":
        raise ValueError("此归档未保存 origin 或具备明确会话映射的工作区；不会读取原现场路径")
    if source not in ("workspace", "origin"):
        raise ValueError("代码来源须为 workspace 或 origin")
    if (not isinstance(path, str) or (path and any(part in ("", ".", "..") or part.lower() == ".git" or "\\" in part
            or any(ord(c) < 32 or ord(c) == 127 for c in part) for part in path.split("/")))):
        raise ValueError("文件路径须为安全相对路径，且不能浏览 .git")
    if source == "origin" and action != "refs" and (not isinstance(commit, str) or not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", commit)):
        raise ValueError("origin 阅读需要完整的小写 commit SHA")
    config = run["docker"]
    state = config["state"] if config else run["state"]
    if source == "origin":
        root = str(PurePosixPath(state) / "origin.git")
    else:
        root = record.get("worktree") if record else None
    if not isinstance(root, str) or not PurePosixPath(root).is_absolute() or ".." in root.split("/"):
        raise ValueError("CLI 未提供此会话的有效 worktree 登记目录")
    root = str(PurePosixPath(root))
    if config:
        _, access = service.access({"service_id": run["service_id"]}, run)
        if not access["state"]["Running"] or access["state"]["Paused"]:
            raise ValueError("CLI 访问容器需要运行且未暂停")
        declared = {"id": "registered", "mounts": [{"Source": mount["source"], "Destination": mount["destination"]}
                                                  for mount in config["mounts"]]}
        expected = docker_runtime.mounted_database(declared, root)
        inspected_paths = [root] + [mount["Destination"] for mount in access["mounts"]
                                    if PurePosixPath(mount["Destination"]).is_relative_to(PurePosixPath(root))]
        for inspected_path in inspected_paths:
            if docker_runtime.mounted_database(access, inspected_path) != docker_runtime.mounted_database(declared, inspected_path):
                raise ValueError("容器实际嵌套挂载改变代码读取来源：" + inspected_path)
        if source == "workspace" and not Path(expected).is_relative_to(Path(run["workspace"])):
            raise ValueError("会话 worktree 不在登记 workspace 挂载内：" + root)
        command = docker_runtime.base_command(config) + ["exec", "-i", config["cli_container"], "python3", "-c", READER]
    else:
        if source == "workspace" and not Path(root).is_relative_to(Path(run["workspace"])):
            raise ValueError("会话 worktree 不在登记 workspace 内：" + root)
        command = [sys.executable, "-E", "-s", "-c", READER]
    request = {"source": source, "path": path, "root": root, "commit": commit, "action": action}
    try:
        result = subprocess.run(command, input=json.dumps(request), text=True, capture_output=True, timeout=30, check=False)
    except subprocess.TimeoutExpired as error:
        detail = error.stderr.decode("utf-8", "replace") if isinstance(error.stderr, bytes) else error.stderr or ""
        raise RuntimeError(redaction.redact(f"代码读取超过 30 秒，结果未确认；stderr={detail}")) from error
    except OSError as error:
        raise RuntimeError(redaction.redact(f"代码读取未确认：{error}")) from error
    if result.returncode:
        raise RuntimeError(redaction.redact(f"代码读取退出码 {result.returncode}: {result.stderr.strip()}\n{result.stdout.strip()}"))
    return json.loads(result.stdout)


def refs(run):
    return _read(run, "origin", action="refs")


def read(run, source, path="", *, record=None, commit=None):
    return _read(run, source, path, record=record, commit=commit)
