"""Read-only cross-chain navigation for one saved Factory run.

This module joins only fields that the run already persisted.  A text match is
kept as a candidate and is never promoted to an identity or causal link.
"""

import codecs
import json
from pathlib import Path
import sqlite3


MAX_MATCHES = 50
MAX_PREVIEW = 320


def _json(path, default):
    try:
        value = json.loads(path.read_text())
    except (OSError, ValueError):
        return default
    return value


def _relocate(run, value):
    if not isinstance(value, str) or not value:
        return None
    path = (run / value).resolve() if not Path(value).is_absolute() else Path(value)
    return str(path.relative_to(run)) if path.is_relative_to(run) else None


def _status(query, matches):
    unique = []
    seen = set()
    for match in matches:
        marker = json.dumps(match, ensure_ascii=False, sort_keys=True)
        if marker not in seen:
            seen.add(marker)
            unique.append(match)
    if len(unique) == 1:
        return {"query": query, "status": "exact", "matches": unique}
    return {"query": query, "status": "missing" if not unique else "ambiguous", "matches": unique}


def _work_item_query(value):
    text = str(value or "")
    if ":" in text:
        kind, number = text.split(":", 1)
        return kind, number
    return None, text


def _entry_identity(entry):
    return [value for value in (entry.get("native_id"), entry.get("native_session_id"), entry.get("session_id"))
            if isinstance(value, str) and value]


def _entry_for_session(entries, query):
    matches = [entry for entry in entries if query in _entry_identity(entry)]
    return matches


def _read_span(path, offset, size, record_end=None):
    if offset < 0 or size < 1:
        raise ValueError("offset must be nonnegative and bytes positive")
    if record_end is not None and offset > record_end:
        raise ValueError(f"record offset exceeds record boundary: {offset}>{record_end}")
    with path.open("rb") as stream:
        stream.seek(offset)
        limit = size if record_end is None else min(size, record_end - offset)
        content = stream.read(limit)
        decoder = codecs.getincrementaldecoder("utf-8")("replace")
        text = decoder.decode(content, final=False)
        pending = decoder.getstate()[0]
        while pending:
            if record_end is not None and stream.tell() >= record_end:
                text += decoder.decode(b"", final=True)
                break
            extra = stream.read(1)
            if not extra:
                text += decoder.decode(b"", final=True)
                break
            content += extra
            text += decoder.decode(extra, final=False)
            pending = decoder.getstate()[0]
        truncated = bool(record_end is None and stream.read(1)) or (record_end is not None and offset + len(content) < record_end)
    return {"offset": offset, "next_offset": offset + len(content), "bytes": len(content),
            "record_complete": record_end is None or offset + len(content) >= record_end,
            "truncated": truncated, "text": text}


def _record_text(value):
    if not isinstance(value, dict):
        return ""
    message = value.get("message") if value.get("type") == "message" else value.get("payload")
    if not isinstance(message, dict):
        return ""
    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(message.get("output"), str):
        return message["output"]
    if not isinstance(content, list):
        return ""
    chunks = []
    for block in content:
        if isinstance(block, dict) and isinstance(block.get("text"), str):
            chunks.append(block["text"])
        elif isinstance(block, dict) and isinstance(block.get("content"), str):
            chunks.append(block["content"])
    return "\n".join(chunks)


def _preview(value):
    text = " ".join(str(value or "").split())
    return text[:MAX_PREVIEW] + ("…" if len(text) > MAX_PREVIEW else "")


def _native_records(run, entry, *, record=None, tool_call=None, text=None):
    relative = entry.get("native")
    if not isinstance(relative, str):
        return [], ["native archive missing"]
    path = (run / relative).resolve()
    if not path.is_file() or not path.is_relative_to(run):
        return [], [f"native archive unavailable: {relative}"]
    found, warnings = [], []
    try:
        with path.open("rb") as stream:
            line_number = 0
            while True:
                offset = stream.tell()
                raw = stream.readline()
                if not raw:
                    break
                line_number += 1
                try:
                    value = json.loads(raw)
                except ValueError:
                    warnings.append(f"{relative}:{line_number}: invalid JSON")
                    continue
                if not isinstance(value, dict):
                    continue
                identity = value.get("id")
                message = value.get("message") if value.get("type") == "message" else value.get("payload")
                role = message.get("role") if isinstance(message, dict) else None
                record_hit = record is not None and identity == record
                raw_text = _record_text(value)
                text_hit = text is not None and text.casefold() in raw.decode("utf-8", "replace").casefold()
                calls = []
                content = message.get("content") if isinstance(message, dict) else None
                if isinstance(content, list):
                    calls.extend(block for block in content if isinstance(block, dict) and
                                 block.get("type") == "toolCall")
                if isinstance(value.get("payload"), dict) and value["payload"].get("type") == "function_call":
                    calls.append(value["payload"])
                call_hit = tool_call is not None and any(block.get("id", block.get("call_id")) == tool_call for block in calls)
                response_hit = isinstance(message, dict) and (
                    (message.get("role") == "toolResult" and message.get("toolCallId") == tool_call) or
                    (message.get("type") == "function_call_output" and message.get("call_id") == tool_call))
                if not (record_hit or text_hit or call_hit or response_hit):
                    continue
                match_kind = "call" if call_hit and not response_hit else "result" if response_hit else None
                found.append({"record_id": identity, "type": value.get("type"), "role": role,
                              "timestamp": value.get("timestamp"), "line": line_number,
                              "offset": offset, "next_offset": offset + len(raw),
                              "source": relative, "preview": _preview(raw_text),
                              "match_type": "text_candidate" if text_hit and not (record_hit or call_hit or response_hit) else "exact_identity",
                              "tool_match": match_kind})
    except OSError as exc:
        warnings.append(f"{relative}: {exc}")
    return found, warnings


def _timing(run, session_ids=None, pid=None):
    path = run / "pi-timing.jsonl"
    if not path.is_file():
        return {"status": "missing", "source": None, "matches": []}
    ids = set(session_ids or ())
    rows = []
    warnings = []
    try:
        for line_number, line in enumerate(path.read_text().splitlines(), 1):
            try:
                value = json.loads(line)
            except ValueError:
                warnings.append(f"pi-timing.jsonl:{line_number}: invalid JSON")
                continue
            if ids and value.get("session_id") not in ids:
                continue
            if pid is not None and value.get("pid") != pid:
                continue
            if ids or pid is not None:
                value = {key: value.get(key) for key in
                         ("kind", "at_ms", "instance_id", "pid", "session_id", "request_id",
                          "tool_call_id", "tool_name", "is_error", "status", "source_path")}
                value["line"] = line_number
                rows.append(value)
    except OSError as exc:
        warnings.append(str(exc))
    return {"status": "available" if rows else ("missing" if not warnings else "unavailable"),
            "source": "pi-timing.jsonl", "matches": rows[:MAX_MATCHES],
            "match_count": len(rows), "truncated": len(rows) > MAX_MATCHES, "warnings": warnings}


def _git(run, work_item=None, commit=None, tree=None):
    path = run / "braid-state/braid.sqlite3"
    result = {"status": "missing", "source": str(path.relative_to(run)) if path.is_file() else None,
              "worktrees": [], "merges": [], "commits": [], "trees": [], "warnings": []}
    if not path.is_file():
        return result
    try:
        with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as db:
            db.row_factory = sqlite3.Row
            if work_item:
                node = f"{work_item[0]}:{work_item[1]}"
                result["worktrees"] = [dict(row) for row in db.execute(
                    "select w.* from worktrees w join agent_instances a on a.agent_id=w.agent_id "
                    "join assignments x on x.assignment_id=a.assignment_id where x.work_item_node_id=?",
                    (node,)).fetchall()]
                result["merges"] = [dict(row) for row in db.execute(
                    "select * from local_merges where writer_node=? or pr_node_id in "
                    "(select pr_node_id from associations where issue_node_id=?)", (node, node)).fetchall()]
            if commit:
                for field in ("base_commit", "head_commit", "merge_commit"):
                    result["commits"].extend(dict(row) for row in db.execute(
                        f"select pr_node_id, {field} as value, base_ref, head_ref, lifecycle from local_merges where {field}=?",
                        (commit,)).fetchall())
                result["commits"].extend(dict(row) for row in db.execute(
                    "select node_id, work_item_node_id, object_kind, version, digest, lifecycle from canonical_objects where version=? or digest=?",
                    (commit, commit)).fetchall())
            if tree:
                for field in ("base_ref", "head_ref"):
                    result["trees"].extend(dict(row) for row in db.execute(
                        f"select pr_node_id, {field} as value, base_commit, head_commit, merge_commit from local_merges where {field}=?",
                        (tree,)).fetchall())
            result["status"] = "available"
    except sqlite3.Error as exc:
        result["status"] = "unavailable"
        result["warnings"].append(str(exc))
    if commit is not None:
        result["commit_query"] = _status(commit, [{"value": commit}] if result["commits"] else [])
    if tree is not None:
        result["tree_query"] = _status(tree, [{"value": tree}] if result["trees"] else [])
    return result


def _tree(run, entry):
    relative = entry.get("session_tree_manifest")
    if not relative:
        return {"status": "missing", "source": None, "parent": None, "children": []}
    path = (run / relative).resolve()
    value = _json(path, None)
    if not isinstance(value, dict):
        return {"status": "unavailable", "source": relative, "parent": None, "children": []}
    parent = value.get("parent_native_session_id")
    self_ids = set(_entry_identity(entry))
    parent_source = value.get("parent_session_file")
    parent_local = None
    if isinstance(parent_source, str):
        base = Path(parent_source).name
        parent_local = next((str(path.relative_to(run)) for path in (run / "native").glob("*.jsonl")
                             if path.name.endswith(base)), None)
    return {"status": "available", "source": relative,
            "parent": parent, "parent_relation": "self" if parent in self_ids else "recorded_parent" if parent else "missing",
            "parent_source": parent_source, "parent_local": parent_local,
            "children": value.get("children") if isinstance(value.get("children"), list) else [],
            "diagnostic_status": value.get("diagnostic_status")}


def trace(run, *, work_item=None, session=None, pid=None, commit=None, tree=None,
          text=None, record=None, tool_call=None, offset=0, size=4096):
    if offset < 0:
        raise ValueError("record offset must be nonnegative")
    run = Path(run).expanduser().resolve(strict=True)
    manifest_path = run / "native/manifest.json"
    manifest = _json(manifest_path, {})
    entries = manifest.get("sessions") if isinstance(manifest, dict) else None
    if not isinstance(entries, list):
        raise ValueError("native/manifest.json has no sessions array")
    entries = [entry for entry in entries if isinstance(entry, dict)]
    kind, number = _work_item_query(work_item) if work_item is not None else (None, None)
    item_matches = [entry for entry in entries if number is not None and str(entry.get("work_item_id")) == number and
                    (kind is None or entry.get("work_item_kind") == kind)]
    if work_item is not None and kind is None and len({entry.get("work_item_kind") for entry in item_matches}) > 1:
        item_identity = _status(work_item, [{"kind": e.get("work_item_kind"), "number": e.get("work_item_id")} for e in item_matches])
        item_identity["member_count"] = len(item_matches)
        selected = []
    else:
        item_identity = _status(work_item, [{"kind": e.get("work_item_kind"), "number": e.get("work_item_id")} for e in item_matches]) if work_item is not None else None
        if item_identity is not None:
            item_identity["member_count"] = len(item_matches)
        selected = item_matches
    session_matches = _entry_for_session(entries, session) if session is not None else []
    session_identity = _status(session, [{"native_id": e.get("native_id"), "work_item_id": e.get("work_item_id")} for e in session_matches]) if session is not None else None
    if session is not None and len(session_matches) == 1:
        selected = [session_matches[0]]
    elif session is not None:
        selected = []
    selected = list(dict.fromkeys(id(entry) for entry in selected))
    selected_entries = [entry for entry in entries if id(entry) in selected]
    selected_ids = {identity for entry in selected_entries for identity in _entry_identity(entry)}
    output = {"run": str(run), "source": {"manifest": "native/manifest.json"},
              "identity": {"work_item": item_identity, "session": session_identity},
              "sessions": [], "timing": _timing(run, selected_ids if selected_entries else None, pid),
              "git": _git(run, (kind, number) if work_item is not None and kind else None, commit, tree),
              "text_candidates": [], "warnings": []}
    for entry in selected_entries:
        item = {key: entry.get(key) for key in
                ("native_id", "native_session_id", "profile_id", "work_item_id", "work_item_kind",
                 "group_id", "assignment_generation", "status", "native", "worktree", "context_path",
                 "instructions_path", "turns", "source_path", "native_session_path")}
        item["native"] = _relocate(run, entry.get("native"))
        item["context_path"] = _relocate(run, entry.get("context_path"))
        item["instructions_path"] = _relocate(run, entry.get("instructions_path"))
        item["turns"] = [{key: turn.get(key) for key in ("braid_turn_id", "provider_turn_id", "status", "input_path")}
                          for turn in entry.get("turns", []) if isinstance(turn, dict)]
        for turn in item["turns"]:
            turn["input_path"] = _relocate(run, turn.get("input_path"))
        item["session_tree"] = _tree(run, entry)
        records, warnings = _native_records(run, entry, record=record, tool_call=tool_call, text=text)
        item["records"] = records[:MAX_MATCHES] if record or tool_call else []
        output["text_candidates"].extend(row for row in records if row.get("match_type") == "text_candidate")
        output["warnings"].extend(warnings)
        output["sessions"].append(item)
    candidate_count = len(output["text_candidates"])
    output["text_candidates"] = output["text_candidates"][:MAX_MATCHES]
    output["text_candidates_truncated"] = candidate_count > MAX_MATCHES
    if text is not None and not selected_entries:
        output["warnings"].append("text query has no exact session/work-item scope; pass --session or --work-item")
    if (record or tool_call) and len(output["sessions"]) == 1:
        records = output["sessions"][0]["records"]
        if tool_call:
            identity_matches = [{"record_id": r.get("record_id"), "line": r.get("line"),
                                 "role": r.get("role")} for r in records]
            output["record_identity"] = _status(tool_call, identity_matches)
            if (len(identity_matches) == 2 and
                    sum(row.get("tool_match") == "call" for row in records) == 1 and
                    sum(row.get("tool_match") == "result" for row in records) == 1):
                output["record_identity"]["status"] = "exact_pair"
        elif record:
            output["record_identity"] = _status(record, [{"record_id": r.get("record_id"), "line": r.get("line")} for r in records])
        exact = [r for r in records if r.get("match_type") == "exact_identity"]
        reads = []
        read_items = exact if tool_call else exact if len(exact) == 1 else []
        for item in read_items:
            source = run / item["source"]
            read = _read_span(source, item["offset"] + offset, size, item["next_offset"])
            read.update({"record_id": item["record_id"], "role": item.get("role"),
                         "source": item["source"], "line": item["line"],
                         "next_line": item["line"] + read["text"].count("\n"),
                         "record_end_offset": item["next_offset"],
                         "record_offset": item["offset"],
                         "next_record_offset": read["next_offset"] - item["offset"]})
            reads.append(read)
        if reads:
            if tool_call:
                output["reads"] = reads
            else:
                output["read"] = reads[0]
    return output
