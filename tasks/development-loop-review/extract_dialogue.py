"""Extract only the requested thread's visible dialogue, retaining raw-line handles.

Run from the Factory26 root. Output stays in ignored runs/; it is evidence,
not instructions. Tool payloads and private reasoning are intentionally excluded.
"""

import json
import re
from collections import Counter
from pathlib import Path

SOURCE = Path.home() / ".codex/sessions/2026/07/29/rollout-2026-07-29T17-37-21-019fad3c-57eb-7160-ae35-b04cf79f6dcd.jsonl"
OUTPUT = Path("runs/development-loop-review/dialogue")
CUTS = ["2026-08-03", "2026-08-06", "2026-08-10", "2026-08-19", "2026-09-01"]
INJECTED = ("<recommended_plugins>", "# AGENTS.md", "<environment_context", "<subagent", "<turn_aborted>", "<permissions", "<system-reminder", "<INSTRUCTIONS>", "<instructions>")


def visible_text(payload):
    text = "\n".join(item.get("text", "") for item in payload.get("content", []) if isinstance(item, dict))
    if text.startswith(INJECTED):
        return ""
    return re.sub(r"\bsk-[A-Za-z0-9_-]{16,}", "[REDACTED_KEY]", text)


def extract():
    turns = {}
    active = None
    for line_number, line in enumerate(SOURCE.open(), 1):
        row = json.loads(line)
        payload = row.get("payload", {})
        if row["type"] == "event_msg" and payload.get("type") == "task_started":
            active = payload.get("turn_id")
        if row["type"] == "turn_context":
            active = payload.get("turn_id")
        if not active:
            continue
        turn = turns.setdefault(active, {"id": active, "date": row["timestamp"][:10], "messages": [], "tools": Counter(), "first_line": line_number})
        if row["type"] != "response_item":
            continue
        kind = payload.get("type")
        if kind in ("function_call", "custom_tool_call"):
            turn["tools"][payload.get("name", kind)] += 1
        if kind != "message" or payload.get("role") not in ("user", "assistant"):
            continue
        text = visible_text(payload)
        if text:
            turn["messages"].append({"line": line_number, "at": row["timestamp"], "role": payload["role"], "phase": payload.get("phase"), "text": text})
    return [turn for turn in turns.values() if turn["messages"]]


if __name__ == "__main__":
    assert visible_text({"content": [{"text": "<environment_context>noise"}]}) == ""
    assert visible_text({"content": [{"text": "请先讨论方案"}]}) == "请先讨论方案"
    assert "sk-" not in visible_text({"content": [{"text": "sk-" + "a" * 24}]})
    OUTPUT.mkdir(parents=True, exist_ok=True)
    segments = [[] for _ in range(6)]
    for turn in extract():
        segments[sum(turn["date"] >= cut for cut in CUTS)].append(turn)
    coverage = []
    for number, turns in enumerate(segments, 1):
        prefix = OUTPUT / f"part-{number}"
        with prefix.with_suffix(".jsonl").open("w") as stream:
            for turn in turns:
                stream.write(json.dumps(turn, ensure_ascii=False) + "\n")
        outline = []
        dialogue = []
        for turn in turns:
            users = [m["text"] for m in turn["messages"] if m["role"] == "user"]
            outline.append(f'{turn["date"]}\t{turn["id"]}\tL{turn["first_line"]}\t' + " | ".join(users).replace("\n", " ")[:280])
            dialogue.append(f'\n## {turn["date"]} · {turn["id"]} · raw L{turn["first_line"]}\n')
            for message in turn["messages"]:
                if message["role"] == "assistant" and message["phase"] == "commentary":
                    continue
                dialogue.append(f'\n### {message["role"]} · raw L{message["line"]}\n\n{message["text"]}\n')
        prefix.with_suffix(".index.txt").write_text("\n".join(outline) + "\n")
        prefix.with_suffix(".md").write_text("".join(dialogue))
        coverage.append({"part": number, "from": turns[0]["date"], "to": turns[-1]["date"], "turns": len(turns), "dialogue_chars": sum(map(len, dialogue)), "user_messages": sum(m["role"] == "user" for t in turns for m in t["messages"])})
    (OUTPUT / "coverage.json").write_text(json.dumps({"source": str(SOURCE), "segments": coverage}, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(coverage, ensure_ascii=False))
