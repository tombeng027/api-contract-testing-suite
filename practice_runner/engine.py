import json
import random
import time
import uuid
from collections.abc import Callable
from datetime import datetime, timezone
from importlib.resources import files

from practice_runner.exercise import check_code
from practice_runner.models import Attempt, Event, TASKS, Variant, digest, task_kind
from practice_runner.storage import StorageError, Store, safe_path


class PracticeError(Exception):
    pass


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def asset(name: str) -> str:
    return files("practice_runner").joinpath("assets", f"{name}.py.txt").read_text(encoding="utf-8")


def create_attempt(store: Store, seed: int, scope: str = "slice") -> Attempt:
    if scope not in ("slice", *TASKS):
        raise PracticeError("Unknown scope")
    if type(seed) is not int or not 0 <= seed <= 2**32 - 1:
        raise PracticeError("Seed must be an integer from 0 through 4294967295")
    generator = random.Random(seed)
    price = generator.randint(10, 5000)
    missing = generator.randint(100, 999)
    variant = Variant(
        price=price, missing_id=missing,
        prediction=f"GET /v1/products/{missing}: predict HTTP status (200, 404 or 422).",
        explanation="Why can a product response pass its schema but still have an incorrect price?",
        exercise=(
            f"Edit work/answer.py: check_product(payload, expected_price) must assert an exact "
            f"integer price, accepting {price} cents and zero, rejecting wrong/string/boolean prices."
        ),
    )
    tasks = list(TASKS) if scope == "slice" else [scope]
    points = {task: 0 if task == "explanation" else 1 for task in tasks}
    manifest = {"track": "api-foundations-m1b", "assessment": "1",
                "tasks": tasks, "points": points, "variant": variant.model_dump()}
    timestamp = now()
    record = Attempt.model_validate({
        "attempt_id": uuid.uuid4().hex, "scope": scope, "seed": seed,
        "variant": variant.model_dump(),
        "manifest_digest": digest(json.dumps(manifest, sort_keys=True)),
        "tasks": tasks, "points": points, "started_at": timestamp, "updated_at": timestamp,
        "practice_seconds": 0.0,
    })
    store.save(record)
    folder = store.directory(record.attempt_id)
    work = safe_path(folder, "work")
    try:
        work.mkdir(exist_ok=False)
        if "code" in tasks:
            safe_path(work, "answer.py").write_text(asset("starter"), encoding="utf-8")
    except (OSError, StorageError) as error:
        failed = record.model_dump()
        failed.update(status="errored", ended_at=now(), updated_at=now(), error=str(error))
        store.save(Attempt.model_validate(failed))
        raise StorageError(f"Could not prepare fresh exercise workspace: {error}") from error
    return record


class Session:
    def __init__(self, store: Store, record: Attempt, clock: Callable[[], float] = time.monotonic) -> None:
        if record.status != "in_progress" or record.events:
            raise PracticeError("Only a fresh attempt can be started; resume is not implemented")
        self.store = store
        self.record = record
        self.clock = clock
        self.last = clock()
        self.paused = False

    def prompt(self, task: str) -> str:
        return getattr(self.record.variant, "exercise" if task == "code" else task)

    def commit(self, event: Event | None = None, **changes: object) -> None:
        current = self.clock()
        elapsed = current - self.last
        if elapsed < 0:
            raise PracticeError("Monotonic clock moved backward")
        data = self.record.model_dump()
        data["practice_seconds"] += 0 if self.paused else elapsed
        data["updated_at"] = now()
        if event is not None:
            data["events"].append(event.model_dump())
        data.update(changes)
        candidate = Attempt.model_validate(data)
        self.store.save(candidate)
        self.record = candidate
        self.last = current

    def event(self, kind: str, **fields: object) -> Event:
        return Event.model_validate({
            "sequence": len(self.record.events) + 1,
            "timestamp": now(), "kind": kind, **fields,
        })

    def available(self, task: str | None = None) -> None:
        if self.record.status != "in_progress":
            raise PracticeError("Attempt is closed")
        if self.paused:
            raise PracticeError("Resume before a learning action")
        if task is not None and task not in self.record.tasks:
            raise PracticeError("Task not in selected scope")

    def submit(self, task: str, answer: str = "") -> Event:
        self.available(task)
        if task == "prediction":
            answer = answer.strip()
            if answer not in ("200", "404", "422"):
                raise PracticeError("Enter 200, 404 or 422; no answer was recorded")
            outcome = "passed" if answer == "404" else "learner_failure"
            event = self.event("submission", task=task, answer=answer, outcome=outcome,
                               feedback="Valid missing ID returns 404." if outcome == "passed" else
                               "Incorrect prediction; compare missing resource with invalid input.")
        elif task == "explanation":
            if not answer.strip():
                raise PracticeError("Explanation cannot be blank")
            event = self.event("submission", task=task, answer=answer, outcome="ungraded",
                               feedback="Saved for rubric review; no automatic explanation score.")
        else:
            folder = self.store.directory(self.record.attempt_id)
            try:
                source = safe_path(folder, "work", "answer.py").read_text(encoding="utf-8")
            except (OSError, UnicodeError) as error:
                raise StorageError(f"Cannot read exercise file: {error}") from error
            if len(source.encode("utf-8")) > 65536:
                raise PracticeError("Exercise source exceeds 64 KiB; shorten it before submitting")
            result = check_code(folder, source, self.record.variant.price)
            prior = self.record.submissions("code")
            kind = "check" if prior and prior[-1].answer == source else "submission"
            event = self.event(kind, task="code", answer=source, source_digest=digest(source), **result)
        self.commit(event)
        if event.outcome == "infrastructure_error":
            self.finish("errored", event.feedback)
            raise PracticeError(event.feedback)
        return event

    def assistance(self, task: str, solution: bool = False) -> str:
        self.available(task)
        if solution and not self.record.submissions(task):
            raise PracticeError("Make a submission before revealing the solution")
        hints = {
            "prediction": "The ID is valid but not seeded; distinguish missing from invalid.",
            "explanation": "Compare structural constraints with independent expected business values.",
            "code": "Check both exact integer type and expected value. bool is an int subclass in Python.",
        }
        solutions = {
            "prediction": "404: the positive canonical ID is valid but missing.",
            "explanation": "Schema checks shape/type/bounds, not the independently expected price.",
            "code": asset("solution"),
        }
        text = (solutions if solution else hints)[task]
        self.commit(self.event("solution" if solution else "hint", task=task, feedback=text))
        return text

    def pause(self) -> None:
        self.available()
        self.commit(self.event("pause"))
        self.paused = True

    def resume(self) -> None:
        if not self.paused or self.record.status != "in_progress":
            raise PracticeError("Attempt is not paused")
        self.commit(self.event("resume"))
        self.paused = False

    def finish(self, status: str = "completed", error: str | None = None) -> None:
        if self.record.status != "in_progress":
            raise PracticeError("Attempt is already closed")
        if status == "completed":
            self.available()
            if any(not self.record.submissions(task) for task in self.record.tasks):
                raise PracticeError("Submit every required task before completion")
        self.commit(status=status, ended_at=now(), timing_complete=True, error=error)


def statistics(records: list[Attempt]) -> list[dict[str, object]]:
    groups: dict[tuple[str, str, str], list[Attempt]] = {}
    for record in records:
        groups.setdefault((record.track, record.assessment_version, record.scope), []).append(record)
    result = []
    for key, attempts in sorted(groups.items()):
        completed = [record for record in attempts if record.status == "completed"]
        scored = [record for record in completed if record.score() is not None]
        timed = [record for record in completed if record.timing_complete]
        unassisted = [record for record in scored if not record.assisted()]

        def mean(values: list[float | None]) -> float | None:
            numbers = [value for value in values if value is not None]
            return sum(numbers) / len(numbers) if numbers else None

        predictions = [
            record.submissions("prediction")[0] for record in completed
            if record.submissions("prediction")
        ]
        result.append({
            "track": key[0], "assessment_version": key[1], "scope": key[2],
            "started": len(attempts), "completed": len(completed),
            "abandoned": sum(record.status == "abandoned" for record in attempts),
            "errored": sum(record.status == "errored" for record in attempts),
            "in_progress": sum(record.status == "in_progress" for record in attempts),
            "completion_rate": 100 * len(completed) / len(attempts),
            "mean_final_score": mean([record.score() for record in scored]),
            "mean_first_score": mean([record.score(first=True) for record in scored]),
            "scored_count": len(scored),
            "mean_practice_seconds": mean([record.practice_seconds for record in timed]),
            "timed_count": len(timed),
            "unassisted_count": len(unassisted),
            "mean_unassisted_score": mean([record.score() for record in unassisted]),
            "prediction_first_correct": sum(event.outcome == "passed" for event in predictions),
            "prediction_first_answered": len(predictions),
            "assistance_events": sum(
                event.kind in ("hint", "solution") for record in completed for event in record.events
            ),
            "failed_code_checks": sum(
                task_kind(event.task) == "code" and event.outcome == "learner_failure"
                for record in completed for event in record.events
            ),
            "topics": {
                task: {
                    "first_answered": sum(bool(record.submissions(task)) for record in completed),
                    "first_correct": sum(
                        bool(record.submissions(task)) and record.submissions(task)[0].outcome == "passed"
                        for record in completed
                    ),
                    "final_correct": sum(
                        bool(record.results(task)) and record.results(task)[-1].outcome == "passed"
                        for record in completed
                    ),
                }
                for task in attempts[0].tasks if task_kind(task) != "explanation"
            },
        })
    return result
