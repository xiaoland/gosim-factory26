from __future__ import annotations
import json
import sys
from pathlib import Path
import pytest
from svc_cli.double.materialization import (
    run_materializer,
)
from svc_cli.double.model import (
    Materializer,
    SemanticMatcher,
)
from svc_cli.errors import SvcError

from ..support.http import (
    engine_request,
)
from ..support.scenarios import (
    FIRST_EXTERNAL_ID,
    build_engine,
)


def test_response_derived_value_receives_the_normalized_matched_request() -> None:
    engine = build_engine(123)
    interaction = engine.scenario.interactions[0]
    assert interaction.response.body is not None
    body_node = interaction.response.body.nodes[0].model_copy(
        update={
            "expression": "request.body.value.externalId",
            "validator": SemanticMatcher(
                semantic="rfc.uuid",
                using="svc.rfc-uuid/v1",
            ),
        }
    )
    response_body = interaction.response.body.model_copy(update={"nodes": (body_node,)})
    response = interaction.response.model_copy(update={"body": response_body})
    engine.scenario = engine.scenario.model_copy(
        update={
            "contract": None,
            "interactions": (interaction.model_copy(update={"response": response}),),
        }
    )

    status, _headers, raw = engine_request(engine)

    assert status == 201
    assert json.loads(raw) == {"paymentId": FIRST_EXTERNAL_ID}


def test_external_materializer_stdout_is_enforced_while_reading(tmp_path: Path) -> None:
    context = build_engine(123).context
    materializer = Materializer(
        argv=(sys.executable, "-c", "import sys; sys.stdout.write('x' * 4096)"),
        cwd=str(tmp_path),
        env={},
        timeout_ms=2_000,
        max_output_bytes=32,
    )

    with pytest.raises(SvcError) as caught:
        run_materializer(
            materializer,
            phase="response",
            context=context,
            request=None,
            expected_status=200,
        )

    assert caught.value.code == "double-materializer-output-too-large"


@pytest.mark.parametrize(
    ("headers", "code"),
    [
        ({"x-derived": "ok\r\nx-injected: yes"}, "double-header-value-invalid"),
        ({"content-length": "999"}, "double-header-name-invalid"),
    ],
)
def test_materialized_headers_cannot_escape_runtime_framing(
    headers: dict[str, object], code: str
) -> None:
    engine = build_engine(123)
    interaction = engine.scenario.interactions[0]
    response = interaction.response.model_copy(
        update={"headers": headers, "header_nodes": ()}
    )
    engine.scenario = engine.scenario.model_copy(
        update={
            "contract": None,
            "interactions": (interaction.model_copy(update={"response": response}),),
        }
    )

    status, _headers, raw = engine_request(engine)

    assert status == 500
    assert json.loads(raw)["error"]["code"] == code
