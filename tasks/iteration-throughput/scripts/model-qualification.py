#!/usr/bin/env python3
"""Run one bounded, no-retry capability probe for each target model."""
import argparse
import base64
import concurrent.futures
import json
import struct
import subprocess
import time
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
import sys
sys.path.insert(0, str(ROOT / "scripts"))
from factory import api_key

BASE_URL = "https://api.arc-bench.com/v1"
TIMEOUT = 120


def png_data_url():
    row = b"\0" + b"\xff\0\0" * 32
    raw = row * 32

    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff)

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", 32, 32, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(raw, 9))
    png += chunk(b"IEND", b"")
    return "data:image/png;base64," + base64.b64encode(png).decode()


def tool(name, properties):
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": "Report the requested probe value.",
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": list(properties),
                "additionalProperties": False,
            },
        },
    }


def requests(model=None):
    lookup = tool("lookup", {"q": {"type": "string"}, "limit": {"type": "integer"}})
    observe = tool("observe", {"color": {"type": "string"}})
    requests = [
        {
            "model": "deepseek-v4-flash",
            "messages": [{"role": "user", "content": "Call lookup with q=ping and limit=1. Do not answer in text."}],
            "tools": [lookup],
            "tool_choice": {"type": "function", "function": {"name": "lookup"}},
        },
        {
            "model": "glm-5.3-flash",
            "messages": [{"role": "user", "content": "Call lookup with q=ping and limit=1. Do not answer in text."}],
            "tools": [lookup],
            "tool_choice": {"type": "function", "function": {"name": "lookup"}},
        },
        {
            "model": "deepseek-v4-flash-vision-exp",
            "messages": [{"role": "user", "content": [
                {"type": "text", "text": "Use observe to report the dominant color in this image. Return red as the color."},
                {"type": "image_url", "image_url": {"url": png_data_url()}},
            ]}],
            "tools": [observe],
        },
    ]
    return [request for request in requests if model is None or request["model"] == model]


def validate(response, expected_name, expected_args):
    if not isinstance(response, dict):
        return False, "response is not a JSON object"
    if response.get("error") is not None:
        return False, "gateway returned error"
    choices = response.get("choices")
    if not isinstance(choices, list) or not choices:
        return False, "missing choices"
    choice = choices[0]
    if choice.get("finish_reason") == "length":
        return False, "truncated finish_reason=length"
    message = choice.get("message")
    calls = message.get("tool_calls") if isinstance(message, dict) else None
    if not isinstance(calls, list) or len(calls) != 1:
        return False, "expected exactly one tool call"
    function = calls[0].get("function")
    if not isinstance(function, dict) or function.get("name") != expected_name:
        return False, "tool function name mismatch"
    try:
        arguments = json.loads(function.get("arguments", ""))
    except (TypeError, json.JSONDecodeError):
        return False, "tool arguments are not JSON"
    if arguments != expected_args:
        return False, "tool arguments mismatch"
    return True, None


def run_one(request, output, key):
    model = request["model"]
    slug = model.replace("/", "_")
    request_path = output / (slug + ".request.json")
    response_path = output / (slug + ".response.json")
    stderr_path = output / (slug + ".stderr")
    request_path.write_text(json.dumps(request | {"reasoning_effort": "high", "stream": False, "max_tokens": 2048}, ensure_ascii=False, indent=2) + "\n")
    config = (
        f'url = "{BASE_URL}/chat/completions"\n'
        'header = "Content-Type: application/json"\n'
        f'header = "Authorization: Bearer {key.replace(chr(92), chr(92) * 2).replace(chr(34), chr(92) + chr(34))}"\n'
        'silent\nshow-error\n'
        f'max-time = {TIMEOUT}\noutput = "{response_path}"\nwrite-out = "%{{http_code}}"\n'
    )
    started = time.monotonic()
    curl_exit = None
    http_status = None
    stderr = ""
    try:
        result = subprocess.run(
            ["curl", "--config", "-", "--data-binary", "@" + str(request_path)],
            input=config,
            capture_output=True,
            text=True,
            timeout=TIMEOUT + 5,
        )
        curl_exit = result.returncode
        stderr = result.stderr
        try:
            http_status = int(result.stdout.strip())
        except ValueError:
            pass
    except subprocess.TimeoutExpired as exc:
        stderr = (exc.stderr or "") if isinstance(exc.stderr, str) else "curl timeout"
        stderr += "\ncurl process timeout\n"
    elapsed = round(time.monotonic() - started, 3)
    stderr_path.write_text(stderr.replace(key, "<redacted>"))
    raw = response_path.read_text() if response_path.exists() else ""
    safe_raw = raw.replace(key, "<redacted>")
    response_path.write_text(safe_raw)
    try:
        response = json.loads(safe_raw)
    except json.JSONDecodeError:
        response = None
    message = None
    if isinstance(response, dict) and response.get("choices"):
        message = response["choices"][0].get("message")
    reasoning_fields = [field for field in ("reasoning", "reasoning_content") if isinstance(message, dict) and field in message]
    expected = ("observe", {"color": "red"}) if model.endswith("vision-exp") else ("lookup", {"q": "ping", "limit": 1})
    if curl_exit != 0:
        passed, failure = False, f"curl exit {curl_exit}"
    elif http_status != 200:
        error = response.get("error") if isinstance(response, dict) else None
        if isinstance(error, dict):
            detail = error.get("message") or error.get("code") or "unknown gateway error"
            failure = f"HTTP {http_status} gateway error: {detail}"
        else:
            failure = f"HTTP {http_status} without a valid completion"
        passed = False
    else:
        passed, failure = validate(response, *expected)
    result = {
        "model": model,
        "status": "passed" if passed else "failed",
        "http_status": http_status,
        "curl_exit": curl_exit,
        "elapsed_seconds": elapsed,
        "usage": response.get("usage") if isinstance(response, dict) else None,
        "reasoning_present": bool(reasoning_fields),
        "reasoning_fields": reasoning_fields,
        "failure": failure,
        "request": request_path.name,
        "response": response_path.name,
        "stderr": stderr_path.name,
    }
    (output / (slug + ".json")).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "runs/qualification/models")
    parser.add_argument("--model", choices=["deepseek-v4-flash", "glm-5.3-flash", "deepseek-v4-flash-vision-exp"])
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    key = api_key()
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        futures = [pool.submit(run_one, request, args.output, key) for request in requests(args.model)]
        results = [future.result() for future in futures]
    summary = {"status": "passed" if all(r["status"] == "passed" for r in results) else "failed", "models": results}
    (args.output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(summary, ensure_ascii=False))
    raise SystemExit(0 if summary["status"] == "passed" else 1)


if __name__ == "__main__":
    main()
