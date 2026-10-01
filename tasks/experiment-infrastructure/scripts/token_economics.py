"""Read-only Pi usage ledger for a Factory generation directory or workspace ZIP.

Counts assistant messages once by (native session ID, message ID), including
native child sessions. It never treats absent usage as zero or counts replayed
copies of a generation as another run.
"""

import argparse
from collections import defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import zipfile

FIELDS = ("input", "output", "cacheRead", "cacheWrite")
UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.I)


def time_ms(value):
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        return int(datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp() * 1000)
    return None


def sources(path):
    if path.suffix == ".zip":
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            session_name = next((n for n in names if n.endswith("/braid-state/sessions.json")), None)
            sessions = json.loads(archive.read(session_name)) if session_name else []
            for name in names:
                if "/work/native-homes/" not in name or not name.endswith(".jsonl") or "/subagent-artifacts/" in name:
                    continue
                with archive.open(name) as stream:
                    yield name, stream, sessions
    else:
        session_file = path / "braid-state/sessions.json"
        sessions = json.loads(session_file.read_text()) if session_file.is_file() else []
        for file in (path / "work/native-homes").rglob("*.jsonl"):
            if "subagent-artifacts" in file.parts:
                continue
            with file.open("rb") as stream:
                yield str(file.relative_to(path)), stream, sessions


def report(path, since, until, bucket_minutes):
    parent = {}
    records = {}
    invalid = 0
    duplicates = 0
    conflicting = 0
    session_files = set()
    for name, stream, sessions in sources(path):
        if not parent:
            parent = {row["native_session_id"]: row for row in sessions if row.get("native_session_id")}
        session_files.add(name)
        session_id = None
        match = UUID.search(Path(name).stem)
        if match:
            session_id = match.group()
        child_path = "/run-" in name
        for line_no, raw in enumerate(stream, 1):
            try:
                entry = json.loads(raw)
            except (ValueError, UnicodeDecodeError):
                invalid += 1
                continue
            if entry.get("type") == "session":
                session_id = entry.get("id") or entry.get("sessionId") or session_id
                continue
            msg = entry.get("message") if entry.get("type") == "message" else None
            if not isinstance(msg, dict) or msg.get("role") != "assistant" or not session_id:
                continue
            at = time_ms(msg.get("timestamp") or entry.get("timestamp"))
            if at is None or (since is not None and at < since) or (until is not None and at >= until):
                continue
            message_id = entry.get("id")
            if not message_id:
                invalid += 1
                continue
            usage = msg.get("usage") if isinstance(msg.get("usage"), dict) else {}
            tokens = {field: usage.get(field) if isinstance(usage.get(field), (int, float)) and not isinstance(usage.get(field), bool) else None for field in FIELDS}
            key = (session_id, message_id)
            row = {"session": session_id, "message": message_id, "at": at,
                   "model": msg.get("model") or "unknown", "provider": msg.get("provider") or "unknown",
                   "kind": "braid_member" if session_id in parent else "pi_subagent" if child_path else "unmapped",
                   "work_item": (parent.get(session_id) or {}).get("work_item_kind", "") + ":" + str((parent.get(session_id) or {}).get("work_item_id", "")) if session_id in parent else None,
                   "profile": (parent.get(session_id) or {}).get("profile_id"),
                   "error": msg.get("stopReason") == "error" or bool(msg.get("errorMessage")),
                   "tokens": tokens, "source": name}
            old = records.get(key)
            if old:
                duplicates += 1
                if old["tokens"] != tokens:
                    conflicting += 1
                    if sum(v is not None for v in tokens.values()) > sum(v is not None for v in old["tokens"].values()):
                        records[key] = row
            else:
                records[key] = row

    groups = defaultdict(lambda: {"assistant_messages": 0, "errors": 0, "known": {f: 0 for f in FIELDS}, "tokens": {f: 0 for f in FIELDS}, "maximum_message_tokens": {f: 0 for f in FIELDS}, "sessions": set()})
    buckets = defaultdict(lambda: {"assistant_messages": 0, "tokens": {f: 0 for f in FIELDS}})
    items = defaultdict(lambda: {"assistant_messages": 0, "tokens": {f: 0 for f in FIELDS}, "sessions": set()})
    for row in records.values():
        label = (row["kind"], row["model"], row["provider"])
        group = groups[label]
        group["assistant_messages"] += 1
        group["errors"] += row["error"]
        group["sessions"].add(row["session"])
        minute = row["at"] // (bucket_minutes * 60_000) * bucket_minutes * 60_000
        bucket = buckets[(minute, row["work_item"] or row["kind"])]
        bucket["assistant_messages"] += 1
        item = items[row["work_item"] or row["kind"]]
        item["assistant_messages"] += 1
        item["sessions"].add(row["session"])
        for field, amount in row["tokens"].items():
            if amount is not None:
                group["known"][field] += 1
                group["tokens"][field] += amount
                group["maximum_message_tokens"][field] = max(group["maximum_message_tokens"][field], amount)
                bucket["tokens"][field] += amount
                item["tokens"][field] += amount

    request_starts = None
    timing_file = path / "pi-timing.jsonl" if path.is_dir() else None
    if timing_file and timing_file.is_file():
        requests = {}
        for raw in timing_file.open():
            try:
                event = json.loads(raw)
            except ValueError:
                invalid += 1
                continue
            at = time_ms(event.get("at_ms"))
            request_id = event.get("request_id")
            if event.get("kind") != "request_start" or not request_id or at is None or (since is not None and at < since) or (until is not None and at >= until):
                continue
            requests[request_id] = event
        request_starts = []
        by_request_group = defaultdict(int)
        for event in requests.values():
            session_id = event.get("session_id")
            kind = "braid_member" if session_id in parent else "other_or_child"
            by_request_group[(kind, event.get("model") or "unknown", event.get("provider") or "unknown")] += 1
        for (kind, model, provider), count in sorted(by_request_group.items()):
            request_starts.append({"kind": kind, "model": model, "provider": provider, "count": count})

    def token_volume(row):
        return sum(row["tokens"].values())

    return {
        "source": str(path), "since": since, "until": until,
        "sessions_in_braid_index": len(parent),
        "physical_sessions_observed": len({r["session"] for r in records.values()}),
        "native_files": len(session_files), "messages": len(records),
        "duplicate_copies_skipped": duplicates, "conflicting_duplicates": conflicting,
        "invalid_or_unkeyed_lines": invalid,
        "request_starts_from_timing": request_starts,
        "groups": [{"kind": kind, "model": model, "provider": provider,
                    **{k: v for k, v in value.items() if k != "sessions"}, "sessions": len(value["sessions"])}
                   for (kind, model, provider), value in sorted(groups.items())],
        "top_items": [{"item": key, "assistant_messages": value["assistant_messages"], "sessions": len(value["sessions"]), "tokens": value["tokens"]}
                      for key, value in sorted(items.items(), key=lambda item: token_volume(item[1]), reverse=True)[:15]],
        "top_buckets": [{"start_utc": datetime.fromtimestamp(at / 1000, timezone.utc).isoformat(), "item": item, **value}
                        for (at, item), value in sorted(buckets.items(), key=lambda item: token_volume(item[1]), reverse=True)[:15]],
        "top_messages": [{k: v for k, v in row.items() if k not in ("source", "message")} | {"source": row["source"]}
                         for row in sorted(records.values(), key=token_volume, reverse=True)[:15]],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--since", help="inclusive ISO UTC timestamp")
    parser.add_argument("--until", help="exclusive ISO UTC timestamp")
    parser.add_argument("--bucket-minutes", type=int, default=15)
    args = parser.parse_args()
    if args.bucket_minutes <= 0:
        parser.error("--bucket-minutes must be positive")
    print(json.dumps(report(args.source, time_ms(args.since), time_ms(args.until), args.bucket_minutes), ensure_ascii=False))


if __name__ == "__main__":
    main()
