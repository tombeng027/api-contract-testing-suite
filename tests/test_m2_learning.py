import json
import subprocess
import sys
import time
from pathlib import Path

import pytest
from pydantic import ValidationError

from practice_runner.engine import PracticeError, Session, asset, create_attempt, statistics
from practice_runner.exercise import check_code
from practice_runner.m2 import M2Session, create_m2_attempt, manifest
from practice_runner.m2_checks import check_lab
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
    group = statistics([first.record])[0]
    assert group["prediction_first_answered"] == group["prediction_first_correct"] == 4
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
    assert group["prediction_first_answered"] == 1
    assert group["prediction_first_correct"] == 0


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


@pytest.mark.parametrize("lab,source", [
    (2, """def check_response(status, payload, expected):
    assert status == 200
    assert not isinstance(payload["price_cents"], bool)
    assert payload["price_cents"] == expected
"""),
    (3, """from contracts.compatibility import consumer
from copy import deepcopy
from jsonschema import Draft202012Validator
def check_response(status, payload, expected):
    assert status == 200
    schema = deepcopy(consumer("v1").schema)
    schema["additionalProperties"] = False
    assert not list(Draft202012Validator(schema).iter_errors(payload))
"""),
    (5, """def compatible(payload, version):
    if version not in ("v1", "v2"):
        raise ValueError("Unknown version")
    if version == "v1":
        price = payload.get("price_cents")
        return type(price) is int and price >= 0
    price = payload.get("price", {})
    amount = price.get("amount_cents")
    return type(amount) is int and amount == 0 and price.get("currency") == "USD"
"""),
])
def test_review_false_pass_regressions(tmp_path: Path, lab: int, source: str) -> None:
    result = check_code(tmp_path, source, 2500, lab=lab)
    assert result["outcome"] == "learner_failure", result


@pytest.mark.parametrize("version", ["v1", "v2"])
@pytest.mark.parametrize("field,value", [
    ("id", 0), ("id", 2147483648), ("id", True), ("id", "1"), ("id", 1.5),
    ("sku", ""), ("sku", "   "), ("sku", 42),
    ("name", ""), ("name", "   "), ("name", None),
    ("available", "true"), ("available", 0), ("available", None),
])
def test_lab5_detects_ignored_identity_and_availability(
    version: str, field: str, value: object
) -> None:
    from contracts.compatibility import consumer

    def ignores_violation(payload: object, selected: str) -> bool:
        if selected not in ("v1", "v2"):
            raise ValueError("Unknown version")
        if (
            selected == version and isinstance(payload, dict)
            and field in payload and type(payload[field]) is type(value) and payload[field] == value
        ):
            return True
        return not any(consumer(selected).iter_errors(payload))

    assert not all(item["passed"] for item in check_lab(ignores_violation, 5, 2500))


@pytest.mark.parametrize("version", ["v1", "v2"])
@pytest.mark.parametrize("field", ["id", "sku", "name", "available"])
def test_lab5_detects_ignored_required_field(version: str, field: str) -> None:
    from contracts.compatibility import consumer

    def ignores_missing(payload: object, selected: str) -> bool:
        if selected not in ("v1", "v2"):
            raise ValueError("Unknown version")
        if selected == version and isinstance(payload, dict) and field not in payload:
            return True
        return not any(consumer(selected).iter_errors(payload))

    assert not all(item["passed"] for item in check_lab(ignores_missing, 5, 2500))


@pytest.mark.parametrize("case", [
    "v1-zero", "v1-float", "v2-positive", "v2-float", "v2-additive", "false-availability",
])
def test_lab5_detects_rejection_of_valid_payloads(case: str) -> None:
    from contracts.compatibility import consumer

    def rejects_valid(payload: object, version: str) -> bool:
        if version not in ("v1", "v2"):
            raise ValueError("Unknown version")
        if isinstance(payload, dict):
            price = payload.get("price_cents") if version == "v1" else payload.get("price", {})
            reject = (
                (case == "v1-zero" and version == "v1" and price == 0)
                or (case == "v1-float" and version == "v1" and type(price) is float)
                or (case == "false-availability" and payload.get("available") is False)
            )
            if version == "v2" and isinstance(price, dict):
                reject = reject or (
                    (case == "v2-positive" and price.get("amount_cents") == 2500)
                    or (case == "v2-float" and type(price.get("amount_cents")) is float)
                    or (case == "v2-additive" and "metadata" in price)
                )
            if reject:
                return False
        return not any(consumer(version).iter_errors(payload))

    assert not all(item["passed"] for item in check_lab(rejects_valid, 5, 2500))


@pytest.mark.parametrize("lab", [2, 3, 4, 5])
def test_focused_prediction_totals_count_tasks_not_attempts(tmp_path: Path, lab: int) -> None:
    session = session_at(tmp_path, lab)
    complete(session)
    incomplete = create_m2_attempt(session.store, 42, lab)
    group = statistics([session.record, incomplete])[0]
    assert group["started"] == 2 and group["completed"] == 1
    assert group["prediction_first_answered"] == group["prediction_first_correct"] == 1


def legacy_m2(record: Attempt) -> Attempt:
    data = record.model_dump()
    data.update(assessment_version="1", checker_version="1")
    snapshot = {
        "track": data["track"], "assessment": data["assessment_version"],
        "tasks": data["tasks"], "points": data["points"], "variant": data["variant"],
    }
    data["manifest_digest"] = digest(json.dumps(snapshot, sort_keys=True))
    return Attempt.model_validate(data)


def test_m2_versions_preserve_history_and_separate_averages(tmp_path: Path) -> None:
    current = session_at(tmp_path / "current", 2)
    complete(current)
    old = legacy_m2(current.record)
    old_data = old.model_dump()
    old_data["attempt_id"] = "a" * 32
    old = Attempt.model_validate(old_data)
    old_store = Store(tmp_path / "old")
    old_store.save(old)
    path = old_store.directory(old.attempt_id) / "attempt.json"
    original = path.read_bytes()
    loaded = old_store.load(old.attempt_id)
    assert loaded.model_dump() == old.model_dump()
    assert loaded.score() == loaded.score(first=True) == 100
    assert path.read_bytes() == original
    assert current.record.assessment_version == current.record.checker_version == "2"
    assert current.record.content_version == current.record.generator_version == "1"
    evidence = current.store.directory(current.record.attempt_id) / "evidence"
    assert all(json.loads(result.read_text())["checker_version"] == "2"
               for result in evidence.glob("*/result.json"))
    groups = statistics([loaded, current.record])
    assert len(groups) == 2
    assert {group["assessment_version"] for group in groups} == {"1", "2"}
    assert all(group["completed"] == group["scored_count"] == 1 for group in groups)
    assert all(group["prediction_first_answered"] == 1 for group in groups)
    old_store.save(current.record)
    command = [sys.executable, "-m", "practice_runner", "--data-dir", str(old_store.root)]
    review = subprocess.run(
        [*command, "review", old.attempt_id], capture_output=True, text=True, timeout=15,
    )
    assert review.returncode == 0, review.stderr
    reviewed = json.loads(review.stdout)
    assert reviewed["record"] == old.model_dump()
    assert reviewed["summary"]["assessment_version"] == reviewed["summary"]["checker_version"] == "1"
    stats = subprocess.run(
        [*command, "stats", "--track", M2_TRACK], capture_output=True, text=True, timeout=15,
    )
    assert stats.returncode == 0, stats.stderr
    assert json.loads(stats.stdout) == groups
    history = subprocess.run(
        [*command, "history"], capture_output=True, text=True, timeout=15,
    )
    assert history.returncode == 0, history.stderr
    assert {item["assessment_version"] for item in json.loads(history.stdout)} == {"1", "2"}
    assert path.read_bytes() == original


def test_old_m2_session_cannot_use_new_checker(tmp_path: Path) -> None:
    store = Store(tmp_path)
    old = legacy_m2(create_m2_attempt(store, 42, 2))
    session = M2Session(store, old)
    with pytest.raises(PracticeError, match="fresh version-2"):
        session.submit("2.code")
    assert session.record.events == []


@pytest.mark.parametrize("track,assessment,checker", [
    (M2_TRACK, "1", "2"), (M2_TRACK, "2", "1"),
    ("api-foundations-m1b", "2", "2"),
])
def test_invalid_assessment_checker_pair_rejected(
    tmp_path: Path, track: str, assessment: str, checker: str
) -> None:
    store = Store(tmp_path)
    record = create_m2_attempt(store, 42, 2) if track == M2_TRACK else create_attempt(store, 42)
    data = record.model_dump()
    data.update(assessment_version=assessment, checker_version=checker)
    with pytest.raises(ValidationError, match="versions"):
        Attempt.model_validate(data)


def full_cli_workspace_ready(root: Path) -> bool:
    folders = list((root / "attempts").glob("*"))
    return len(folders) == 1 and (folders[0] / "attempt.json").is_file() and all(
        (folders[0] / "work" / f"lab{lab}.py").is_file() for lab in (2, 3, 4, 5)
    )


def test_cli_readiness_does_not_read_provisional_history(tmp_path: Path) -> None:
    record = create_m2_attempt(Store(tmp_path / "source"), 42)
    store = Store(tmp_path / "target")
    assert not full_cli_workspace_ready(store.root)
    folder = store.directory(record.attempt_id)
    folder.mkdir(parents=True)
    assert not full_cli_workspace_ready(store.root)
    store.save(record)
    assert not full_cli_workspace_ready(store.root)
    work = folder / "work"
    work.mkdir()
    for lab in (2, 3, 4):
        (work / f"lab{lab}.py").write_text("# synthetic readiness probe", encoding="utf-8")
        assert not full_cli_workspace_ready(store.root)
    (work / "lab5.py").write_text("# synthetic readiness probe", encoding="utf-8")
    assert full_cli_workspace_ready(store.root)


def test_full_installed_cli_reference_completion(tmp_path: Path) -> None:
    process = subprocess.Popen(
        [sys.executable, "-u", "-m", "practice_runner", "--data-dir", str(tmp_path),
         "start", "--track", M2_TRACK, "--seed", "42"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    try:
        deadline = time.monotonic() + 10
        while process.poll() is None and time.monotonic() < deadline:
            if full_cli_workspace_ready(tmp_path):
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
        assert "null score means N/A" in stdout and "lab5.py" in stdout
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
