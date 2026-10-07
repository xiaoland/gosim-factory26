"""Read saved Braid objects without opening its writable CLI or original Git paths."""

import hashlib
import json
from pathlib import Path
import sqlite3


def identity(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def within(root, relative):
    path = Path(relative)
    if path.is_absolute() or not path.parts or ".." in path.parts:
        raise ValueError(f"归档路径必须是安全相对路径：{relative}")
    result = (root / path).resolve(strict=True)
    if not result.is_relative_to(root):
        raise ValueError(f"归档路径越界：{relative}")
    return result


class Archive:
    def __init__(self, root, expected=None):
        self.root = Path(root).resolve(strict=True)
        self.database = within(self.root, "braid-state/braid.sqlite3")
        wal = Path(str(self.database) + "-wal")
        if wal.exists() and wal.stat().st_size:
            raise ValueError("归档数据库仍有非空 WAL；需要生产者保存完整冻结数据库，Console 不合并或修复")
        self.files = {"braid-state/braid.sqlite3": identity(self.database)}
        self.coverage = ["仅展示保存的对象与关系，不重新计算 Git 分支、合并条件或当前运行状态。"]
        with self.connect() as connection:
            self.columns = {row[0]: {column[1] for column in connection.execute(f'PRAGMA table_info("{row[0]}")')}
                            for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            for table, fields in {"work_items": {"node_id", "kind", "number", "state"},
                                  "local_items": {"node_id", "title", "body", "revision"},
                                  "local_comments": {"comment_id", "work_item_node_id", "body", "lifecycle", "writer_group", "created_at", "updated_at"}}.items():
                if not fields <= self.columns.get(table, set()):
                    raise ValueError(f"不支持此归档对象 schema：{table} 缺少 {sorted(fields - self.columns.get(table, set()))}")
            if "parent_issue" not in self.columns["local_items"]:
                self.coverage.append("此历史 schema 未保存父子 Issue 关系。")
            if "desired_member_login" not in self.columns["local_items"]:
                self.coverage.append("此历史 schema 未保存当前成员身份；空负责人不证明当时无人负责。")
            if "thread_root" not in self.columns["local_comments"]:
                self.coverage.append("此历史 schema 未保存讨论串关系及解决范围。")
        self.records = self.read_sessions()
        self.manifest = self.read_manifest()
        for record in self.records:
            matches = [row for row in self.manifest if row.get("provider") == record.get("provider")
                       and row.get("group_id") == record.get("group_id")
                       and row.get("session_id") == record.get("session_id")]
            record["archive_native_error"] = "native manifest 未提供此会话的唯一正文映射"
            if len(matches) == 1:
                row = matches[0]
                if row.get("native") and row.get("native_id") and row.get("sha256"):
                    try:
                        if (row.get("work_item_id") != record.get("work_item_id") or
                                row.get("work_item_kind") != record.get("work_item_kind") or
                                row.get("source_path") != record.get("native_session_path")):
                            raise ValueError("manifest 与保存会话的工作项或原文身份不一致")
                        native = within(self.root, row["native"])
                        if not native.is_relative_to(self.root / "native"):
                            raise ValueError("manifest 原文不在归档 native 目录内")
                        self.files[row["native"]] = identity(native)
                        if self.files[row["native"]] != row["sha256"]:
                            raise ValueError(f"归档原文 SHA-256 不匹配：{row['native']}")
                        record.update(native_session_path=str(native), native_session_id=row["native_id"],
                                      archive_native_error=None, archive_native=row["native"])
                    except (OSError, ValueError) as error:
                        record["archive_native_error"] = f"{type(error).__name__}: {error}"
        if expected is not None and self.files != expected:
            raise ValueError("归档保存文件身份已改变；保留旧配置并重新核对来源，不隐式接纳新内容")

    def connect(self):
        # immutable prevents SQLite from creating or modifying WAL/SHM sidecars.
        if identity(self.database) != self.files["braid-state/braid.sqlite3"]:
            raise ValueError("归档数据库身份已改变")
        connection = sqlite3.connect(self.database.as_uri() + "?mode=ro&immutable=1", uri=True)
        connection.row_factory = sqlite3.Row
        return connection

    def read_json(self, relative):
        path = within(self.root, relative)
        self.files[relative] = identity(path)
        return json.loads(path.read_text())

    def read_sessions(self):
        relative = "braid-state/sessions.json"
        if (self.root / relative).is_file():
            rows = self.read_json(relative)
            if (self.root / "braid-state/status.json").is_file():
                if self.read_json("braid-state/status.json").get("physical_sessions") != rows:
                    self.coverage.append("保存的 sessions 与 status 会话目录不同；仅展示 sessions，不静默合并。")
        elif (self.root / "braid-state/status.json").is_file():
            rows = self.read_json("braid-state/status.json").get("physical_sessions")
        else:
            self.coverage.append("缺少保存的 sessions.json/status.json；会话目录不可用。")
            return []
        if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
            raise ValueError("归档保存会话目录格式不支持")
        seen = set()
        with self.connect() as connection:
            for row in rows:
                context = row.get("context_path")
                if not isinstance(context, str) or not context:
                    raise ValueError("归档会话缺少保存的 context_path 身份")
                row["record_id"] = Path(context).parent.name
                if row["record_id"] in seen:
                    raise ValueError("归档 physical 记录身份重复")
                seen.add(row["record_id"])
                if not row.get("profile_id") and {"agent_id", "profile_id"} <= self.columns.get("agent_instances", set()):
                    profiles = connection.execute("SELECT profile_id FROM agent_instances WHERE agent_id=?", (row.get("group_id"),)).fetchall()
                    if len(profiles) == 1:
                        row["profile_id"] = profiles[0][0]
                row.setdefault("profile_id", "未保存")
                row["source_mode"] = "archive"
        self.coverage.append("会话目录来自保存的 physical 枚举，不证明缺失材料的会话也已列出。")
        return rows

    def read_manifest(self):
        if not (self.root / "native/manifest.json").is_file():
            self.coverage.append("缺少 native/manifest.json；保留会话目录，但不能定位原生正文。")
            return []
        data = self.read_json("native/manifest.json")
        if (data.get("schema_version") != 1 or not isinstance(data.get("sessions"), list)
                or not all(isinstance(row, dict) for row in data["sessions"])):
            self.coverage.append("不支持此 native manifest schema；正文定位不可用。")
            return []
        return data["sessions"]

    def member(self, connection, raw):
        if raw in (None, "external", "Braid"):
            return raw or "external"
        if "member_login" in self.columns.get("assignments", set()):
            row = connection.execute("SELECT a.member_login FROM agent_instances ai JOIN assignments a ON a.assignment_id=ai.assignment_id WHERE ai.agent_id=?", (raw,)).fetchone()
            if row and row[0]:
                return row[0]
        return f"历史成员 {raw}"

    def items(self):
        with self.connect() as connection:
            rows = connection.execute("SELECT w.kind,w.number,w.state,l.* FROM work_items w JOIN local_items l USING(node_id) WHERE w.kind IN ('issue','pr') ORDER BY w.number").fetchall()
            return [{key: item[key] for key in ("kind", "id", "number", "title", "state", "assignees", "revision")}
                    for row in rows for item in [self.item_row(connection, row)]]

    def item_row(self, connection, row):
        row = dict(row)
        member = row.get("desired_member_login")
        return {**{key: row[key] for key in ("node_id", "kind", "number", "state", "title", "body", "revision")},
                "id": row["number"], "assignees": [{"login": member}] if member else [],
                "parent_node": row.get("parent_issue"), "head_ref": row.get("head_ref"), "base_ref": row.get("base_ref"),
                "reason": row.get("state_reason"), "draft": bool(row["draft"]) if "draft" in row else None}

    def comments(self, connection, target, *, include_hidden=False):
        rows = [dict(row) for row in connection.execute("SELECT * FROM local_comments WHERE work_item_node_id=? ORDER BY comment_id", (target,))]
        roots = {row["comment_id"]: row for row in rows}
        hidden_ancestors = {}
        result = []
        for row in rows:
            root = row.get("thread_root", row["comment_id"])
            cutoff = roots.get(root, {}).get("resolved_through")
            folded = cutoff is not None and row["comment_id"] <= cutoff
            parent = roots.get(row.get("reply_to"))
            hidden_by = parent["comment_id"] if parent and parent["lifecycle"] == "hidden" else hidden_ancestors.get(row.get("reply_to"))
            hidden_ancestors[row["comment_id"]] = hidden_by
            visible = row["lifecycle"] == "visible" and hidden_by is None and not folded
            result.append({"database_id": str(row["comment_id"]),
                           "author": {"login": self.member(connection, row.get("system_author") or row["writer_group"])},
                           "body": row["body"] if row["lifecycle"] != "deleted" and (visible or include_hidden) else None,
                           "created_at": row["created_at"], "updated_at": row["updated_at"] if visible or include_hidden else row["created_at"],
                           "reply_to": row.get("reply_to"), "thread_root": root,
                           "resolved": cutoff is not None, "folded": folded,
                           "minimized": row["lifecycle"] == "hidden", "minimized_reason": row.get("hide_reason"),
                           "hidden_by": hidden_by, "hidden_by_reason": roots[hidden_by].get("hide_reason") if hidden_by is not None else None,
                           "deleted": row["lifecycle"] == "deleted", "lifecycle": row["lifecycle"]})
        return result

    def item(self, kind, item_id):
        with self.connect() as connection:
            row = connection.execute("SELECT w.kind,w.number,w.state,l.* FROM work_items w JOIN local_items l USING(node_id) WHERE w.kind=? AND w.number=?", (kind, item_id)).fetchone()
            if row is None:
                raise ValueError("归档未保存此对象")
            item = self.item_row(connection, row)
            item["comments"] = self.comments(connection, row["node_id"])
            by_node = {value["node_id"]: value for saved in connection.execute("SELECT w.kind,w.number,w.state,l.* FROM work_items w JOIN local_items l USING(node_id)")
                       for value in [self.item_row(connection, saved)]}
            reference = lambda node: {key: by_node[node][key] for key in ("kind", "number", "title", "state")}
            if "parent_issue" in row.keys():
                item["parent_issue"] = reference(row["parent_issue"]) if row["parent_issue"] in by_node else None
                item["sub_issues"] = [reference(value["node_id"]) for value in by_node.values() if value.get("parent_node") == row["node_id"]]
            if {"issue_node_id", "pr_node_id", "active"} <= self.columns.get("associations", set()):
                own, other, field = (("issue_node_id", "pr_node_id", "associated_prs") if kind == "issue" else ("pr_node_id", "issue_node_id", "associated_issues"))
                item[field] = [reference(value[0]) for value in connection.execute(f"SELECT {other} FROM associations WHERE {own}=? AND active=1", (row["node_id"],)) if value[0] in by_node]
            return {key: value for key, value in item.items() if key not in ("node_id", "parent_node")}

    def comment(self, comment_id, thread):
        with self.connect() as connection:
            row = connection.execute("SELECT * FROM local_comments WHERE comment_id=?", (comment_id,)).fetchone()
            if row is None:
                raise ValueError("归档未保存此评论")
            root = row["thread_root"] if "thread_root" in row.keys() else comment_id
            return [value for value in self.comments(connection, row["work_item_node_id"], include_hidden=True)
                    if value["thread_root"] == root and (thread or int(value["database_id"]) == comment_id)]

    def native_record(self, record):
        if record.get("archive_native_error"):
            raise ValueError(record["archive_native_error"] + "；不会回退原工作树或容器")
        path = within(self.root, record["archive_native"])
        if identity(path) != self.files[record["archive_native"]]:
            raise ValueError("归档原生正文身份已改变")
        return record
