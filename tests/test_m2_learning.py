import json
import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from practice_runner.engine import PracticeError, Session, asset, create_attempt, statistics
from practice_runner.exercise import check_code
from practice_runner.m2 import M2Session, create_m2_attempt, manifest
from practice_runner.models import Attempt, M2_CHECKS, M2_TRACK, M2Variant, digest
from practice_runner.storage import Store, StorageError


def session_at(root: Path, lab: int | None = None, seed: int = 42) -> M2Session:
    store = Store(root)
    return M2Session(store, create_m2_attempt(store, seed, lab))


def write_solution(session: M2Session, lab: str) -> None:
    path = session.store.directory(session.record.attempt_id) / "work" / f"lab{lab}.py"
    path.write_text(asset(f"lab{lab}-solution"), encoding="utf-8")


def complete(session: M2Session) -> None:
    assert isinstance(session.record.variant, M2Variant)
    for lab, spec in session.record.variant.labs.items():
        session.submit(f"{lab}.prediction", spec.correct)
        session.submit(f"{lab}.explanation", "Synthetic explanation for manual rubric review.")
        write_solution(session, lab)
        assert session.submit(f"{lab}.code").outcome == "passed"
    session.finish()


@pytest.mark.parametrize("lab", [2, 3, 4, 5])
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
    second = create_m2_attempt(first.store, 42)
    assert second.events == []
    assert second.variant == first.record.variant
    assert second.attempt_id != first.record.attempt_id
    assert second.scope == "full" and len(second.tasks) == 12
    assert second.record_schema_version == 2
    assert first.store.load(first.record.attempt_id).model_dump() == saved
    assert first.record.score() == first.record.score(first=True) == 100
    work = first.store.directory(second.attempt_id) / "work"
    assert len(list(work.glob("*.py"))) == 4
    assert (work / "lab3.py").read_text() == asset("lab3-starter")


@pytest.mark.parametrize("lab", [2, 3, 4, 5])
def test_scope_variant_matches_full_seed(tmp_path: Path, lab: int) -> None:
    full = create_m2_attempt(Store(tmp_path / "full"), 17)
    focused = create_m2_attempt(Store(tmp_path / "focused"), 17, lab)
    assert isinstance(full.variant, M2Variant) and isinstance(focused.variant, M2Variant)
    assert focused.variant.labs[str(lab)] == full.variant.labs[str(lab)]
    assert focused.scope == f"lab-{lab}"
    assert focused.tasks == [f"{lab}.{kind}" for kind in ("prediction", "explanation", "code")]
    assert len(list((Store(tmp_path / "focused").directory(focused.attempt_id) / "work").glob("*.py"))) == 1


def test_deterministic_variants_offer_different_reasoning(tmp_path: Path) -> None:
    prompts = set()
    for seed in range(8):
        record = create_m2_attempt(Store(tmp_path), seed, 3)
        assert isinstance(record.variant, M2Variant)
        prompts.add(record.variant.labs["3"].correct)
    assert prompts == {"required", "type", "minimum"}


def test_first_final_rechecks_and_assistance(tmp_path: Path) -> None:
    session = session_at(tmp_path, 2)
    assert isinstance(session.record.variant, M2Variant)
    spec = session.record.variant.labs["2"]
    with pytest.raises(PracticeError, match="submission"):
        session.assistance("2.code", True)
    session.submit("2.prediction", next(choice for choice in spec.choices if choice != spec.correct))
    session.submit("2.prediction", spec.correct)
    session.submit("2.explanation", "Structural validity is distinct from an independent price.")
    assert session.submit("2.code").outcome == "learner_failure"
    assert session.assistance("2.code", True) == asset("lab2-solution")
    write_solution(session, "2")
    assert session.submit("2.code").outcome == "passed"
    assert session.submit("2.code").kind == "check"
    session.finish()
    assert session.record.score(first=True) == 0
    assert session.record.score() == 100
    group = statistics([session.record])[0]
    assert group["unassisted_count"] == 0
    assert group["failed_code_checks"] == 1
    assert group["topics"]["2.prediction"] == {
        "first_answered": 1, "first_correct": 0, "final_correct": 1,
    }


def test_infrastructure_recheck_does_not_reuse_pass(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    session = session_at(tmp_path, 3)
    write_solution(session, "3")
    session.submit("3.code")
    monkeypatch.setattr("practice_runner.m2.check_code", lambda *_args, **_kwargs: {
        "outcome": "infrastructure_error", "feedback": "SYNTHETIC_FAILURE",
        "checks": {}, "exit_code": 2,
    })
    with pytest.raises(PracticeError, match="SYNTHETIC_FAILURE"):
        session.submit("3.code")
    saved = session.store.load(session.record.attempt_id)
    assert saved.status == "errored"
    assert saved.events[-1].kind == "check"
    assert saved.score() == 0
    assert statistics([saved])[0]["scored_count"] == 0


def test_invalid_actions_pause_and_missing_completion(tmp_path: Path) -> None:
    session = session_at(tmp_path, 4)
    with pytest.raises(PracticeError, match="every"):
        session.finish()
    for task, answer in (("4.prediction", "500"), ("4.explanation", " "), ("2.code", "")):
        with pytest.raises(PracticeError):
            session.submit(task, answer)
    assert not session.record.events
    session.pause()
    with pytest.raises(PracticeError, match="Resume"):
        session.submit("4.code")
    session.resume()
    session.finish("abandoned")
    assert statistics([session.record])[0]["completed"] == 0


@pytest.mark.parametrize("change", ["scope", "track", "schema", "digest", "prediction", "check-source"])
def test_corrupt_m2_record_is_rejected(tmp_path: Path, change: str) -> None:
    session = session_at(tmp_path, 5)
    complete(session)
    data = session.record.model_dump()
    if change == "scope":
        data["scope"] = "full"
    elif change == "track":
        data["track"] = "api-foundations-m1b"
    elif change == "schema":
        data["record_schema_version"] = 1
    elif change == "digest":
        data["variant"]["labs"]["5"]["prediction"] = "Rewritten"
    elif change == "prediction":
        data["events"][0]["outcome"] = "learner_failure"
    else:
        event = dict(data["events"][-1])
        event.update(kind="check", sequence=len(data["events"]) + 1, answer="# changed")
        event["source_digest"] = digest(event["answer"])
        data["events"].append(event)
    with pytest.raises(ValidationError):
        Attempt.model_validate(data)


def test_statistics_versions_scopes_and_old_history(tmp_path: Path) -> None:
    old_store = Store(tmp_path / "old")
    old = Session(old_store, create_attempt(old_store, 42, "prediction"))
    old.submit("prediction", "404")
    old.finish()
    old_json = old.record.model_dump_json()
    focused = session_at(tmp_path / "new", 2)
    complete(focused)
    full = session_at(tmp_path / "full")
    full.finish("abandoned")
    groups = statistics([old.record, focused.record, full.record])
    assert len(groups) == 3
    assert {group["scope"] for group in groups} == {"prediction", "lab-2", "full"}
    assert Attempt.model_validate_json(old_json).model_dump_json() == old_json
    assert manifest().track == M2_TRACK


def test_cli_track_lab_history_stats_and_eof(tmp_path: Path) -> None:
    command = [sys.executable, "-m", "practice_runner", "--data-dir", str(tmp_path)]
    result = subprocess.run(
        [*command, "start", "--track", M2_TRACK, "--lab", "4", "--seed", "42"],
        input="submit 4.prediction 404\nsubmit 4.explanation Expected rejection is not a network failure.\n"
              "submit 4.code\ncomplete\n",
        capture_output=True, text=True, timeout=15,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    records, errors = Store(tmp_path).history()
    assert not errors and len(records) == 1
    record = records[0]
    assert record.status == "completed" and record.score() == 50
    assert "4.code:" in result.stdout and "lab4.py" in result.stdout
    for arguments in (["review", record.attempt_id], ["history"], ["stats", "--track", M2_TRACK]):
        response = subprocess.run([*command, *arguments], capture_output=True, text=True, timeout=15)
        assert response.returncode == 0, response.stderr
        parsed = json.loads(response.stdout)
        assert parsed
    default_stats = subprocess.run([*command, "stats"], capture_output=True, text=True, timeout=15)
    assert json.loads(default_stats.stdout) == []
    abandoned = subprocess.run(
        [*command, "start", "--track", M2_TRACK, "--lab", "5"],
        input="", capture_output=True, text=True, timeout=15,
    )
    assert abandoned.returncode == 1
    assert not (tmp_path / ".writer-lock.json").exists()


@pytest.mark.parametrize("arguments", [
    ["start", "--lab", "2"], ["start", "--track", M2_TRACK, "--scope", "code"],
    ["start", "--track", M2_TRACK, "--lab", "6"], ["start", "--track", M2_TRACK, "--seed", "-1"],
])
def test_invalid_cli_scope_has_no_attempt(tmp_path: Path, arguments: list[str]) -> None:
    response = subprocess.run(
        [sys.executable, "-m", "practice_runner", "--data-dir", str(tmp_path), *arguments],
        input="", capture_output=True, text=True, timeout=15,
    )
    assert response.returncode == 2
    assert Store(tmp_path).history() == ([], [])
    assert not (tmp_path / ".writer-lock.json").exists()


def test_m2_workspace_path_boundary_preserved(tmp_path: Path) -> None:
    session = session_at(tmp_path, 2)
    from practice_runner.storage import safe_path
    with pytest.raises(StorageError):
        session.store.directory("../outside")
    assert safe_path(session.store.directory(session.record.attempt_id), "work", "lab2.py").exists()


@pytest.mark.parametrize("lab,source", [
    (2, "def check_response(status, payload, expected):\n    assert payload['price_cents'] == expected\n"),
    (3, "def check_response(status, payload, expected):\n    assert type(payload['price_cents']) is int\n    assert payload['price_cents'] >= 0\n"),
    (4, "def check_response(status, payload, expected):\n    assert status == expected['status']\n    assert payload['error']['code'] == expected['code']\n"),
    (5, "def compatible(payload, version):\n    from contracts.compatibility import consumer\n    return not any(consumer('v1' if version == 'v3' else version).iter_errors(payload))\n"),
])
def test_shortcuts_do_not_earn_code_credit(tmp_path: Path, lab: int, source: str) -> None:
    result = check_code(tmp_path, source, 123, lab=lab)
    assert result["outcome"] != "passed", result


def test_full_installed_cli_reference_completion(tmp_path: Path) -> None:
    process = subprocess.Popen(
        [sys.executable, "-u", "-m", "practice_runner", "--data-dir", str(tmp_path),
         "start", "--track", M2_TRACK, "--seed", "42"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    try:
        assert process.stdout is not None and process.stdin is not None
        preamble = []
        for _ in range(20):
            line = process.stdout.readline()
            assert line, "CLI exited before printing workspace/task instructions"
            preamble.append(line)
            if "null score means N/A" in line:
                break
        else:
            pytest.fail("CLI instructions not found")
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
        saved = Store(tmp_path).load(record.attempt_id)
        assert saved.status == "completed"
        assert len(saved.events) == 12
        assert saved.score(first=True) == saved.score() == 100
        assert all(saved.results(f"{lab}.code")[-1].exit_code == 0 for lab in record.variant.labs)
        assert not (tmp_path / ".writer-lock.json").exists()
    finally:
        if process.poll() is None:
            process.kill()
            process.communicate(timeout=5)


def test_m2_exact_average_and_pause_duration(tmp_path: Path) -> None:
    clock = [0.0]
    store = Store(tmp_path)
    first = M2Session(store, create_m2_attempt(store, 42, 2), clock=lambda: clock[0])
    assert isinstance(first.record.variant, M2Variant)
    spec = first.record.variant.labs["2"]
    clock[0] = 10
    first.pause()
    clock[0] = 100
    first.resume()
    clock[0] = 110
    first.submit("2.prediction", spec.correct)
    first.submit("2.explanation", "Synthetic explanation.")
    first.submit("2.code")
    first.finish()
    assert first.record.practice_seconds == 20
    assert first.record.score() == 50
    second = M2Session(store, create_m2_attempt(store, 42, 2), clock=lambda: clock[0])
    clock[0] = 150
    complete(second)
    group = statistics([first.record, second.record])[0]
    assert group["completed"] == group["scored_count"] == group["timed_count"] == 2
    assert group["mean_final_score"] == group["mean_first_score"] == 75
    assert group["mean_practice_seconds"] == 30


def test_m2_workspace_failure_is_saved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def missing_asset(_name: str) -> str:
        raise OSError("SYNTHETIC_ASSET_FAILURE")

    monkeypatch.setattr("practice_runner.m2.asset", missing_asset)
    store = Store(tmp_path)
    with pytest.raises(StorageError, match="SYNTHETIC_ASSET_FAILURE"):
        create_m2_attempt(store, 42, 2)
    records, errors = store.history()
    assert not errors and len(records) == 1
    assert records[0].status == "errored"
    assert statistics(records)[0]["completed"] == 0


def test_m2_corrupt_history_reports_incomplete_summary(tmp_path: Path) -> None:
    session = session_at(tmp_path, 2)
    session.finish("abandoned")
    path = session.store.directory(session.record.attempt_id) / "attempt.json"
    data = session.record.model_dump()
    data["checker_version"] = "99"
    path.write_text(json.dumps(data), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-m", "practice_runner", "--data-dir", str(tmp_path),
         "stats", "--track", M2_TRACK],
        capture_output=True, text=True, timeout=15,
    )
    assert result.returncode == 2
    assert "INCOMPLETE SUMMARY" in result.stderr
    assert json.loads(result.stdout) == []
