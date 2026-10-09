import json
import os
import signal
import subprocess
import sys
import uuid
from pathlib import Path

from practice_runner.storage import StorageError, safe_path
from practice_runner.models import M2_CHECKS

OUTPUT_LIMIT = 4096


def stop_owned_process(process: subprocess.Popen[bytes]) -> None:
    if os.name == "nt":
        stopped = subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            capture_output=True, timeout=5, check=False,
        )
        if stopped.returncode != 0 and process.poll() is None:
            raise StorageError("Failed to stop timed-out exercise process tree")
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    process.wait(timeout=5)


def check_code(
    folder: Path, source: str, price: int, timeout: float = 5, *, lab: int | None = None
) -> dict[str, object]:
    if lab is not None and lab not in (2, 3, 4, 5):
        raise ValueError(f"Unknown lab: {lab}")
    evidence = safe_path(folder, "evidence", uuid.uuid4().hex)
    evidence.mkdir(parents=True, exist_ok=False)
    snapshot = safe_path(evidence, "submission.py")
    snapshot.write_text(source, encoding="utf-8")
    result_path = safe_path(evidence, "result.json")
    stdout_path = safe_path(evidence, "stdout.txt")
    stderr_path = safe_path(evidence, "stderr.txt")
    timed_out = False
    worker = Path(__file__).with_name("check_worker.py")
    with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        process = subprocess.Popen(
            [sys.executable, "-I", str(worker), str(snapshot), str(price), str(result_path),
             *([] if lab is None else [str(lab)])],
            cwd=evidence, stdout=stdout, stderr=stderr, start_new_session=os.name != "nt",
        )
        try:
            process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            stop_owned_process(process)
        except BaseException:
            stop_owned_process(process)
            raise

    def output(path: Path) -> tuple[str, bool]:
        with safe_path(evidence, path.name).open("rb") as stream:
            data = stream.read(OUTPUT_LIMIT + 1)
        return data[:OUTPUT_LIMIT].decode("utf-8", errors="replace"), len(data) > OUTPUT_LIMIT

    stdout_text, stdout_cut = output(stdout_path)
    stderr_text, stderr_cut = output(stderr_path)
    common: dict[str, object] = {
        "stdout": stdout_text, "stderr": stderr_text, "truncated": stdout_cut or stderr_cut,
        "exit_code": process.returncode, "checks": {},
    }
    if timed_out or process.returncode != 0 or not result_path.exists():
        return {
            **common, "outcome": "infrastructure_error",
            "feedback": "Exercise timeout/process failure/missing checker result; no credit awarded.",
        }
    try:
        result = json.loads(safe_path(evidence, "result.json").read_text(encoding="utf-8"))
        if (
            not isinstance(result, dict) or result.get("checker_version") != "1"
            or result.get("lab") != lab
            or result.get("outcome") not in ("passed", "learner_failure", "infrastructure_error")
            or not isinstance(result.get("feedback"), str)
            or not isinstance(result.get("checks"), list)
        ):
            raise ValueError("Invalid checker protocol")
        checks = {}
        for item in result["checks"]:
            if (
                not isinstance(item, dict) or not isinstance(item.get("name"), str)
                or type(item.get("passed")) is not bool or item["name"] in checks
            ):
                raise ValueError("Invalid checker evidence")
            checks[item["name"]] = item["passed"]
        names = (
            ("correct", "zero", "wrong-price", "string-price", "boolean-price")
            if lab is None else M2_CHECKS
        )
        if result["outcome"] == "passed" and checks != {name: True for name in names}:
            raise ValueError("Pass missing required checks")
        return {**common, "outcome": result["outcome"], "feedback": result["feedback"], "checks": checks}
    except (ValueError, OSError) as error:
        return {**common, "outcome": "infrastructure_error", "feedback": f"Checker protocol error: {error}"}
