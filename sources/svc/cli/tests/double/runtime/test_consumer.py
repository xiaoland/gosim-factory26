from __future__ import annotations
import json
import subprocess
import sys
import time
from pathlib import Path
import urllib3
from svc_cli.double.materialization import (
    compact_json,
)
from svc_cli.double.service import (
    emit_event,
    stop_run,
)

from ..support.runs import cleanup_run, start_double_run
from ..support.scenarios import (
    CONSUMER_FIXTURES,
    FIRST_EXTERNAL_ID,
    FIRST_REQUEST_ID,
)


def test_black_box_consumer_owns_the_public_product_assertion(tmp_path: Path) -> None:
    ready_path = tmp_path / "consumer.ready"
    provider_path = tmp_path / "provider.origin"
    consumer = subprocess.Popen(
        (
            sys.executable,
            str(CONSUMER_FIXTURES / "consumer_app.py"),
            str(ready_path),
            str(provider_path),
        ),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    started = None
    stopped = False
    try:
        deadline = time.monotonic() + 5
        while not ready_path.is_file():
            if consumer.poll() is not None:
                stderr = b"" if consumer.stderr is None else consumer.stderr.read()
                raise AssertionError(f"Consumer exited before readiness: {stderr!r}")
            if time.monotonic() >= deadline:
                raise AssertionError("Consumer did not publish readiness")
            time.sleep(0.02)
        consumer_origin = ready_path.read_text(encoding="utf-8")
        started, run_root, execution_root = start_double_run(
            tmp_path,
            consumer_origin,
            seed=123,
        )
        provider_path.write_text(started.responder_url, encoding="utf-8")

        manager = urllib3.PoolManager(retries=False)
        accepted = manager.request(
            "POST",
            consumer_origin + "/orders/pay",
            body=compact_json(
                {"externalId": FIRST_EXTERNAL_ID, "requestId": FIRST_REQUEST_ID}
            ),
            headers={"Content-Type": "application/json"},
            redirect=False,
            retries=False,
            timeout=urllib3.Timeout(total=5),
        )
        assert accepted.status == 202
        assert (
            emit_event(
                started.run_id,
                "payment.succeeded",
                run_root=run_root,
            ).status
            == "acknowledged"
        )

        public_order = manager.request(
            "GET",
            consumer_origin + f"/orders/{FIRST_EXTERNAL_ID}",
            redirect=False,
            retries=False,
            timeout=urllib3.Timeout(total=5),
        )

        assert json.loads(public_order.data) == {"status": "paid"}
        assert stop_run(started.run_id, run_root=run_root).status == "stopped"
        stopped = True
    finally:
        if started is not None and not stopped:
            cleanup_run(started.run_id, run_root, execution_root)
        if consumer.poll() is None:
            consumer.terminate()
        consumer.wait(timeout=5)
