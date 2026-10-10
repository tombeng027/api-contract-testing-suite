import json
import re
import socket
import subprocess
import sys
import threading
from copy import deepcopy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files
from pathlib import Path
from types import SimpleNamespace

import pytest
from jsonschema import Draft202012Validator

from contracts.compatibility import consumer
from postman.runner import PostmanError, collection, resource, run_collection


def test_portable_export_matches_packaged_source() -> None:
    cases = json.loads(resource("requests.json"))
    assert len(cases) == 10
    assert len({case["name"] for case in cases}) == 10
    generated = collection(cases, resource("checks.js"))
    assert json.loads(resource("catalog.postman_collection.json")) == generated
    environment = json.loads(resource("catalog.postman_environment.json"))
    assert environment["values"] == [{
        "key": "base_url", "value": "http://127.0.0.1:8001", "type": "default", "enabled": True,
    }]


def test_postman_expectations_match_independent_contract() -> None:
    cases = json.loads(resource("requests.json"))
    for case in cases:
        expected = case["expected"]
        if expected["kind"] == "error":
            schema = json.loads(files("contracts").joinpath(
                "v1", "error.json"
            ).read_text(encoding="utf-8"))
            assert not list(Draft202012Validator(schema).iter_errors(expected["value"]))
            assert expected["status"] in (404, 422)
        else:
            values = expected["value"] if expected["kind"] == "list" else [expected["value"]]
            assert all(not list(consumer("v1").iter_errors(value)) for value in values)
            assert expected["status"] == 200
    seeds = [
        {"id": 1, "sku": "DEMO-001", "name": "Inspection kit", "price_cents": 2500, "available": True},
        {"id": 2, "sku": "DEMO-002", "name": "Replacement seal", "price_cents": 0, "available": False},
        {"id": 3, "sku": "DEMO-003", "name": "Test gauge", "price_cents": 1099, "available": True},
    ]
    assert cases[0]["expected"]["value"] == seeds[0]
    assert cases[1]["expected"]["value"] == seeds[1]
    assert cases[2]["expected"]["value"] == seeds
    assert cases[3]["expected"]["value"] == [seeds[0], seeds[2]]
    assert cases[4]["expected"]["value"] == [seeds[1]]
    for case in cases[5:]:
        assert case["expected"]["value"] == {
            "error": {
                "code": "PRODUCT_NOT_FOUND" if case["expected"]["status"] == 404 else "INVALID_REQUEST",
                "message": "Product not found" if case["expected"]["status"] == 404 else "Invalid request",
            },
        }


def test_live_postman_critical_parity(app_url: str, request: pytest.FixtureRequest) -> None:
    result = run_collection(
        json.loads(resource("catalog.postman_collection.json")), app_url,
        request.config.rootpath / "artifacts" / "postman-parity",
    )
    output = result.stdout_path.read_text(encoding="utf-8")
    errors = result.stderr_path.read_text(encoding="utf-8")
    assert result.exit_code == 0, output + errors
    assert not errors
    assert re.search(r"\|\s*requests\s*\|\s*10\s*\|\s*0\s*\|", output)
    assert re.search(r"\|\s*assertions\s*\|\s*40\s*\|\s*0\s*\|", output)
    for name in ("status", "media-type", "schema", "known-values"):
        assert len(re.findall(rf"^\s*Pass\s+{name}\s*$", output, re.MULTILINE)) == 10
    assert "View on Postman" not in output


def test_schema_valid_wrong_price_fails_exact_business_assertion(
    app_url: str, request: pytest.FixtureRequest,
) -> None:
    case = json.loads(resource("requests.json"))[0]
    case["expected"]["value"]["price_cents"] = 2501
    result = run_collection(
        collection([case], resource("checks.js")), app_url,
        request.config.rootpath / "artifacts" / "postman-parity",
    )
    output = result.stdout_path.read_text(encoding="utf-8")
    assert result.exit_code == 1, output
    assert re.search(r"\|\s*requests\s*\|\s*1\s*\|\s*0\s*\|", output)
    assert re.search(r"\|\s*assertions\s*\|\s*4\s*\|\s*1\s*\|", output)
    for name in ("status", "media-type", "schema"):
        assert re.search(rf"^\s*Pass\s+{name}\s*$", output, re.MULTILINE)
    assert "known-values" in output and "2500" in output and "2501" in output


def test_postman_selected_positive_and_negative_schema_oracles(
    request: pytest.FixtureRequest,
) -> None:
    original = json.loads(resource("requests.json"))[0]["expected"]
    product = original["value"]
    probes = [
        ("additive", {**product, "category": "DEMO"}, "application/json; charset=utf-8", 200, None),
        ("integral-float", {**product, "price_cents": 2500.0}, "application/json", 200, None),
        ("wrong-status", product, "application/json", 404, "status"),
        ("wrong-media", product, "text/plain", 200, "media-type"),
    ]
    for field, value in (
        ("id", True), ("id", 0), ("id", 2147483648), ("id", 1.5),
        ("sku", "   "), ("name", ""), ("price_cents", True),
        ("price_cents", "2500"), ("price_cents", -1), ("price_cents", 2500.5),
        ("available", "true"),
    ):
        probes.append((f"invalid-{field}-{len(probes)}", {**product, field: value},
                       "application/json", 200, "schema"))
    for field in product:
        probes.append((f"missing-{field}", {key: value for key, value in product.items() if key != field},
                       "application/json", 200, "schema"))
    cases = []
    for index, (name, _payload, _media, _status, _failure) in enumerate(probes):
        cases.append({"name": name, "path": f"/probe/{index}", "expected": deepcopy(original)})

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            index = int(self.path.rsplit("/", 1)[-1])
            _name, payload, media, status, _failure = probes[index]
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", media)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, _format: str, *args: object) -> None:
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        result = run_collection(
            collection(cases, resource("checks.js")),
            f"http://127.0.0.1:{server.server_port}",
            request.config.rootpath / "artifacts" / "postman-parity",
        )
        output = result.stdout_path.read_text(encoding="utf-8")
        assert result.exit_code == 1, output
        assert re.search(rf"\|\s*requests\s*\|\s*{len(probes)}\s*\|\s*0\s*\|", output)
        sections = re.split(r"^Root ", output, flags=re.MULTILINE)[1:]
        assert len(sections) == len(probes)
        for section, (name, _payload, _media, _status, failure) in zip(sections, probes, strict=True):
            assert section.splitlines()[0].strip() == name
            if failure is None:
                for assertion in ("status", "media-type", "schema", "known-values"):
                    assert re.search(rf"^\s*Pass\s+{assertion}\s*$", section, re.MULTILINE)
            else:
                assert not re.search(rf"^\s*Pass\s+{failure}\s*$", section, re.MULTILINE)
                assert failure in section
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        assert not thread.is_alive()


def test_missing_cli_is_actionable(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CATALOG_POSTMAN_CLI", str(tmp_path / "missing"))
    with pytest.raises(PostmanError, match="npm ci"):
        run_collection({}, "http://127.0.0.1:8001", tmp_path)


def verify_schema_probes(
    kind: str, probes: list[tuple[str, object, object, bool]], request: pytest.FixtureRequest,
) -> None:
    status = 404 if kind == "error" else 200
    schema = json.loads(files("contracts").joinpath(
        "v1", {"product": "product.json", "list": "products.json", "error": "error.json"}[kind],
    ).read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    cases = []
    for index, (name, payload, expected_value, valid) in enumerate(probes):
        assert validator.is_valid(payload) is valid, name
        cases.append({
            "name": name, "path": f"/probe/{index}",
            "expected": {"status": status, "kind": kind, "value": expected_value},
        })

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            body = json.dumps(probes[int(self.path.rsplit("/", 1)[-1])][1]).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, _format: str, *args: object) -> None:
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        result = run_collection(
            collection(cases, resource("checks.js")),
            f"http://127.0.0.1:{server.server_port}",
            request.config.rootpath / "artifacts" / "postman-parity",
        )
        output = result.stdout_path.read_text(encoding="utf-8")
        assert not result.stderr_path.read_text(encoding="utf-8"), output
        assert result.exit_code == (0 if all(probe[3] for probe in probes) else 1), output
        assert re.search(rf"\|\s*requests\s*\|\s*{len(probes)}\s*\|\s*0\s*\|", output)
        assert re.search(rf"\|\s*assertions\s*\|\s*{4 * len(probes)}\s*\|", output)
        sections = re.split(r"^Root ", output, flags=re.MULTILINE)[1:]
        assert len(sections) == len(probes)
        for section, (name, _payload, _expected, valid) in zip(sections, probes, strict=True):
            assert section.splitlines()[0].strip() == name
            for assertion in ("status", "media-type"):
                assert re.search(rf"^\s*Pass\s+{assertion}\s*$", section, re.MULTILINE), name
            assert bool(re.search(r"^\s*Pass\s+schema\s*$", section, re.MULTILINE)) is valid, name
            if valid:
                assert re.search(r"^\s*Pass\s+known-values\s*$", section, re.MULTILINE), name
            else:
                assert re.search(r"^\s*\d+\.\s+schema\s*$", section, re.MULTILINE), name
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        assert not thread.is_alive()


@pytest.mark.parametrize("field", ["sku", "name", "message"])
def test_postman_nonblank_matches_python_contract(
    field: str, request: pytest.FixtureRequest,
) -> None:
    kind = "error" if field == "message" else "product"
    reference = json.loads(resource("requests.json"))[5 if kind == "error" else 0]["expected"]["value"]
    whitespace = [
        *range(0x09, 0x0E), *range(0x1C, 0x21), 0x85, 0xA0, 0x1680,
        *range(0x2000, 0x200B), 0x2028, 0x2029, 0x202F, 0x205F, 0x3000,
    ]
    assert whitespace == [code for code in range(0x110000) if chr(code).isspace()]
    strings = [(f"blank-{code:04x}", chr(code), False) for code in whitespace]
    strings += [
        ("empty", "", False),
        ("mixed-blank", " \t\u0085\u3000", False),
        ("bom", "\ufeff", True),
        ("zero-width-space", "\u200b", True),
        ("mongolian-vowel-separator", "\u180e", True),
        ("before-controls", "\u001b", True),
        ("after-controls", "\u0021", True),
        ("padded-ascii", "\u0085x\u3000", True),
        ("padded-unicode", "\u0085\u00e9\u3000", True),
        ("supplementary", "\U0001f600", True),
    ]
    probes = []
    for name, text, valid in strings:
        payload = deepcopy(reference)
        target = payload["error"] if kind == "error" else payload
        target[field] = text
        probes.append((name, payload, payload, valid))
    verify_schema_probes(kind, probes, request)


@pytest.mark.parametrize("kind", ["list", "error"])
def test_postman_list_and_error_schema_boundaries(
    kind: str, request: pytest.FixtureRequest,
) -> None:
    reference = json.loads(resource("requests.json"))[2 if kind == "list" else 5]["expected"]["value"]
    probes = [
        ("valid-reference", reference, reference, True),
        ("null-response", None, reference, False),
        ("wrong-envelope", {"items": reference} if kind == "list" else [reference], reference, False),
    ]
    if kind == "list":
        additive = [{**value, "category": "DEMO"} for value in reference]
        probes.extend([
            ("empty-list", [], [], True),
            ("additive-items", additive, reference, True),
            ("null-item", [None], reference, False),
            ("array-item", [[]], reference, False),
            ("string-item", ["product"], reference, False),
            ("missing-id", [{key: value for key, value in reference[0].items() if key != "id"}],
             reference, False),
            ("wrong-price-type", [{**reference[0], "price_cents": True}], reference, False),
            ("invalid-second-item", [reference[0], {**reference[1], "available": "false"}],
             reference, False),
            ("whitespace-only-sku", [{**reference[0], "sku": "\u0085"}], reference, False),
            ("bom-sku", [{**reference[0], "sku": "\ufeff"}],
             [{**reference[0], "sku": "\ufeff"}], True),
        ])
    else:
        additive = {**reference, "trace": "synthetic",
                    "error": {**reference["error"], "detail": "synthetic"}}
        probes.extend([
            ("additive-envelope-and-error", additive, reference, True),
            ("missing-error", {}, reference, False),
            ("null-error", {"error": None}, reference, False),
            ("array-error", {"error": []}, reference, False),
            ("string-error", {"error": "failure"}, reference, False),
        ])
        for field in ("code", "message"):
            probes.append((f"missing-{field}", {"error": {
                key: value for key, value in reference["error"].items() if key != field
            }}, reference, False))
        for name, code in (("unknown-code", "UNKNOWN"), ("numeric-code", 404), ("null-code", None)):
            probes.append((name, {"error": {**reference["error"], "code": code}}, reference, False))
        for name, message in (
            ("empty-message", ""), ("blank-message", " \t\n"), ("numeric-message", 404),
            ("null-message", None), ("array-message", []),
        ):
            probes.append((name, {"error": {**reference["error"], "message": message}}, reference, False))
    verify_schema_probes(kind, probes, request)


@pytest.mark.parametrize("url", [
    "https://example.com", "http://localhost:8001", "http://127.0.0.1",
    "http://user:password@127.0.0.1:8001", "http://127.0.0.1:8001/path",
    "http://127.0.0.1:8001?query=1", "http://127.0.0.1:99999",
])
def test_nonlocal_or_ambiguous_url_is_rejected(tmp_path: Path, url: str) -> None:
    with pytest.raises(PostmanError, match="127.0.0.1"):
        run_collection({}, url, tmp_path)


def test_connection_failure_is_not_contract_success(tmp_path: Path) -> None:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        url = f"http://127.0.0.1:{listener.getsockname()[1]}"
        result = run_collection(
            collection(json.loads(resource("requests.json"))[:1], resource("checks.js")),
            url, tmp_path,
        )
    assert result.exit_code == 1
    assert "ECONNREFUSED" in result.stdout_path.read_text(encoding="utf-8")


def test_cli_version_mismatch_is_explicit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("postman.runner.cli_path", lambda: Path(sys.executable))
    monkeypatch.setattr("postman.runner.subprocess.run", lambda *_args, **_kwargs: subprocess.CompletedProcess(
        [], 0, stdout="0.0.0\n", stderr="",
    ))
    with pytest.raises(PostmanError, match="Expected pinned"):
        run_collection({}, "http://127.0.0.1:8001", tmp_path)
    assert not (tmp_path / "postman").exists()


def test_owned_cli_timeout_stops_process(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("postman.runner.cli_path", lambda: Path(sys.executable))
    original = subprocess.Popen
    owned = []

    def sleeping_process(_arguments: list[str], **kwargs: object) -> subprocess.Popen:
        process = original([sys.executable, "-c", "import time; time.sleep(60)"], **kwargs)
        owned.append(process)
        return process

    monkeypatch.setattr("postman.runner.subprocess", SimpleNamespace(
        run=lambda *_args, **_kwargs: subprocess.CompletedProcess(
            [], 0, stdout="1.71.0\n", stderr="",
        ),
        Popen=sleeping_process, TimeoutExpired=subprocess.TimeoutExpired,
    ))
    with pytest.raises(PostmanError, match="timed out"):
        run_collection({}, "http://127.0.0.1:8001", tmp_path, timeout=0.1)
    assert len(owned) == 1 and owned[0].poll() is not None
