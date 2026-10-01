#!/usr/bin/env python3
"""Disposable BSL authoring/runtime conformance spike; not product code."""

from __future__ import annotations

import argparse
import hashlib
import http.client
import json
import random
import re
import shutil
import socket
import subprocess
import tempfile
import threading
import time
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import yaml
from cel_expr_python import cel
from faker import Faker


UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.IGNORECASE,
)
TOKEN_RE = re.compile(r"^ride_[a-z0-9]{16}$")
DVLA_CURRENT_RE = re.compile(r"^[A-HJ-PR-Y]{2}[0-9]{2} [A-HJ-PR-Z]{3}$")
BSL_CEL_PROFILE = """
stdlib:
  exclude_macros:
    - all
    - exists
    - exists_one
    - map
    - filter
"""


def compact_json(value: Any) -> bytes:
    return json.dumps(value, separators=(",", ":"), ensure_ascii=False).encode()


def request_json(method: str, url: str, body: Any | None = None) -> tuple[int, bytes]:
    data = None if body is None else compact_json(body)
    req = urllib.request.Request(url, data=data, method=method)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as error:
        return error.code, error.read()


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def validate_uuid(value: str) -> bool:
    if not UUID_RE.fullmatch(value):
        return False
    try:
        return str(uuid.UUID(value)).lower() == value.lower()
    except ValueError:
        return False


def validate_dvla_current_syntax(value: str) -> bool:
    """Validate only DVLA current-style syntax, never issuance/existence."""
    return bool(DVLA_CURRENT_RE.fullmatch(value)) and "I" not in value and "Q" not in value


def generate_dvla_current_syntax(seed: int) -> str:
    """Independent spike adapter; it is intentionally not an SVC built-in."""
    rng = random.Random(seed)
    memory_tag_letters = "ABCDEFGHJKLMNOPRSTUVWXY"  # no I, Q, or Z
    suffix_letters = "ABCDEFGHJKLMNOPRSTUVWXYZ"  # no I or Q; Z is permitted
    prefix = "".join(rng.choice(memory_tag_letters) for _ in range(2))
    age = "".join(rng.choice("0123456789") for _ in range(2))
    suffix = "".join(rng.choice(suffix_letters) for _ in range(3))
    return f"{prefix}{age} {suffix}"


def generate_token(seed: int) -> str:
    rng = random.Random(seed ^ 0x5C)
    alphabet = "abcdefghijklmnopqrstuvwxyz0123456789"
    return "ride_" + "".join(rng.choice(alphabet) for _ in range(16))


def evaluate_cel(source: str, captures: dict[str, str]) -> str:
    config = cel.NewEnvConfigFromYaml(BSL_CEL_PROFILE)
    env = cel.NewEnv(
        config=config,
        variables={"captures": cel.Type.Map(cel.Type.STRING, cel.Type.STRING)}
    )
    expression = env.compile(source)
    if expression.return_type() != cel.Type.STRING:
        raise TypeError(f"CEL expression must return string: {source}")
    return str(expression.eval(data={"captures": captures}).value())


def materialize_node(node: Any, captures: dict[str, str], seed: int) -> Any:
    if isinstance(node, list):
        return [materialize_node(item, captures, seed) for item in node]
    if not isinstance(node, dict):
        return node
    if set(node) != {"$bsl"}:
        return {key: materialize_node(value, captures, seed) for key, value in node.items()}

    spec = node["$bsl"]
    if "generate" in spec:
        generation = spec["generate"]
        identity = generation["using"]
        if identity == "svc.opaque-token/v1":
            value = generate_token(seed)
            valid = bool(TOKEN_RE.fullmatch(value))
        elif identity == "spike.uk-dvla-current-style/v1":
            value = generate_dvla_current_syntax(seed)
            valid = validate_dvla_current_syntax(value)
        else:
            raise ValueError(f"unknown generator: {identity}")
        if not valid:
            raise ValueError(f"generated value failed independent validation: {identity}")
    elif "derive" in spec:
        value = evaluate_cel(spec["derive"], captures)
    elif "example" in spec:
        value = spec["example"]
    else:
        raise ValueError(f"value node has no role: {spec}")

    matcher = spec.get("match", spec.get("generate", {}).get("match"))
    if matcher:
        if matcher.get("semantic") == "rfc.uuid" and not validate_uuid(value):
            raise ValueError(f"not an RFC UUID: {value}")
        if matcher.get("semantic") == "uk.dvla.current-registration-mark.syntax" and not validate_dvla_current_syntax(value):
            raise ValueError(f"not current-style DVLA syntax: {value}")
        if "regex" in matcher and not re.fullmatch(matcher["regex"], value):
            raise ValueError(f"value does not match {matcher['regex']}: {value}")
    if binding := spec.get("bind"):
        captures[binding] = value
    return value


def compile_scenario(path: Path) -> dict[str, Any]:
    document = yaml.safe_load(path.read_text())
    if set(document) != {"language", "scenario"}:
        raise ValueError("unknown top-level BSL key")
    scenario = document["scenario"]
    if scenario["policy"] != {
        "unmatched": "fail",
        "real-egress": "deny",
        "state": "isolated-run",
    }:
        raise ValueError("spike requires strict fail-closed policy")
    if len(scenario["interactions"]) != 1 or len(scenario["events"]) != 1:
        raise ValueError("spike expects exactly one interaction and one event")

    seed = int(scenario["run"]["seed"])
    captures: dict[str, str] = {}
    interaction = scenario["interactions"][0]
    response_body = materialize_node(interaction["response"]["body"]["json"], captures, seed)
    request_external = interaction["request"]["body"]["json"]["externalId"]["$bsl"]
    normalized = {
        "ir": "svc.bsl.ir/v0-spike",
        "scenario": {
            "name": scenario["name"],
            "claim": scenario["claim"],
            "boundary": scenario["boundary"],
            "contract": scenario["contract"],
            "policy": scenario["policy"],
            "run": scenario["run"],
        },
        "interaction": {
            "name": interaction["name"],
            "provenance": interaction["provenance"],
            "fidelity": interaction["fidelity"],
            "request": {
                "method": interaction["request"]["method"],
                "path": interaction["request"]["path"],
                "body": {
                    "externalId": {
                        "example": request_external["example"],
                        "matcher": request_external["match"],
                        "bind": request_external["bind"],
                    }
                },
            },
            "response": {
                "status": interaction["response"]["status"],
                "headers": interaction["response"]["headers"],
                "body": response_body,
            },
        },
        "event": scenario["events"][0],
        "arranged_captures": captures,
        "replay": {
            "seed": seed,
            "clock": str(scenario["run"]["clock"]),
            "generators": [
                "svc.opaque-token/v1",
                "spike.uk-dvla-current-style/v1",
            ],
            "validators": [
                "rfc.uuid",
                "spike.uk-dvla-current-style-validator/v1",
            ],
        },
    }
    return normalized


@dataclass
class Journal:
    requests: list[dict[str, Any]] = field(default_factory=list)


def native_server(ir: dict[str, Any], journal: Journal) -> ThreadingHTTPServer:
    interaction = ir["interaction"]

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length)
            matched = False
            try:
                body = json.loads(raw)
                matched = (
                    self.path == interaction["request"]["path"]
                    and validate_uuid(body.get("externalId", ""))
                )
            except (json.JSONDecodeError, AttributeError):
                body = None
            journal.requests.append(
                {"path": self.path, "body": body, "raw": raw.hex(), "matched": matched}
            )
            if not matched:
                self.send_response(404)
                self.end_headers()
                return
            payload = compact_json(interaction["response"]["body"])
            self.send_response(interaction["response"]["status"])
            for name, value in interaction["response"]["headers"].items():
                self.send_header(name, value)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, format: str, *args: Any) -> None:
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def wiremock_mapping(ir: dict[str, Any]) -> dict[str, Any]:
    interaction = ir["interaction"]
    return {
        "name": interaction["name"],
        "request": {
            "method": interaction["request"]["method"],
            "urlPath": interaction["request"]["path"],
            "bodyPatterns": [
                {
                    "matchesJsonPath": {
                        "expression": "$.externalId",
                        "matches": UUID_RE.pattern,
                    }
                }
            ],
        },
        "response": {
            "status": interaction["response"]["status"],
            "headers": interaction["response"]["headers"],
            "jsonBody": interaction["response"]["body"],
        },
    }


def start_wiremock(jar: Path, mapping: dict[str, Any]) -> tuple[subprocess.Popen[str], int, float, Path]:
    root = Path(tempfile.mkdtemp(prefix="svc-bsl-wiremock-"))
    (root / "mappings").mkdir()
    (root / "__files").mkdir()
    (root / "mappings" / "create-ride.json").write_text(json.dumps(mapping, indent=2))
    port = free_port()
    started = time.monotonic()
    process = subprocess.Popen(
        [
            "java",
            "-jar",
            str(jar),
            "--root-dir",
            str(root),
            "--port",
            str(port),
            "--disable-gzip",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        try:
            status, _ = request_json("GET", f"http://127.0.0.1:{port}/__admin/mappings")
            if status == 200:
                return process, port, time.monotonic() - started, root
        except (urllib.error.URLError, ConnectionError):
            pass
        if process.poll() is not None:
            output = process.stdout.read() if process.stdout else ""
            raise RuntimeError(f"WireMock exited early: {output}")
        time.sleep(0.05)
    process.terminate()
    raise TimeoutError("WireMock did not start")


@dataclass
class CallbackRecord:
    path: str = ""
    headers: dict[str, str] = field(default_factory=dict)
    raw: bytes = b""


def callback_server(record: CallbackRecord) -> ThreadingHTTPServer:
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            record.path = self.path
            record.headers = {key.lower(): value for key, value in self.headers.items()}
            record.raw = self.rfile.read(int(self.headers.get("Content-Length", "0")))
            self.send_response(204)
            self.end_headers()

        def log_message(self, format: str, *args: Any) -> None:
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def materialize_event(ir: dict[str, Any], captures: dict[str, str]) -> tuple[dict[str, str], bytes]:
    event = ir["event"]["request"]
    headers = materialize_node(event["headers"], captures, int(ir["replay"]["seed"]))
    body = materialize_node(event["body"]["json"], captures, int(ir["replay"]["seed"]))
    return headers, compact_json(body)


def send_raw_event(port: int, path: str, headers: dict[str, str], raw: bytes) -> int:
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    connection.request("POST", path, body=raw, headers={**headers, "Content-Length": str(len(raw))})
    response = connection.getresponse()
    response.read()
    connection.close()
    return response.status


def exercise_http(
    base_url: str, expected: dict[str, Any], external_id: str
) -> dict[str, Any]:
    valid_status, valid_raw = request_json(
        "POST", f"{base_url}/v1/rides", {"externalId": external_id}
    )
    retry_status, retry_raw = request_json(
        "POST", f"{base_url}/v1/rides", {"externalId": external_id}
    )
    invalid_status, invalid_raw = request_json(
        "POST", f"{base_url}/v1/rides", {"externalId": "not-a-uuid"}
    )
    unknown_status, unknown_raw = request_json("POST", f"{base_url}/not-declared", {})
    valid_body = json.loads(valid_raw)
    assert valid_status == 201
    assert retry_status == 201 and retry_raw == valid_raw
    assert invalid_status == 404 and unknown_status == 404
    assert valid_body == expected
    return {
        "external_id": external_id,
        "status": valid_status,
        "retry_same_response": retry_raw == valid_raw,
        "invalid_status": invalid_status,
        "unknown_status": unknown_status,
        "invalid_diagnostic_bytes": len(invalid_raw),
        "invalid_has_near_miss": b"Closest stub" in invalid_raw,
        "unknown_diagnostic_bytes": len(unknown_raw),
        "response_sha256": hashlib.sha256(valid_raw).hexdigest(),
    }


def faker_conformance(sample_size: int) -> dict[str, int]:
    faker = Faker("en_GB")
    faker.seed_instance(20260810)
    counts = {
        "valid_canonical": 0,
        "missing_space_only": 0,
        "forbidden_i_or_q": 0,
        "z_in_memory_tag": 0,
    }
    for _ in range(sample_size):
        value = faker.license_plate()
        normalized = value if " " in value else value[:4] + " " + value[4:]
        if validate_dvla_current_syntax(value):
            counts["valid_canonical"] += 1
        elif "I" in value or "Q" in value:
            counts["forbidden_i_or_q"] += 1
        elif value[0] == "Z" or value[1] == "Z":
            counts["z_in_memory_tag"] += 1
        elif validate_dvla_current_syntax(normalized):
            counts["missing_space_only"] += 1
        else:
            raise AssertionError(f"unclassified Faker plate: {value}")
    return counts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", type=Path, required=True)
    parser.add_argument("--wiremock-jar", type=Path, required=True)
    parser.add_argument(
        "--external-id",
        default="123e4567-e89b-42d3-a456-426614174000",
    )
    args = parser.parse_args()

    ir = compile_scenario(args.scenario)
    seed = int(ir["replay"]["seed"])
    plate = ir["interaction"]["response"]["body"]["vehicleRegistration"]
    replay_plate = generate_dvla_current_syntax(seed)
    assert plate == replay_plate and validate_dvla_current_syntax(plate)

    faker = Faker("en_GB")
    faker.seed_instance(seed)
    faker_plate = faker.license_plate()
    assert not validate_dvla_current_syntax(faker_plate)
    faker_counts = faker_conformance(10_000)

    native_journal = Journal()
    native = native_server(ir, native_journal)
    native_port = native.server_address[1]
    native_result = exercise_http(
        f"http://127.0.0.1:{native_port}",
        ir["interaction"]["response"]["body"],
        args.external_id,
    )
    native.shutdown()
    native.server_close()

    mapping = wiremock_mapping(ir)
    wiremock, wiremock_port, startup_seconds, wiremock_root = start_wiremock(
        args.wiremock_jar, mapping
    )
    try:
        wiremock_result = exercise_http(
            f"http://127.0.0.1:{wiremock_port}",
            ir["interaction"]["response"]["body"],
            args.external_id,
        )
        wiremock_rss_kib = int(
            subprocess.check_output(
                ["ps", "-o", "rss=", "-p", str(wiremock.pid)], text=True
            ).strip()
        )
        journal_status, journal_raw = request_json(
            "GET", f"http://127.0.0.1:{wiremock_port}/__admin/requests"
        )
        assert journal_status == 200
        journal = json.loads(journal_raw)
        matched_count = sum(1 for request in journal["requests"] if request["wasMatched"])
        unmatched_count = sum(1 for request in journal["requests"] if not request["wasMatched"])
        matched_external_ids = {
            json.loads(request["request"]["body"])["externalId"]
            for request in journal["requests"]
            if request["wasMatched"]
        }
        assert matched_external_ids == {wiremock_result["external_id"]}
    finally:
        wiremock.terminate()
        wiremock.wait(timeout=10)
        shutil.rmtree(wiremock_root)

    captures = dict(ir["arranged_captures"])
    captures["external_id"] = native_result["external_id"]
    callback_record = CallbackRecord()
    callback = callback_server(callback_record)
    callback_port = callback.server_address[1]
    event_headers, event_raw = materialize_event(ir, captures)
    event_status = send_raw_event(
        callback_port, ir["event"]["request"]["path"], event_headers, event_raw
    )
    callback.shutdown()
    callback.server_close()
    assert event_status == 204
    assert callback_record.raw == event_raw
    assert json.loads(callback_record.raw)["externalId"] == captures["external_id"]

    try:
        evaluate_cel("captures.external_id + 1", captures)
        cel_diagnostic = "missing"
    except RuntimeError as error:
        cel_diagnostic = str(error).splitlines()[0]
    cel_env = cel.NewEnv()
    cel_comprehension = (
        cel_env.compile("[1, 2, 3].map(x, x + 1)").eval().plain_value()
    )
    try:
        cel_env.compile("env('SECRET')")
        undeclared_function_rejected = False
    except RuntimeError:
        undeclared_function_rejected = True
    restricted_cel = cel.NewEnv(config=cel.NewEnvConfigFromYaml(BSL_CEL_PROFILE))
    try:
        restricted_cel.compile("[1, 2, 3].map(x, x + 1)")
        restricted_comprehension_rejected = False
    except RuntimeError:
        restricted_comprehension_rejected = True

    result = {
        "status": "pass",
        "surface": "local-typed-node",
        "normalized_ir_sha256": hashlib.sha256(compact_json(ir)).hexdigest(),
        "semantic_generation": {
            "faker_40_1_0_seed_123": faker_plate,
            "faker_rejected_by_independent_validator": True,
            "faker_10k": faker_counts,
            "adapter_value": plate,
            "adapter_replay_equal": plate == replay_plate,
            "adapter_validated": True,
        },
        "cel": {
            "derived_external_id": json.loads(callback_record.raw)["externalId"],
            "static_type_diagnostic": cel_diagnostic,
            "standard_comprehension_enabled": cel_comprehension == [2, 3, 4],
            "bsl_profile_rejects_comprehension": restricted_comprehension_rejected,
            "undeclared_env_function_rejected": undeclared_function_rejected,
        },
        "native": {
            **native_result,
            "journal_entries": len(native_journal.requests),
            "matched_count": sum(1 for request in native_journal.requests if request["matched"]),
        },
        "wiremock_3_13_2": {
            **wiremock_result,
            "startup_seconds": round(startup_seconds, 3),
            "rss_kib_local_probe": wiremock_rss_kib,
            "jar_bytes": args.wiremock_jar.stat().st_size,
            "jar_sha256": hashlib.sha256(args.wiremock_jar.read_bytes()).hexdigest(),
            "matched_count": matched_count,
            "unmatched_count": unmatched_count,
            "projection": mapping,
        },
        "callback": {
            "explicitly_triggered": True,
            "status": event_status,
            "raw_body_preserved": callback_record.raw == event_raw,
            "raw_body_sha256": hashlib.sha256(callback_record.raw).hexdigest(),
            "path": callback_record.path,
            "event_header": callback_record.headers["x-provider-event"],
            "serialization": "json.compact-utf8/v1-spike",
        },
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
