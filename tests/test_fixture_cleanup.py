import hashlib
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def test_fixture_cleanup_after_assertion_failure(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    xml = tmp_path / "probe.xml"
    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(root / "tests" / "fixture_failure_probe.py"),
         "--junitxml", str(xml), "--tb=short"],
        cwd=root, capture_output=True, text=True, timeout=20,
    )
    assert result.returncode == 1, result.stdout + result.stderr
    suite = ET.parse(xml).getroot().find("testsuite")
    assert suite is not None
    assert suite.attrib["tests"] == "1"
    assert suite.attrib["failures"] == "1"
    assert suite.attrib["errors"] == "0"
    assert suite.attrib["skipped"] == "0"
    failure = suite.find("testcase/failure")
    assert failure is not None
    assert "M1_FIXTURE_FAILURE_PROBE" in failure.attrib["message"]
    identity = hashlib.sha256(
        b"tests/fixture_failure_probe.py::test_owned_server_cleanup_after_failure"
    ).hexdigest()[:16]
    events = [
        json.loads(line) for line in
        (root / "artifacts" / "lifecycle" / f"{identity}.jsonl").read_text().splitlines()
    ]
    assert [event["event"] for event in events] == ["app_starting", "app_ready", "app_stopped"]
