import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from practice_runner.engine import PracticeError, Session, asset, create_attempt, statistics
from practice_runner.exercise import check_code
from practice_runner.models import Attempt
from practice_runner.storage import StorageError, Store


class Clock:
    def __init__(self) -> None:
        self.value = 0.0

    def __call__(self) -> float:
        return self.value


def session_at(tmp_path: Path, scope: str = "slice") -> tuple[Session, Clock]:
    store = Store(tmp_path)
    clock = Clock()
    return Session(store, create_attempt(store, 42, scope), clock), clock


def write_source(session: Session, source: str) -> Path:
    path = session.store.directory(session.record.attempt_id) / "work" / "answer.py"
    path.write_text(source, encoding="utf-8")
    return path


def complete(session: Session, prediction: str = "404") -> None:
    session.submit("prediction", prediction)
    session.submit("explanation", "Schema verifies structure, not the expected business price.")
    write_source(session, asset("solution"))
    session.submit("code")
    session.finish()


def test_fresh_attempts_preserve_history_and_work(tmp_path: Path) -> None:
    first, _ = session_at(tmp_path)
    first.submit("prediction", "200")
    path = write_source(first, "# my unfinished work")
    first.finish("abandoned")
    previous = first.store.load(first.record.attempt_id).model_dump()
    second = create_attempt(first.store, 42)
    assert second.attempt_id != first.record.attempt_id
    assert second.events == []
    assert second.variant == first.record.variant
    assert first.store.load(first.record.attempt_id).model_dump() == previous
    assert path.read_text() == "# my unfinished work"
    assert (first.store.directory(second.attempt_id) / "work" / "answer.py").read_text() == asset("starter")


def test_submission_revision_first_final_and_repeat_check(tmp_path: Path) -> None:
    session, _ = session_at(tmp_path)
    session.submit("prediction", "200")
    session.submit("prediction", "404")
    session.submit("explanation", "Independent expected values complement structural checks.")
    first_code = session.submit("code")
    assert first_code.outcome == "learner_failure"
    write_source(session, asset("solution"))
    assert session.submit("code").outcome == "passed"
    assert session.submit("code").kind == "check"
    session.finish()
    record = session.store.load(session.record.attempt_id)
    assert len(record.submissions("code")) == 2
    assert record.score(first=True) == 0
    assert record.score() == 100
    assert record.submissions("code")[0].checks["wrong-price"] is False
    assert record.submissions("code")[1].checks == {
        name: True for name in ("correct", "zero", "wrong-price", "string-price", "boolean-price")
    }


def test_pause_timing_and_closed_record(tmp_path: Path) -> None:
    session, clock = session_at(tmp_path, "prediction")
    clock.value = 10
    session.pause()
    clock.value = 100
    with pytest.raises(PracticeError, match="Resume"):
        session.submit("prediction", "404")
    with pytest.raises(PracticeError, match="Resume"):
        session.assistance("prediction")
    with pytest.raises(PracticeError, match="Resume"):
        session.finish()
    session.resume()
    clock.value = 110
    session.submit("prediction", "404")
    clock.value = 120
    session.finish()
    assert session.record.practice_seconds == 30
    assert session.record.timing_complete is True
    with pytest.raises(PracticeError, match="closed"):
        session.submit("prediction", "200")
    with pytest.raises(StorageError, match="Terminal"):
        session.store.save(session.record)


def test_assistance_gate_and_unassisted_statistics(tmp_path: Path) -> None:
    session, _ = session_at(tmp_path, "prediction")
    with pytest.raises(PracticeError, match="submission"):
        session.assistance("prediction", solution=True)
    session.assistance("prediction")
    session.submit("prediction", "404")
    assert "404" in session.assistance("prediction", solution=True)
    session.finish()
    group = statistics([session.record])[0]
    assert group["unassisted_count"] == 0
    assert group["mean_unassisted_score"] is None
    assert group["assistance_events"] == 2
    assert [event.kind for event in session.record.events] == [
        "hint", "submission", "solution",
    ]


@pytest.mark.parametrize("task,answer", [("prediction", "abc"), ("explanation", "   "), ("unknown", "")])
def test_invalid_answers_do_not_create_submissions(tmp_path: Path, task: str, answer: str) -> None:
    session, _ = session_at(tmp_path)
    with pytest.raises(PracticeError):
        session.submit(task, answer)
    assert session.store.load(session.record.attempt_id).events == []


def test_missing_tasks_and_wrong_answers_completion(tmp_path: Path) -> None:
    session, _ = session_at(tmp_path)
    with pytest.raises(PracticeError, match="every"):
        session.finish()
    session.submit("prediction", "200")
    session.submit("explanation", "My explanation will need review.")
    session.submit("code")
    session.finish()
    assert session.record.status == "completed"
    assert session.record.score() == 0


def test_exact_statistics_scope_and_incomplete_exclusions(tmp_path: Path) -> None:
    first, first_clock = session_at(tmp_path / "one")
    first_clock.value = 120
    complete(first, "200")
    second, second_clock = session_at(tmp_path / "two")
    second_clock.value = 180
    complete(second)
    third, clock = session_at(tmp_path / "three")
    clock.value = 999
    third.finish("abandoned")
    explain, _ = session_at(tmp_path / "four", "explanation")
    explain.submit("explanation", "Structural validity and expected values are different.")
    explain.finish()
    groups = statistics([first.record, second.record, third.record, explain.record])
    group = next(group for group in groups if group["scope"] == "slice")
    assert group["started"] == 3
    assert group["completed"] == 2
    assert group["abandoned"] == 1
    assert group["completion_rate"] == pytest.approx(200 / 3)
    assert group["mean_final_score"] == 75
    assert group["mean_first_score"] == 75
    assert group["mean_practice_seconds"] == 150
    assert group["scored_count"] == 2
    assert group["prediction_first_correct"] == 1
    assert group["prediction_first_answered"] == 2
    no_score = next(group for group in groups if group["scope"] == "explanation")
    assert no_score["mean_final_score"] is None
    assert statistics([]) == []


def test_atomic_write_failure_keeps_previous_record(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    session, _ = session_at(tmp_path)
    session.submit("prediction", "200")
    previous = session.store.load(session.record.attempt_id).model_dump()

    def broken_replace(source: Path, target: Path) -> None:
        raise OSError("SIMULATED_REPLACE_FAILURE")

    monkeypatch.setattr(os, "replace", broken_replace)
    with pytest.raises(StorageError, match="SIMULATED_REPLACE_FAILURE"):
        session.submit("prediction", "404")
    assert session.store.load(session.record.attempt_id).model_dump() == previous
    assert session.record.model_dump() == previous
    assert not list(session.store.directory(session.record.attempt_id).glob("*.tmp"))


def test_corrupt_and_unsupported_history_are_reported(tmp_path: Path) -> None:
    session, _ = session_at(tmp_path)
    session.finish("abandoned")
    corrupt = "a" * 32
    directory = session.store.directory(corrupt)
    directory.mkdir()
    (directory / "attempt.json").write_text('{"broken":')
    records, errors = session.store.history()
    assert len(records) == 1 and len(errors) == 1
    assert corrupt in errors[0]
    with pytest.raises(StorageError, match="Cannot review"):
        session.store.load(corrupt)
    data = session.record.model_dump()
    data["record_schema_version"] = 99
    (directory / "attempt.json").write_text(json.dumps(data))
    assert len(session.store.history()[1]) == 1


def test_record_validation_catches_inconsistency(tmp_path: Path) -> None:
    session, _ = session_at(tmp_path, "prediction")
    session.submit("prediction", "200")
    data = session.record.model_dump()
    data["events"][0]["outcome"] = "passed"
    with pytest.raises(ValidationError, match="outcome mismatch"):
        Attempt.model_validate(data)
    data = session.record.model_dump()
    data["practice_seconds"] = float("nan")
    with pytest.raises(ValidationError):
        Attempt.model_validate(data)
    data = session.record.model_dump()
    data["variant"]["price"] += 1
    with pytest.raises(ValidationError, match="Manifest"):
        Attempt.model_validate(data)


def test_writer_lock_conflict_and_token_recovery(tmp_path: Path) -> None:
    store = Store(tmp_path)
    with store.writer():
        with pytest.raises(StorageError, match="lock exists"):
            with store.writer():
                pytest.fail("Second writer entered")
        with pytest.raises(StorageError, match="token mismatch"):
            store.unlock("wrong")
        assert (tmp_path / ".writer-lock.json").exists()
    assert not (tmp_path / ".writer-lock.json").exists()
    (tmp_path / ".writer-lock.json").write_text(json.dumps({"pid": 123, "token": "stale"}))
    store.unlock("stale")
    assert not (tmp_path / ".writer-lock.json").exists()


def test_path_escape_rejected_without_deleting_work(tmp_path: Path) -> None:
    session, _ = session_at(tmp_path)
    with pytest.raises(StorageError, match="Attempt ID"):
        session.store.load("..\\elsewhere")
    path = session.store.directory(session.record.attempt_id) / "work" / "answer.py"
    path.unlink()
    outside = tmp_path / "outside.py"
    outside.write_text(asset("solution"))
    if os.name == "nt":
        work = path.parent
        work.rmdir()
        target = tmp_path / "external"
        target.mkdir()
        (target / "answer.py").write_text(asset("solution"))
        result = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(work), str(target)], capture_output=True,
        )
        assert result.returncode == 0
    else:
        path.symlink_to(outside)
    with pytest.raises(StorageError, match="Links/junctions"):
        session.submit("code")
    assert outside.read_text() == asset("solution")


@pytest.mark.parametrize("source,outcome", [
    ("def broken(:", "learner_failure"),
    ("import module_that_does_not_exist", "infrastructure_error"),
    ("raise RuntimeError('unexpected')", "infrastructure_error"),
    ("def check_product(payload, expected_price):\n    assert False", "learner_failure"),
])
def test_checker_distinguishes_failures(tmp_path: Path, source: str, outcome: str) -> None:
    result = check_code(tmp_path, source, 2500)
    assert result["outcome"] == outcome


def test_checker_timeout_and_output_limit(tmp_path: Path) -> None:
    timed = check_code(tmp_path, "while True: pass", 100, timeout=0.3)
    assert timed["outcome"] == "infrastructure_error"
    assert "timeout" in str(timed["feedback"])
    loud = check_code(tmp_path, "print('x' * 6000)\n" + asset("solution"), 100)
    assert loud["outcome"] == "passed"
    assert loud["truncated"] is True
    assert len(str(loud["stdout"])) == 4096


def test_infrastructure_failure_is_saved_without_credit(tmp_path: Path) -> None:
    session, _ = session_at(tmp_path)
    write_source(session, "import module_that_does_not_exist")
    with pytest.raises(PracticeError, match="ModuleNotFoundError"):
        session.submit("code")
    saved = session.store.load(session.record.attempt_id)
    assert saved.status == "errored"
    assert saved.submissions("code")[0].outcome == "infrastructure_error"
    assert statistics([saved])[0]["scored_count"] == 0


def cli(root: Path, arguments: list[str], text: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "practice_runner", "--data-dir", str(root), *arguments],
        input=text, capture_output=True, text=True, timeout=15,
    )


def test_cli_complete_review_stats_and_eof(tmp_path: Path) -> None:
    result = cli(tmp_path, ["start", "--scope", "prediction", "--seed", "1"],
                 "submit prediction 200\nsubmit prediction 404\ncomplete\n")
    assert result.returncode == 0, result.stderr
    records, errors = Store(tmp_path).history()
    assert not errors and len(records) == 1
    assert records[0].score(first=True) == 0
    assert records[0].score() == 100
    review = cli(tmp_path, ["review", records[0].attempt_id])
    assert review.returncode == 0
    assert len(json.loads(review.stdout)["record"]["events"]) == 2
    stats = cli(tmp_path, ["stats"])
    assert stats.returncode == 0
    assert json.loads(stats.stdout)[0]["completed"] == 1
    interrupted = cli(tmp_path, ["start", "--seed", "1"], "submit prediction 404\n")
    assert interrupted.returncode == 1
    records, errors = Store(tmp_path).history()
    abandoned = next(record for record in records if record.status == "abandoned")
    assert len(abandoned.events) == 1
    assert not errors
    assert not (tmp_path / ".writer-lock.json").exists()


def test_cli_corruption_warning_and_nonzero(tmp_path: Path) -> None:
    folder = tmp_path / "attempts" / ("f" * 32)
    folder.mkdir(parents=True)
    (folder / "attempt.json").write_text("not JSON")
    result = cli(tmp_path, ["stats"])
    assert result.returncode == 2
    assert "INCOMPLETE SUMMARY" in result.stderr
    assert json.loads(result.stdout) == []


def test_keyboard_interrupt_preserves_accepted_answers(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from practice_runner.__main__ import interact

    session, _ = session_at(tmp_path)
    commands = iter(["submit prediction 404"])

    def interrupted(prompt: str) -> str:
        try:
            return next(commands)
        except StopIteration:
            raise KeyboardInterrupt()

    monkeypatch.setattr("builtins.input", interrupted)
    assert interact(session) == 130
    assert session.store.load(session.record.attempt_id).status == "abandoned"
    assert len(session.record.events) == 1


def test_interrupted_checkpoint_stays_incomplete(tmp_path: Path) -> None:
    session, clock = session_at(tmp_path, "prediction")
    clock.value = 12
    session.submit("prediction", "404")
    saved = session.store.load(session.record.attempt_id)
    assert saved.status == "in_progress"
    assert saved.practice_seconds == 12
    assert saved.timing_complete is False
    assert statistics([saved])[0]["completed"] == 0
    with pytest.raises(PracticeError, match="fresh"):
        Session(session.store, saved)


def test_wall_clock_change_does_not_change_duration(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    session, clock = session_at(tmp_path, "prediction")
    monkeypatch.setattr("practice_runner.engine.now", lambda: "2000-01-01T00:00:00+00:00")
    clock.value = 15
    session.submit("prediction", "404")
    clock.value = 25
    session.finish()
    assert session.record.practice_seconds == 25


def test_cli_paused_eof_and_invalid_seed(tmp_path: Path) -> None:
    result = cli(tmp_path, ["start", "--scope", "prediction", "--seed", "1"],
                 "submit prediction 404\npause\nsubmit prediction 200\n")
    assert result.returncode == 1
    assert "Resume" in result.stderr
    records, errors = Store(tmp_path).history()
    assert not errors
    assert records[0].status == "abandoned"
    assert len(records[0].submissions("prediction")) == 1
    invalid = cli(tmp_path, ["start", "--seed", "-1"])
    assert invalid.returncode == 2
    assert len(Store(tmp_path).history()[0]) == 1


def test_started_attempt_failure_is_reported_and_saved(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from practice_runner.__main__ import interact

    session, _ = session_at(tmp_path)
    original_save = session.store.save
    calls = 0

    def fail_one_write(record: Attempt) -> None:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise StorageError("SIMULATED_STORAGE_FAILURE")
        original_save(record)

    monkeypatch.setattr(session.store, "save", fail_one_write)
    monkeypatch.setattr("builtins.input", lambda prompt: "submit prediction 404")
    assert interact(session) == 2
    saved = session.store.load(session.record.attempt_id)
    assert saved.status == "errored"
    assert saved.events == []
    assert "SIMULATED_STORAGE_FAILURE" in (saved.error or "")


def test_cli_full_slice_can_complete_with_wrong_code(tmp_path: Path) -> None:
    result = cli(
        tmp_path, ["start", "--seed", "42"],
        "submit prediction 404\nsubmit explanation Shape is not expected business value.\n"
        "submit code\ncomplete\n",
    )
    assert result.returncode == 0, result.stderr
    record = Store(tmp_path).history()[0][0]
    assert record.status == "completed"
    assert record.score() == 50
    assert record.submissions("code")[0].outcome == "learner_failure"
    assert "awaiting rubric review" in result.stdout


def test_invalid_utf8_history_is_reported(tmp_path: Path) -> None:
    folder = tmp_path / "attempts" / ("a" * 32)
    folder.mkdir(parents=True)
    (folder / "attempt.json").write_bytes(b"\xff\xfe")
    records, errors = Store(tmp_path).history()
    assert records == []
    assert len(errors) == 1 and "Cannot review" in errors[0]
