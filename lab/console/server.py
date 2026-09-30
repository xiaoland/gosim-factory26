#!/usr/bin/env python3
"""Local, live Braid collaboration console. Writes only through the Braid CLI."""

import argparse
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import subprocess
import threading
from urllib.parse import parse_qs, urlsplit

try:
    from markdown_it import MarkdownIt
except ImportError:
    MARKDOWN = None
else:
    MARKDOWN = MarkdownIt("commonmark", {"html": False, "linkify": False}).enable("table").disable("image")


PAGE = Path(__file__).with_name("index.html")
JOURNAL_LOCK = threading.Lock()
MAX_POST = 1_000_000


def load_registry(path):
    data = json.loads(path.read_text())
    if not isinstance(data, list) or not data:
        raise ValueError("registry 必须是非空运行列表")
    runs = {}
    for entry in data:
        if not isinstance(entry, dict) or not isinstance(entry.get("id"), str):
            raise ValueError("每个运行需要 id")
        if entry["id"] in runs or not entry["id"]:
            raise ValueError("运行 id 不得为空或重复")
        if entry.get("kind") not in ("i11", "i12") or type(entry.get("writable")) is not bool:
            raise ValueError(f'{entry["id"]}: kind/writable 无效')
        if entry["writable"] != (entry["kind"] == "i12"):
            raise ValueError(f'{entry["id"]}: 仅 I12 可写')
        state, binary = Path(entry["state"]), Path(entry["binary"])
        if not state.is_absolute() or not (state / "braid.sqlite3").is_file():
            raise ValueError(f'{entry["id"]}: state 需为现存绝对路径')
        if not binary.is_absolute() or not binary.is_file() or not os.access(binary, os.X_OK):
            raise ValueError(f'{entry["id"]}: binary 需为可执行绝对路径')
        runs[entry["id"]] = {"id": entry["id"], "label": str(entry.get("label") or entry["id"]),
                             "kind": entry["kind"], "writable": entry["writable"],
                             "state": str(state), "binary": str(binary)}
    return runs


def braid(run, args, body=None, *, write=False):
    command = [run["binary"], "--state", run["state"]]
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


def add_html(record):
    if MARKDOWN is not None and isinstance(record.get("body"), str):
        record["body_html"] = MARKDOWN.render(record["body"])
    return record


def item_view(run, kind, item_id):
    item = add_html(braid_json(run, [kind, "view", str(item_id), "--json"]))
    for comment in item.get("comments", []):
        add_html(comment)
    return item


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


class Handler(BaseHTTPRequestHandler):
    runs = {}
    journal_path = None

    def reply(self, status, data):
        encoded = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; connect-src 'self'; img-src 'none'")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def run_for(self, value):
        try:
            return self.runs[value]
        except KeyError as error:
            raise ValueError("未登记的运行") from error

    def do_GET(self):
        url = urlsplit(self.path)
        if url.path == "/":
            body = PAGE.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; connect-src 'self'; img-src 'none'")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        params = {key: values[0] for key, values in parse_qs(url.query).items()}
        try:
            if url.path == "/api/runs":
                data = [{key: run[key] for key in ("id", "label", "kind", "writable")}
                        for run in self.runs.values()]
            elif url.path == "/api/items":
                run = self.run_for(params.get("run"))
                data = []
                for kind in ("issue", "pr"):
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
            elif url.path == "/api/comment":
                run = self.run_for(params.get("run"))
                comment_id = int(params.get("id", ""))
                if comment_id < 1:
                    raise ValueError("无效评论编号")
                command = ["comment", "view", str(comment_id), "--include-hidden", "--json"]
                if params.get("thread") == "1":
                    command.insert(3, "--thread")
                data = [add_html(comment) for comment in braid_json(run, command)]
            else:
                return self.reply(404, {"error": "路由不存在"})
            self.reply(200, data)
        except (ValueError, RuntimeError, OSError, KeyError, json.JSONDecodeError) as error:
            self.reply(400, {"error": str(error)})

    def do_POST(self):
        if urlsplit(self.path).path != "/api/action":
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
        except (ValueError, OSError, KeyError, json.JSONDecodeError) as error:
            self.reply(400, {"error": str(error)})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--journal", type=Path, required=True)
    parser.add_argument("--port", type=int, default=8765)
    options = parser.parse_args()
    Handler.runs = load_registry(options.registry)
    options.journal.parent.mkdir(parents=True, exist_ok=True)
    Handler.journal_path = options.journal
    server = ThreadingHTTPServer(("127.0.0.1", options.port), Handler)
    print(f"人工介入实验 console: http://127.0.0.1:{server.server_port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
