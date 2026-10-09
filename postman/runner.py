import json
import os
import platform
import subprocess
import uuid
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from urllib.parse import urlsplit

from practice_runner.exercise import stop_owned_process
from practice_runner.storage import safe_path

CLI_VERSION = "1.71.0"


class PostmanError(Exception):
    pass


@dataclass(frozen=True)
class RunResult:
    exit_code: int
    stdout_path: Path
    stderr_path: Path
    collection_path: Path


def resource(name: str) -> str:
    return files("postman").joinpath(name).read_text(encoding="utf-8")


def cli_path() -> Path:
    explicit = os.environ.get("CATALOG_POSTMAN_CLI")
    system = platform.system()
    machine = platform.machine().lower()
    architecture = "arm64" if machine in ("arm64", "aarch64") else "x64"
    package = {"Windows": "windows", "Linux": "linux", "Darwin": "macos"}.get(system)
    if explicit:
        path = Path(explicit)
    elif package:
        path = (
            Path.cwd() / "node_modules" / "@postman" / f"pm-bin-{package}-{architecture}"
            / "bin" / ("postman.exe" if system == "Windows" else "postman")
        )
    else:
        raise PostmanError(f"Unsupported CLI platform: {system}; set CATALOG_POSTMAN_CLI explicitly")
    if not path.is_file():
        raise PostmanError(
            "Postman CLI unavailable. Run npm ci in this repository. Outside checkout set "
            "CATALOG_POSTMAN_CLI to its pinned postman executable. No login/API key is required."
        )
    return path.resolve()


def collection(cases: list[dict], source: str) -> dict:
    return {
        "info": {
            "name": "Synthetic Catalog Critical Contracts",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        },
        "variable": [{"key": "base_url", "value": "http://127.0.0.1:8001"}],
        "event": [{"listen": "test", "script": {"type": "text/javascript", "exec": source.split("\n")}}],
        "item": [{
            "name": case["name"],
            "request": {"method": "GET", "url": "{{base_url}}" + case["path"]},
            "event": [{
                "listen": "prerequest", "script": {"type": "text/javascript", "exec": [
                    "pm.variables.set('expected', "
                    + json.dumps(json.dumps(case["expected"], separators=(",", ":"))) + ");",
                ]},
            }],
        } for case in cases],
    }


def run_collection(
    content: dict, base_url: str, folder: Path, timeout: float = 30,
) -> RunResult:
    try:
        url = urlsplit(base_url)
        if (
            url.scheme != "http" or url.hostname != "127.0.0.1"
            or url.port is None or not 1 <= url.port <= 65535
            or url.username is not None or url.password is not None
            or url.path not in ("", "/") or url.query or url.fragment
        ):
            raise ValueError("Not an explicit localhost base URL")
    except ValueError as error:
        raise PostmanError("Use http://127.0.0.1:<port> for the synthetic target") from error
    executable = cli_path()
    try:
        version = subprocess.run(
            [str(executable), "--version"], capture_output=True, text=True, timeout=5, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise PostmanError(f"Unable to inspect Postman CLI version: {error}") from error
    if version.returncode != 0 or version.stdout.strip() != CLI_VERSION:
        raise PostmanError(f"Expected pinned Postman CLI {CLI_VERSION}; got {version.stdout.strip()!r}")
    evidence = safe_path(folder, "postman", uuid.uuid4().hex)
    evidence.mkdir(parents=True, exist_ok=False)
    snapshot = safe_path(evidence, "collection.json")
    snapshot.write_text(json.dumps(content, indent=2), encoding="utf-8")
    stdout_path, stderr_path = safe_path(evidence, "stdout.txt"), safe_path(evidence, "stderr.txt")
    environment = dict(os.environ)
    for name in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"):
        environment.pop(name, None)
    environment.update(NO_PROXY="127.0.0.1", no_proxy="127.0.0.1")
    with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        try:
            process = subprocess.Popen(
                [
                    str(executable), "collection", "run", str(snapshot),
                    "--env-var", f"base_url={base_url.rstrip('/')}",
                    "--no-report-events", "--disable-unicode", "--ignore-redirects",
                    "--timeout", "20000", "--timeout-request", "2000",
                    "--timeout-script", "2000", "--no-insecure-file-read",
                    "--working-dir", str(evidence),
                ],
                cwd=evidence, env=environment, stdout=stdout, stderr=stderr,
                start_new_session=os.name != "nt",
            )
        except OSError as error:
            raise PostmanError(f"Cannot start Postman CLI: {error}") from error
        try:
            process.wait(timeout=timeout)
        except subprocess.TimeoutExpired as error:
            stop_owned_process(process)
            raise PostmanError("Postman run timed out; owned process stopped. Inspect raw evidence.") from error
        except BaseException:
            stop_owned_process(process)
            raise
    if process.returncode not in (0, 1):
        raise PostmanError(f"Postman process failure (exit {process.returncode}); inspect {stderr_path}")
    return RunResult(process.returncode, stdout_path, stderr_path, snapshot)
