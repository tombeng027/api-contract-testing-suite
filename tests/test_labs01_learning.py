import json
import subprocess
import sys
import time
from pathlib import Path

import pytest
from pydantic import ValidationError

from practice_runner.engine import PracticeError, asset, statistics
from practice_runner.exercise import check_code
from practice_runner.labs01 import Labs01Session, create_labs01_attempt, labs01_manifest
from practice_runner.labs01_checks import check_lab01
from practice_runner.m2 import create_m2_attempt
from practice_runner.models import Attempt, L01_TRACK, M2_CHECKS, M2_TRACK, M2Variant, digest
from practice_runner.storage import Store, StorageError


def session_at(root: Path, lab: int | None = None, seed: int = 42) -> Labs01Session:
    store = Store(root)
    return Labs01Session(store, create_labs01_attempt(store, seed, lab))


def write_solution(session: Labs01Session, lab: str) -> None:
    path = session.store.directory(session.record.attempt_id) / "work" / f"lab{lab}.py"
    path.write_text(asset(f"lab{lab}-solution"), encoding="utf-8")


def complete(session: Labs01Session) -> None:
    assert isinstance(session.record.variant, M2Variant)
    for lab, spec in session.record.variant.labs.items():
        session.submit(f"{lab}.prediction", spec.correct)
        session.submit(f"{lab}.explanation", "Synthetic explanation for manual rubric review.")
        write_solution(session, lab)
        assert session.submit(f"{lab}.code").outcome == "passed"
    session.finish()


def labs01_cli_workspace_ready(root: Path, labs: tuple[int, ...] = (0, 1)) -> bool:
    folders = list((root / "attempts").glob("*"))
    return len(folders) == 1 and (folders[0] / "attempt.json").is_file() and all(
        (folders[0] / "work" / f"lab{lab}.py").is_file() for lab in labs
    )


@pytest.mark.parametrize("lab", [0, 1])
def test_starters_fail_and_solutions_pass(tmp_path: Path, lab: int) -> None:
    starter = check_code(tmp_path, asset(f"lab{lab}-starter"), 1937, lab=lab)
    assert starter["outcome"] == "learner_failure"
    solution = check_code(tmp_path, asset(f"lab{lab}-solution"), 1937, lab=lab)
    assert solution["outcome"] == "passed", solution
    assert solution["checks"] == {name: True for name in M2_CHECKS}


def test_full_track_fresh_reset_and_history(tmp_path: Path) -> None:
    first = session_at(tmp_path)
    complete(first)
    saved = first.store.load(first.record.attempt_id).model_dump()
    second = create_labs01_attempt(first.store, 42)
    assert second.events == []
    assert second.variant == first.record.variant
    assert second.attempt_id != first.record.attempt_id
    assert second.scope == "full" and len(second.tasks) == 6
    assert second.record_schema_version == 2
    assert second.track == L01_TRACK
    assert first.store.load(first.record.attempt_id).model_dump() == saved
    assert first.record.score() == first.record.score(first=True) == 100
    group = statistics([first.record])[0]
    assert group["prediction_first_answered"] == group["prediction_first_correct"] == 2
    work = first.store.directory(second.attempt_id) / "work"
    assert len(list(work.glob("*.py"))) == 2
    assert (work / "lab0.py").read_text() == asset("lab0-starter")
    assert (work / "lab1.py").read_text() == asset("lab1-starter")


@pytest.mark.parametrize("lab", [0, 1])
def test_scope_variant_matches_full_seed(tmp_path: Path, lab: int) -> None:
    full = create_labs01_attempt(Store(tmp_path / "full"), 17)
    focused = create_labs01_attempt(Store(tmp_path / "focused"), 17, lab)
    assert isinstance(full.variant, M2Variant) and isinstance(focused.variant, M2Variant)
    assert focused.variant.labs[str(lab)] == full.variant.labs[str(lab)]
    assert focused.scope == f"lab-{lab}"
    assert focused.tasks == [f"{lab}.{kind}" for kind in ("prediction", "explanation", "code")]
    assert len(list((Store(tmp_path / "focused").directory(focused.attempt_id) / "work").glob("*.py"))) == 1


def test_deterministic_variants_offer_different_reasoning(tmp_path: Path) -> None:
    lab0, lab1 = set(), set()
    for seed in range(12):
        record = create_labs01_attempt(Store(tmp_path), seed)
        assert isinstance(record.variant, M2Variant)
        lab0.add(record.variant.labs["0"].correct)
        lab1.add(record.variant.labs["1"].correct)
    assert lab0 == {"status", "schema", "price"}
    assert lab1 == {"200", "404", "422"}


def test_first_final_rechecks_and_assistance(tmp_path: Path) -> None:
    session = session_at(tmp_path, 0)
    assert isinstance(session.record.variant, M2Variant)
    spec = session.record.variant.labs["0"]
    with pytest.raises(PracticeError, match="submission"):
        session.assistance("0.code", True)
    session.submit("0.prediction", next(choice for choice in spec.choices if choice != spec.correct))
    session.submit("0.prediction", spec.correct)
    session.submit("0.explanation", "Assertion order decides which failure is reported first.")
    assert session.submit("0.code").outcome == "learner_failure"
    assert session.assistance("0.code", True) == asset("lab0-solution")
    write_solution(session, "0")
    assert session.submit("0.code").outcome == "passed"
    assert session.submit("0.code").kind == "check"
    session.finish()
    assert session.record.score(first=True) == 0
    assert session.record.score() == 100
    group = statistics([session.record])[0]
    assert group["unassisted_count"] == 0
    assert group["failed_code_checks"] == 1
    assert group["topics"]["0.prediction"] == {
        "first_answered": 1, "first_correct": 0, "final_correct": 1,
    }


@pytest.mark.parametrize("change", ["scope", "track", "version", "digest"])
def test_corrupt_labs01_record_is_rejected(tmp_path: Path, change: str) -> None:
    session = session_at(tmp_path, 1)
    complete(session)
    data = session.record.model_dump()
    if change == "scope":
        data["scope"] = "full"
    elif change == "track":
        data["track"] = M2_TRACK
    elif change == "version":
        data["assessment_version"] = "2"
        data["checker_version"] = "2"
    else:
        data["variant"]["labs"]["1"]["prediction"] = "Rewritten"
    with pytest.raises(ValidationError):
        Attempt.model_validate(data)


def test_track_statistics_are_separate(tmp_path: Path) -> None:
    labs01 = session_at(tmp_path / "labs01", 1)
    complete(labs01)
    m2 = create_m2_attempt(Store(tmp_path / "m2"), 42, 2)
    groups = statistics([labs01.record, m2])
    assert len(groups) == 2
    assert {group["track"] for group in groups} == {L01_TRACK, M2_TRACK}
    labs01_group = next(group for group in groups if group["track"] == L01_TRACK)
    assert labs01_group["assessment_version"] == "1"
    assert labs01_group["scope"] == "lab-1"
    assert labs01_group["completed"] == 1
    assert labs01_manifest().track == L01_TRACK


@pytest.mark.parametrize("lab,source", [
    (0, "def failing_assertion(status, payload, expected):\n    return None\n"),
    (0, "def failing_assertion(status, payload, expected):\n    return 'price'\n"),
    (0, "def failing_assertion(status, payload, expected):\n    return True\n"),
    (1, "def expected_status(product_id, filters, known_ids):\n    return 422\n"),
    (1, "def expected_status(product_id, filters, known_ids):\n    return 200\n"),
    (1, "def expected_status(product_id, filters, known_ids):\n    return True\n"),
])
def test_shortcuts_do_not_earn_code_credit(tmp_path: Path, lab: int, source: str) -> None:
    result = check_code(tmp_path, source, 2500, lab=lab)
    assert result["outcome"] == "learner_failure", result


@pytest.mark.parametrize("lab,source", [
    # Checking structure after the business value inverts the documented order.
    (0, "def failing_assertion(status, payload, expected):\n"
        "    if status != 200:\n        return 'status'\n"
        "    if payload.get('price_cents') != expected:\n        return 'price'\n"
        "    if any(f not in payload for f in ('id', 'sku', 'name', 'price_cents', 'available')):\n"
        "        return 'schema'\n"
        "    return None\n"),
    # Ignoring duplicate filters accepts a documented rejection.
    (1, "def expected_status(product_id, filters, known_ids):\n"
        "    if product_id is not None:\n"
        "        if type(product_id) is not int or product_id <= 0:\n            return 422\n"
        "        return 200 if product_id in known_ids else 404\n"
        "    for name, value in filters:\n"
        "        if name != 'available' or value not in ('true', 'false'):\n            return 422\n"
        "    return 200\n"),
])
def test_review_false_pass_regressions(tmp_path: Path, lab: int, source: str) -> None:
    result = check_code(tmp_path, source, 2500, lab=lab)
    assert result["outcome"] == "learner_failure", result


def test_lab0_status_is_checked_before_structure() -> None:
    def structure_first(status: int, payload: object, expected: int) -> object:
        if not isinstance(payload, dict) or "price_cents" not in payload:
            return "schema"
        if status != 200:
            return "status"
        return None

    checks = {check["name"]: check["passed"] for check in check_lab01(structure_first, 0, 2500)}
    assert checks["wrong-type"] is False


def test_lab1_bool_id_is_invalid_input() -> None:
    def truthy(product_id: object, filters: object, known_ids: object) -> int:
        if product_id is None:
            return 200
        return 200 if product_id in known_ids else 404  # type: ignore[operator]

    checks = {check["name"]: check["passed"] for check in check_lab01(truthy, 1, 2500)}
    assert checks["wrong-type"] is False


def test_cli_track_lab_history_stats_and_eof(tmp_path: Path) -> None:
    probe = create_labs01_attempt(Store(tmp_path / "probe"), 42, 1)
    assert isinstance(probe.variant, M2Variant)
    correct = probe.variant.labs["1"].correct
    command = [sys.executable, "-m", "practice_runner", "--data-dir", str(tmp_path / "cli")]
    result = subprocess.run(
        [*command, "start", "--track", L01_TRACK, "--lab", "1", "--seed", "42"],
        input=f"submit 1.prediction {correct}\n"
              "submit 1.explanation A missing valid ID is not the same as invalid input.\n"
              "submit 1.code\ncomplete\n",
        capture_output=True, text=True, timeout=15,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    records, errors = Store(tmp_path / "cli").history()
    assert not errors and len(records) == 1
    record = records[0]
    assert record.status == "completed" and record.score() == 50
    assert "1.code:" in result.stdout and "lab1.py" in result.stdout
    for arguments in (["review", record.attempt_id], ["history"], ["stats", "--track", L01_TRACK]):
        response = subprocess.run([*command, *arguments], capture_output=True, text=True, timeout=15)
        assert response.returncode == 0, response.stderr
        assert json.loads(response.stdout)
    default_stats = subprocess.run([*command, "stats"], capture_output=True, text=True, timeout=15)
    assert json.loads(default_stats.stdout) == []
    abandoned = subprocess.run(
        [*command, "start", "--track", L01_TRACK, "--lab", "0"],
        input="", capture_output=True, text=True, timeout=15,
    )
    assert abandoned.returncode == 1
    assert not (tmp_path / "cli" / ".writer-lock.json").exists()


@pytest.mark.parametrize("arguments", [
    ["start", "--lab", "0"],
    ["start", "--track", L01_TRACK, "--scope", "code"],
    ["start", "--track", L01_TRACK, "--lab", "2"],
    ["start", "--track", M2_TRACK, "--lab", "0"],
    ["start", "--track", L01_TRACK, "--seed", "-1"],
])
def test_invalid_cli_combination_has_no_attempt(tmp_path: Path, arguments: list[str]) -> None:
    response = subprocess.run(
        [sys.executable, "-m", "practice_runner", "--data-dir", str(tmp_path), *arguments],
        input="", capture_output=True, text=True, timeout=15,
    )
    assert response.returncode == 2
    assert Store(tmp_path).history() == ([], [])
    assert not (tmp_path / ".writer-lock.json").exists()


def test_full_installed_cli_reference_completion(tmp_path: Path) -> None:
    process = subprocess.Popen(
        [sys.executable, "-u", "-m", "practice_runner", "--data-dir", str(tmp_path),
         "start", "--track", L01_TRACK, "--seed", "42"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    try:
        deadline = time.monotonic() + 10
        while process.poll() is None and time.monotonic() < deadline:
            if labs01_cli_workspace_ready(tmp_path):
                break
            time.sleep(0.05)
        else:
            pytest.fail("CLI did not create its full workspace within 10 seconds")
        records, errors = Store(tmp_path).history()
        assert not errors and len(records) == 1
        record = records[0]
        assert isinstance(record.variant, M2Variant)
        commands = []
        for lab, spec in record.variant.labs.items():
            path = Store(tmp_path).directory(record.attempt_id) / "work" / f"lab{lab}.py"
            path.write_text(asset(f"lab{lab}-solution"), encoding="utf-8")
            commands.extend([
                f"submit {lab}.prediction {spec.correct}",
                f"submit {lab}.explanation Synthetic reference-driven verification, not learner achievement.",
                f"submit {lab}.code",
            ])
        stdout, stderr = process.communicate("\n".join([*commands, "complete", ""]), timeout=30)
        assert process.returncode == 0, stdout + stderr
        assert not stderr
        assert "null score means N/A" in stdout and "lab0.py" in stdout and "lab1.py" in stdout
        saved = Store(tmp_path).load(record.attempt_id)
        assert saved.status == "completed"
        assert len(saved.events) == 6
        assert saved.score(first=True) == saved.score() == 100
        assert all(saved.results(f"{lab}.code")[-1].exit_code == 0 for lab in record.variant.labs)
        assert not (tmp_path / ".writer-lock.json").exists()
    finally:
        if process.poll() is None:
            process.kill()
            process.communicate(timeout=5)


def test_labs01_workspace_failure_is_saved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def missing_asset(_name: str) -> str:
        raise OSError("SYNTHETIC_ASSET_FAILURE")

    monkeypatch.setattr("practice_runner.labs01.asset", missing_asset)
    store = Store(tmp_path)
    with pytest.raises(StorageError, match="SYNTHETIC_ASSET_FAILURE"):
        create_labs01_attempt(store, 42, 0)
    records, errors = store.history()
    assert not errors and len(records) == 1
    assert records[0].status == "errored"
    assert statistics(records)[0]["completed"] == 0
