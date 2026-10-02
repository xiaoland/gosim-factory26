import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]


def records(path):
    body = (ROOT / path).read_text()
    for block in re.split(r"(?=^## Record \d+\n)", body, flags=re.M):
        if not block.startswith("## Record "):
            continue
        number = int(re.match(r"## Record (\d+)", block).group(1))
        source = block.splitlines()[1][8:]
        yield number, source, json.loads(block[block.index("{") :])


def content_parts(item):
    if isinstance(item, str):
        return [item]
    if isinstance(item, list):
        return sum((content_parts(part) for part in item), [])
    if isinstance(item, dict):
        typ = item.get("type", "")
        if typ == "text":
            return [item.get("text", "")]
        if typ == "thinking":
            return []
        if typ == "toolCall":
            return [f"CALL {item.get('name')} {json.dumps(item.get('arguments'), ensure_ascii=False)}"]
        if typ == "image":
            return ["[image]"]
        return [json.dumps(item, ensure_ascii=False)]
    return [str(item)]


def main():
    path = sys.argv[1]
    start = int(sys.argv[2])
    end = int(sys.argv[3])
    limit = int(sys.argv[4]) if len(sys.argv) > 4 else 2000
    for num, source, data in records(path):
        if not start <= num <= end:
            continue
        role = data.get("message", {}).get("role") or data.get("role") or data.get("recordType") or data.get("type")
        stamp = data.get("timestamp", "")
        parts = content_parts(data.get("message", {}).get("content", data.get("text", "")))
        if not parts and data.get("type") != "message":
            parts = [json.dumps({k:v for k,v in data.items() if k not in ("id", "parentId", "message")}, ensure_ascii=False)]
        print(f"\n### {pathlib.Path(path).name} #{num} {role} {stamp} SOURCE {source}")
        for index, part in enumerate(parts, 1):
            part = part.replace("\\n", "\n")
            if len(part) > limit:
                print(f"PART {index} LENGTH {len(part)} TRUNCATED {part[:limit//2]}\n[...omitted...]\n{part[-limit//2:]}")
            else:
                print(f"PART {index} {part}")


if __name__ == "__main__":
    main()
