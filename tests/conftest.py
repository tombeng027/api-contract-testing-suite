import hashlib
import json
import logging
import socket
import threading
import time
from collections.abc import Iterator
from datetime import datetime, timezone
from queue import Empty, Queue

import httpx
import pytest
import uvicorn

from catalog_api.app import create_app


@pytest.fixture
def app_url(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> Iterator[str]:
    identity = hashlib.sha256(request.node.nodeid.encode("utf-8")).hexdigest()[:16]
    log_path = request.config.rootpath / "artifacts" / "lifecycle" / f"{identity}.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text("", encoding="utf-8")
    request.node.add_report_section("setup", "lifecycle log", str(log_path))

    def record(event: str) -> None:
        with log_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps({
                "event": event, "test": request.node.nodeid,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }) + "\n")

    failures: Queue[BaseException] = Queue()
    listener = socket.socket()
    server: uvicorn.Server | None = None
    thread: threading.Thread | None = None
    try:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
        server = uvicorn.Server(uvicorn.Config(
            create_app(), lifespan="off", access_log=False,
            log_config=None, log_level="warning",
        ))
        # pytest capture can otherwise re-enable raw access logs on new connections.
        monkeypatch.setattr(logging.getLogger("uvicorn.access"), "disabled", True)
        active_server = server

        def run_server() -> None:
            try:
                active_server.run(sockets=[listener])
            except BaseException as error:
                failures.put(error)

        thread = threading.Thread(target=run_server, daemon=True)
        record("app_starting")
        thread.start()
        url = f"http://127.0.0.1:{port}"
        deadline = time.monotonic() + 10
        last_error: httpx.TransportError | None = None
        with httpx.Client(base_url=url, timeout=0.5, trust_env=False) as probe:
            while time.monotonic() < deadline:
                if not thread.is_alive():
                    try:
                        failure = failures.get_nowait()
                    except Empty:
                        pytest.fail("Catalog server exited before readiness")
                    raise RuntimeError("Catalog server failed during startup") from failure
                try:
                    response = probe.get("/health")
                    if response.status_code == 200 and response.json() == {"status": "ok"}:
                        break
                except httpx.TransportError as error:
                    last_error = error
                threading.Event().wait(0.05)
            else:
                pytest.fail(f"Catalog server not ready after 10 seconds: {last_error}")
        record("app_ready")
        yield url
    finally:
        if server is not None:
            server.should_exit = True
        if thread is not None and thread.ident is not None:
            thread.join(timeout=5)
        listener.close()
        if thread is not None and thread.is_alive():
            record("app_stop_failed")
            pytest.fail("Catalog server did not stop within 5 seconds")
        record("app_stopped")
        try:
            failure = failures.get_nowait()
        except Empty:
            pass
        else:
            raise RuntimeError("Catalog server thread failed") from failure


@pytest.fixture
def client(app_url: str) -> Iterator[httpx.Client]:
    with httpx.Client(base_url=app_url, timeout=2, trust_env=False) as connection:
        yield connection
