import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from practice_runner.engine import PracticeError, Session, asset, create_attempt
from practice_runner.models import Attempt, digest
from practice_runner.storage import StorageError, Store


def code_session(tmp_path: Path) -> Session:
    store = Store(tmp_path)
    session = Session(store, create_attempt(store, 42, "code"))
    source = asset("solution")
    (store.directory(session.record.attempt_id) / "work" / "answer.py").write_text(
        source, encoding="utf-8"
    )
    assert session.submit("code").outcome == "passed"
    return session


@pytest.mark.parametrize("outcome", ["learner_failure", "infrastructure_error"])
def test_latest_check_supersedes_stale_passing_score(tmp_path: Path, outcome: str) -> None:
    session = code_session(tmp_path)
    source = session.record.submissions("code")[-1].answer
    session.commit(session.event(
        "check", task="code", answer=source, source_digest=digest(source or ""),
        outcome=outcome, feedback="Synthetic repeat-check failure",
        exit_code=1,
    ))
    record = session.store.load(session.record.attempt_id)
    assert record.score(first=True) == 100
    assert record.score() == 0
    if outcome == "infrastructure_error":
        with pytest.raises(ValidationError, match="valid final submission"):
            session.finish()
        assert session.store.load(record.attempt_id).status == "in_progress"
    else:
        session.finish()
        assert session.store.load(record.attempt_id).score() == 0


def test_repeat_infrastructure_failure_closes_session(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    session = code_session(tmp_path)
    monkeypatch.setattr("practice_runner.engine.check_code", lambda *args: {
        "outcome": "infrastructure_error", "feedback": "SYNTHETIC_CHECKER_FAILURE",
        "checks": {}, "exit_code": 2,
    })
    with pytest.raises(PracticeError, match="SYNTHETIC_CHECKER_FAILURE"):
        session.submit("code")
    record = session.store.load(session.record.attempt_id)
    assert record.status == "errored"
    assert record.events[-1].kind == "check"
    assert record.score(first=True) == 100
    assert record.score() == 0
    with pytest.raises(PracticeError, match="already closed"):
        session.finish()


def test_repeat_check_cannot_claim_another_source(tmp_path: Path) -> None:
    session = code_session(tmp_path)
    source = "# unrelated code"
    event = session.event(
        "check", task="code", answer=source, source_digest=digest(source),
        outcome="learner_failure", exit_code=1,
    )
    with pytest.raises(ValidationError, match="latest code submission"):
        session.commit(event)
    assert len(session.store.load(session.record.attempt_id).events) == 1


@pytest.mark.parametrize("kind", ["submission", "check"])
def test_code_result_cannot_be_ungraded(tmp_path: Path, kind: str) -> None:
    session = code_session(tmp_path)
    data = session.record.model_dump()
    event = dict(data["events"][0])
    event.update(kind=kind, outcome="ungraded")
    if kind == "submission":
        data["events"][0] = event
    else:
        event["sequence"] = 2
        data["events"].append(event)
    with pytest.raises(ValidationError, match="Code results cannot be ungraded"):
        Attempt.model_validate(data)


@pytest.mark.parametrize("field", ["seed", "variant"])
def test_store_rejects_rewritten_attempt_content(tmp_path: Path, field: str) -> None:
    session = code_session(tmp_path)
    original = session.record.model_dump()
    data = session.record.model_dump()
    if field == "seed":
        data["seed"] += 1
    else:
        data["variant"]["explanation"] = "Rewritten prompt"
        manifest = {
            "track": data["track"], "assessment": data["assessment_version"],
            "tasks": data["tasks"], "points": data["points"], "variant": data["variant"],
        }
        data["manifest_digest"] = digest(json.dumps(manifest, sort_keys=True))
    candidate = Attempt.model_validate(data)
    with pytest.raises(StorageError, match="identity/content"):
        session.store.save(candidate)
    assert session.store.load(session.record.attempt_id).model_dump() == original
