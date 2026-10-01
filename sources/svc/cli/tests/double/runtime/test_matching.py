from __future__ import annotations
import http.client
import json
import urllib.parse
from svc_cli.double.materialization import (
    match_body,
    matcher_accepts,
)
from svc_cli.double.model import (
    CaptureValueNode,
    EnumMatcher,
    ExactMatcher,
    LiteralValueNode,
    SemanticMatcher,
    StructuredBody,
)
from svc_cli.double.runtime import ResponderServer

from ..support.http import (
    engine_request,
)
from ..support.scenarios import (
    FIRST_EXTERNAL_ID,
    SECOND_EXTERNAL_ID,
    build_engine,
    payment_target,
)


def test_in_process_matching_capture_and_seed_replay() -> None:
    engine = build_engine(123)

    first = engine_request(engine)
    equal_retry = engine_request(engine)
    conflict = engine_request(engine, external_id=SECOND_EXTERNAL_ID)

    assert first[0] == equal_retry[0] == 201
    assert first[1:] == equal_retry[1:]
    assert conflict[0] == 409
    assert json.loads(conflict[2])["error"]["code"] == "double-capture-conflict"
    assert engine.context.bindings["external_id"] == FIRST_EXTERNAL_ID
    statuses = [
        entry.status
        for entry in engine.observation(run_id="run", sealed=False).journal.entries
    ]
    assert statuses == [
        "matched",
        "matched",
        "capture-conflict",
    ]

    replayed = engine_request(build_engine(123))
    challenged = engine_request(build_engine(456))
    assert replayed[1:] == first[1:]
    assert challenged[0] == 201
    assert challenged[2] != first[2]


def test_json_null_capture_and_boolean_number_equality_are_type_safe() -> None:
    engine = build_engine(123)
    interaction = engine.scenario.interactions[0]
    nullable = StructuredBody(
        template=None,
        nodes=(
            CaptureValueNode(
                path=(),
                name="nullable",
                matcher=EnumMatcher(values=(None, 1)),
            ),
        ),
    )
    request = interaction.request.model_copy(update={"body": nullable})
    engine.scenario = engine.scenario.model_copy(
        update={
            "contract": None,
            "interactions": (interaction.model_copy(update={"request": request}),),
        }
    )

    accepted = engine_request(engine, body=b"null")
    conflict = engine_request(engine, body=b"1")

    assert accepted[0] == 201
    assert engine.context.bindings["nullable"] is None
    assert conflict[0] == 409
    assert json.loads(conflict[2])["error"]["code"] == "double-capture-conflict"
    exact_true = ExactMatcher(value=True)
    assert matcher_accepts(exact_true, True)
    assert not matcher_accepts(exact_true, 1)
    literal_true = StructuredBody(
        template=True,
        nodes=(LiteralValueNode(path=(), value=True),),
    )
    matched, _reasons, _captures, _actual = match_body(
        literal_true,
        b"1",
        engine.context,
        namespace="literal-type-safety",
    )
    assert matched is False
    rfc3339 = SemanticMatcher(semantic="rfc3339", using="svc.rfc3339/v1")
    assert matcher_accepts(rfc3339, "2026-08-10T10:00:00+08:00")
    assert not matcher_accepts(rfc3339, "2026-08-10 10:00:00+08:00")


def test_in_process_fail_closed_matching_and_request_bounds() -> None:
    no_match_engine = build_engine(123)
    no_match = engine_request(no_match_engine, target=payment_target("/unknown"))
    ambiguous_engine = build_engine(123, ambiguous=True)
    ambiguous = engine_request(ambiguous_engine)
    malformed_engine = build_engine(123)
    malformed = engine_request(malformed_engine, body=b"{")

    assert no_match[0] == 404
    assert json.loads(no_match[2])["error"]["code"] == "double-no-match"
    assert ambiguous[0] == 409
    assert json.loads(ambiguous[2])["error"]["code"] == "double-ambiguous-match"
    assert malformed[0] == 400
    assert json.loads(malformed[2])["error"]["code"] == "double-request-json-invalid"
    no_match_journal = no_match_engine.observation(run_id="run", sealed=False).journal
    ambiguous_journal = ambiguous_engine.observation(run_id="run", sealed=False).journal
    assert no_match_journal.entries[-1].status == "no-match"
    assert ambiguous_journal.entries[-1].status == "ambiguous-match"

    server = ResponderServer(build_engine(123))
    server.start()
    connection = http.client.HTTPConnection(
        urllib.parse.urlsplit(server.url).hostname,
        urllib.parse.urlsplit(server.url).port,
        timeout=5,
    )
    try:
        connection.putrequest("POST", "/v1/payments")
        connection.putheader("Content-Length", str(1_048_577))
        connection.endheaders()
        response = connection.getresponse()
        assert response.status == 413
        assert (
            json.loads(response.read())["error"]["code"] == "double-request-too-large"
        )
    finally:
        connection.close()
        server.stop()


def test_unrelated_structured_route_does_not_parse_an_empty_request_body() -> None:
    engine = build_engine(123)
    structured = engine.scenario.interactions[0]
    empty_request = structured.request.model_copy(
        update={
            "method": "GET",
            "path": "/v3/certificates",
            "query": {},
            "query_nodes": (),
            "headers": {},
            "header_nodes": (),
            "body": None,
        }
    )
    certificate = structured.model_copy(
        update={"name": "certificates", "request": empty_request}
    )
    engine.scenario = engine.scenario.model_copy(
        update={"interactions": (certificate, structured)}
    )

    status, _headers, _body = engine.handle_request(
        method="GET",
        target="/v3/certificates",
        headers={},
        raw_body=b"",
    )

    assert status == 201
    assert (
        engine.observation(run_id="run", sealed=False).journal.entries[-1].status
        == "matched"
    )
