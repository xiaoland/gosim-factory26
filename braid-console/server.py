#!/usr/bin/env python3
"""Factory26 Exp Console: registered experiments and Braid collaboration details."""

import argparse
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import logging
from logging.handlers import RotatingFileHandler
import mimetypes
import re
import os
from pathlib import Path
import subprocess
import signal
import sys
import threading
import uuid
from urllib.parse import parse_qs, unquote, urlsplit

import docker_runtime
import native_sessions
import code_files
import archives
import service
import run_records


WEB_DIST = Path(__file__).parent / "web" / "dist"
JOURNAL_LOCK = threading.Lock()
MAX_POST = 1_000_000
# Only declared application pages receive the SPA entry. Missing assets and API
# endpoints keep their real error responses rather than becoming HTML.
APP_PAGE = re.compile(r"/runs/[^/]+(?:/(?:issues|prs)/[1-9][0-9]*(?:/reviews/[1-9][0-9]*)?(?:/agents/[^/]+(?:/providers/[^/]+)?)?)?/?")


def application_page(path):
    if path == "/":
        return True
    parts = path.split("/")
    if any(part in (".", "..") or "\\" in part or any(ord(c) < 32 for c in part) for part in parts):
        return False
    if not APP_PAGE.fullmatch(path):
        return False
    if len(parts) > 6 and parts[5] == "reviews" and (parts[3] != "prs" or int(parts[6]) > 9007199254740991):
        return False
    return len(parts) < 5 or int(parts[4]) <= 9007199254740991



def load_registry(path):
    data = json.loads(path.read_text())
    if not isinstance(data, dict) or data.get("record_type") != "factory26.exp-console-service":
        raise ValueError("使用Factory26 Exp Console服务manifest；旧registry不再支持")
    service_id = data["service_id"]
    data = data["runs"]
    if not isinstance(data, list):
        raise ValueError("服务runs必须是列表；允许零登记")
    runs = {}
    for entry in data:
        if not isinstance(entry, dict) or not isinstance(entry.get("id"), str):
            raise ValueError("每个运行需要 id")
        if entry["id"] in runs or not entry["id"]:
            raise ValueError("运行 id 不得为空或重复")
        if type(entry.get("writable")) is not bool:
            raise ValueError(f'{entry["id"]}: writable 无效')
        run = {"id": entry["id"], "label": str(entry.get("label") or entry["id"]),
               "writable": entry["writable"], "mode": entry.get("mode", "live"),
               "docker": None, "cli_command": None, "operation_lock": threading.Lock(),
               "coverage": [], "archive_error": None, "service_id": service_id,
               "harness": entry.get("harness", "braid"), "facts": run_records.facts(entry), "access_error": None}
        if run["harness"] != "braid":
            raise ValueError(f'{entry["id"]}: 当前只支持Braid接入')
        if run["mode"] == "archive":
            if run["writable"] or entry.get("docker") or entry.get("cli_command"):
                raise ValueError("归档禁止写入和物理控制")
            try:
                run["archive_reader"] = archives.Archive(entry["archive"], entry.get("archive_files"))
                run["coverage"] = run["archive_reader"].coverage
            except (OSError, ValueError, archives.sqlite3.Error) as error:
                run["archive_error"] = f"{type(error).__name__}: {error}"
                run["access_error"] = run["archive_error"]
                run["coverage"] = ["归档读取不可用：" + run["archive_error"]]
            runs[entry["id"]] = run
            continue
        if run["mode"] != "live":
            raise ValueError("mode 必须是 live 或 archive")
        state, binary = Path(entry["state"]), Path(entry.get("binary") or "/unregistered-binary")
        if not state.is_absolute() or not binary.is_absolute():
            raise ValueError(f'{entry["id"]}: state/binary 需为绝对路径')
        if entry.get("cli_command"):
            raise ValueError("不支持自由cli_command；使用受管理本机binary或Docker配置")
        cli_command = None
        docker = entry.get("docker")
        if docker is not None:
            docker = docker_runtime.configuration(docker)
            cli_command = docker_runtime.cli_command(docker)
        run.update(state=str(state), binary=str(binary), cli_command=cli_command, docker=docker,
                   binary_sha256=entry.get("binary_sha256"), workspace=entry.get("workspace"))
        run["access_error"] = service.live_error(run)
        runs[entry["id"]] = run
    return runs


def braid(run, args, body=None, *, write=False):
    # Persisted Git/worktree paths belong to the run's execution namespace.
    command = list(run["cli_command"] or [run["binary"], "--state", run["state"]])
    if run["docker"] and run["docker"].get("mounts"):
        service.access({"service_id": run["service_id"]}, run)
    if write:
        command.append("--external")
    command.extend(args)
    environment = os.environ.copy()
    for name in ("BRAID_AGENT_RUNTIME", "BRAID_STATE", "BRAID_CLI_BINDING_ID"):
        environment.pop(name, None)
    try:
        result = subprocess.run(command, input=body, text=True, capture_output=True,
                                timeout=30, env=environment, check=False)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise RuntimeError(f"CLI 执行未确认：{error}") from error
    if result.returncode:
        raise RuntimeError(f"CLI 退出码 {result.returncode}: {result.stderr.strip()}\n{result.stdout.strip()}")
    return result.stdout


def braid_json(run, args):
    return json.loads(braid(run, args))


def item_view(run, kind, item_id):
    if run["mode"] == "archive":
        return archive_reader(run).item(kind, item_id)
    return braid_json(run, [kind, "view", str(item_id), "--json"])


def archive_reader(run):
    if run["archive_error"]:
        raise ValueError(run["archive_error"])
    return run["archive_reader"]


def session_inventory(run):
    if run["mode"] == "archive":
        return archive_reader(run).records
    records = braid_json(run, ["status", "--json"])["physical_sessions"]
    for record in records:
        record["record_id"] = Path(record["context_path"]).parent.name
    return records


def action_command(payload):
    kind, item_id, action = payload.get("kind"), payload.get("id"), payload.get("action")
    if kind not in ("issue", "pr") or type(item_id) is not int or item_id < 1:
        raise ValueError("目标须为有效 Issue/PR")
    if action == "edit":
        title, body = payload.get("title"), payload.get("body")
        if not isinstance(title, str) or not title.strip() or not isinstance(body, str):
            raise ValueError("标题和正文无效")
        if type(payload.get("revision")) is not int:
            raise ValueError("编辑需要当前 revision")
        return [kind, "edit", str(item_id), f"--title={title}", "--body-file", "-"], body
    if action == "comment":
        body = payload.get("body")
        if not isinstance(body, str) or not body.strip():
            raise ValueError("评论不能为空")
        command = [kind, "comment", str(item_id), "--body-file", "-", "--json"]
        reply = payload.get("reply_to")
        if reply is not None:
            if type(reply) is not int or reply < 1:
                raise ValueError("回复目标无效")
            command.extend(["--reply-to", str(reply)])
        return command, body
    if action in ("hide", "unhide", "resolve", "unresolve"):
        comment = payload.get("comment")
        if type(comment) is not int or comment < 1:
            raise ValueError("评论 ID 无效")
        command = ["comment", action, str(comment)]
        if action == "hide":
            reason = payload.get("reason")
            if not isinstance(reason, str) or not reason.strip():
                raise ValueError("隐藏评论需要原因")
            command.append(f"--reason={reason}")
        return command, None
    if action in ("close", "reopen"):
        command = [kind, action, str(item_id)]
        if action == "close" and kind == "issue":
            reason = payload.get("reason")
            if reason not in ("completed", "not planned", "duplicate"):
                raise ValueError("Issue 关闭原因无效")
            command.append(f"--reason={reason}")
        return command, None
    raise ValueError("未知操作")


def journal(path, record):
    line = json.dumps(record, ensure_ascii=False) + "\n"
    with JOURNAL_LOCK, path.open("a", encoding="utf-8") as stream:
        stream.write(line)
        stream.flush()
        os.fsync(stream.fileno())


class ConsoleServer(ThreadingHTTPServer):
    def handle_error(self, request, client_address):
        logging.getLogger("console.access").exception("HTTP request failed: %s", client_address)


class Handler(BaseHTTPRequestHandler):
    runs = {}
    journal_path = None

    def log_message(self, format, *args):
        logging.getLogger("console.access").info("%s %s", self.client_address[0], format % args)

    def reply(self, status, data):
        encoded = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def run_for(self, value):
        try:
            run = self.runs[value]
        except KeyError as error:
            raise ValueError("未登记的运行") from error
        if run["mode"] == "live":
            error = service.live_error(run)
            run["access_error"] = error
            if error:
                raise ValueError(error)
        return run

    def do_GET(self):
        url = urlsplit(self.path)
        if not url.path.startswith("/api/"):
            path = (WEB_DIST / unquote(url.path).lstrip("/")).resolve()
            if not path.is_relative_to(WEB_DIST.resolve()):
                return self.reply(404, {"error": "文件不存在"})
            if application_page(unquote(url.path)):
                path = WEB_DIST / "index.html"
            if not path.is_file():
                return self.reply(404, {"error": "文件不存在；请先在 web 中执行 pnpm build"})
            body = path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", mimetypes.guess_type(path.name)[0] or "application/octet-stream")
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self'; img-src 'self' data:")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        params = {key: values[0] for key, values in parse_qs(url.query).items()}
        try:
            if url.path == "/api/runs":
                data = []
                for run in self.runs.values():
                    error = run["access_error"]
                    data.append({**{key: run[key] for key in ("id", "label", "harness", "writable", "mode", "coverage", "facts")},
                                 "access_error": error, "controllable": run["docker"] is not None,
                                 "read_check": "unavailable" if error else "saved-archive" if run["mode"] == "archive" else "not-read"})
            elif url.path == "/api/runtime":
                run = self.run_for(params.get("run"))
                if run["docker"] is None:
                    raise ValueError("此运行未登记物理运行控制")
                data = docker_runtime.status(run["docker"])
            elif url.path == "/api/items":
                run = self.run_for(params.get("run"))
                data = []
                if run["mode"] == "archive":
                    data = archive_reader(run).items()
                for kind in (() if run["mode"] == "archive" else ("issue", "pr")):
                    listed = braid_json(run, [kind, "list", "--state", "all", "--limit", "10000",
                                              "--json", "kind,id,number,title,state,assignees,revision"])
                    data.extend(listed)
            elif url.path == "/api/item":
                run = self.run_for(params.get("run"))
                kind = params.get("kind")
                if kind not in ("issue", "pr"):
                    raise ValueError("无效对象类型")
                item_id = int(params.get("id", ""))
                if item_id < 1:
                    raise ValueError("无效对象编号")
                data = item_view(run, kind, item_id)
            elif url.path == "/api/review":
                run = self.run_for(params.get("run"))
                pr, request = int(params.get("pr", "")), int(params.get("id", ""))
                if pr < 1 or request < 1:
                    raise ValueError("无效 PR 或审阅编号")
                if run["mode"] == "archive":
                    raise ValueError("此归档尚未保存可读取的审阅详情；不能从 PR 评论推断结论")
                data = braid_json(run, ["pr", "review", "view", str(pr), str(request), "--json"])
            elif url.path == "/api/comment":
                run = self.run_for(params.get("run"))
                comment_id = int(params.get("id", ""))
                if comment_id < 1:
                    raise ValueError("无效评论编号")
                command = ["comment", "view", str(comment_id), "--include-hidden", "--json"]
                if params.get("thread") == "1":
                    command.insert(3, "--thread")
                data = archive_reader(run).comment(comment_id, params.get("thread") == "1") if run["mode"] == "archive" else braid_json(run, command)
            elif url.path == "/api/sessions":
                data = session_inventory(self.run_for(params.get("run")))
            elif url.path == "/api/code/refs":
                data = code_files.refs(self.run_for(params.get("run")))
            elif url.path == "/api/code":
                run = self.run_for(params.get("run"))
                source = params.get("source")
                record = None
                if source == "workspace" and run["mode"] != "archive":
                    record = next((record for record in session_inventory(run)
                                   if record["record_id"] == params.get("provider")), None)
                    if record is None:
                        raise ValueError("CLI 未发现此 provider session 记录")
                data = code_files.read(run, source, params.get("path", ""), record=record, commit=params.get("commit"))
            elif url.path == "/api/transcript":
                run = self.run_for(params.get("run"))
                record = next((record for record in session_inventory(run)
                               if record["record_id"] == params.get("provider")), None)
                if record is None:
                    raise ValueError("CLI 未发现此 provider session 记录")
                if run["mode"] == "archive":
                    record = archive_reader(run).native_record(record)
                data = native_sessions.read_page(run, record, int(params.get("offset", "0")))
            else:
                return self.reply(404, {"error": "路由不存在"})
            self.reply(200, data)
        except (ValueError, RuntimeError, OSError, KeyError, archives.sqlite3.Error) as error:
            self.reply(400, {"error": str(error)})

    def do_POST(self):
        route = urlsplit(self.path).path
        if route not in ("/api/action", "/api/control"):
            return self.reply(404, {"error": "路由不存在"})
        origin = self.headers.get("Origin")
        host = self.headers.get("Host")
        if not host or (origin and origin != f"http://{host}"):
            return self.reply(403, {"error": "请求来源无效"})
        if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
            return self.reply(415, {"error": "需要 JSON 请求"})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length < 1 or length > MAX_POST:
                raise ValueError("请求正文大小无效")
            payload = json.loads(self.rfile.read(length))
            if not isinstance(payload, dict):
                raise ValueError("请求必须是对象")
            run = self.run_for(payload.get("run"))
            if run["mode"] == "archive":
                return self.reply(403, {"error": "归档仅供阅读，禁止人工修改和运行控制"})
            with run["operation_lock"]:
                if route == "/api/control":
                    self.control_run(run, payload)
                else:
                    self.change_item(run, payload)
        except RuntimeError as error:
            # A failed pre-write read has no mutation receipt to reconcile.
            self.reply(502, {"error": str(error)})
        except (ValueError, OSError, KeyError, json.JSONDecodeError) as error:
            self.reply(400, {"error": str(error)})

    def control_run(self, run, payload):
        action = payload.get("action")
        if action not in ("pause", "resume") or run["docker"] is None:
            raise ValueError("运行控制需要已登记容器及 pause/resume 操作")
        service.access({"service_id": run["service_id"]}, run)
        entry = {"at": datetime.now(timezone.utc).isoformat(), "run": run["id"],
                 "action": "runtime_" + action, "input": payload,
                 "container": run["docker"]["runtime_container"], "status": "started"}
        journal(self.journal_path, entry)
        try:
            result = docker_runtime.control(run["docker"], action)
        except docker_runtime.ControlError as error:
            journal(self.journal_path, {**entry, "status": "unconfirmed" if error.uncertain else "failed",
                                        "error": str(error)})
            detail = "\n控制结果未确认；刷新运行状态并查 journal，勿自动重试。" if error.uncertain else "\n未执行 Docker 暂停/恢复命令；请按读取到的实际状态处理。"
            return self.reply(502, {"error": str(error) + detail})
        try:
            journal(self.journal_path, {**entry, "status": "completed", "result": result})
        except OSError as error:
            return self.reply(502, {"error": f"运行控制已执行，但 journal 写入失败：{error}。先核对实际状态，勿重试。",
                                    "result": result})
        self.reply(200, result)

    def change_item(self, run, payload):
        if not run["writable"]:
            raise ValueError("此运行只读")
        command, body = action_command(payload)
        current = braid_json(run, [payload["kind"], "view", str(payload["id"]), "--json"])
        if payload["action"] == "edit" and current["revision"] != payload["revision"]:
            return self.reply(409, {"error": "对象已变化；刷新后检查草稿再提交"})
        comment_id = payload.get("comment") or payload.get("reply_to")
        if comment_id is not None and not any(int(c["database_id"]) == comment_id for c in current.get("comments", [])):
            raise ValueError("评论不属于当前对象")
        entry = {"at": datetime.now(timezone.utc).isoformat(), "run": run["id"],
                 "state": run["state"], "action": payload["action"], "kind": payload["kind"],
                 "id": payload["id"], "input": payload, "cli": command, "status": "started"}
        journal(self.journal_path, entry)
        try:
            stdout = braid(run, command, body, write=True)
        except RuntimeError as error:
            journal(self.journal_path, {**entry, "status": "unconfirmed", "error": str(error)})
            return self.reply(502, {"error": str(error) + "\n结果不确定；先刷新状态并查 journal，勿自动重试。"})
        try:
            journal(self.journal_path, {**entry, "status": "completed", "result": stdout})
        except OSError as error:
            return self.reply(502, {"error": f"CLI 已返回成功，但 journal 写入失败：{error}。请勿重试操作；先核对 Braid 状态。",
                                    "result": stdout})
        self.reply(200, {"result": stdout})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--service", required=True, type=Path, help="Factory26 Exp Console稳定服务目录")
    parser.add_argument("--port", type=int, default=8765)
    options = parser.parse_args()
    root = options.service.resolve(strict=True)
    record = service.read(root)
    if Path(__file__).resolve() != root / "app/server.py":
        raise ValueError("必须执行服务冻结app/server.py；请使用service.py serve")
    if Path(sys.executable).resolve() != Path(record["interpreter"]["executable"]):
        raise ValueError("请使用service.py serve启动登记Python")
    options.registry, options.journal = root / "manifest.json", root / record["journal"]
    logs = root / "logs"; logs.mkdir(parents=True, exist_ok=True)
    limits = record["access_log"]
    logger = logging.getLogger("console.access"); logger.setLevel(logging.INFO)
    handler = RotatingFileHandler(logs / "http.log", maxBytes=limits["max_bytes"], backupCount=limits["backups"], encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(message)s")); logger.addHandler(handler)
    with service.service_lock(root):
        record = service.read(root)
        Handler.runs = load_registry(options.registry)
        options.journal.parent.mkdir(parents=True, exist_ok=True)
        Handler.journal_path = options.journal
        server = ConsoleServer(("127.0.0.1", options.port), Handler)
        server.daemon_threads = False
        instance = {"phase": "running", "owner": "console", "pid": os.getpid(), "instance_id": str(uuid.uuid4()),
                    "service_id": record["service_id"], "port": server.server_port,
                    "started_at": service.stamp(), "host": service.socket.gethostname(),
                    "application": "app"}
        service.write_json(root / "active.json", instance)
        def terminate(*_):
            raise KeyboardInterrupt
        signal.signal(signal.SIGTERM, terminate)
        print(f"Console: http://127.0.0.1:{server.server_port} PID={os.getpid()}", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()
            service.write_json(root / "active.json", {**instance, "phase": "finished", "stopped_at": service.stamp(),
                                                      "references_released": False})
            handler.close()


if __name__ == "__main__":
    main()
