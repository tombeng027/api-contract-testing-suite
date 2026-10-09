import json
import random
import uuid
from importlib.resources import files
from typing import Literal

from pydantic import model_validator

from practice_runner.engine import PracticeError, Session, asset, now
from practice_runner.exercise import check_code
from practice_runner.models import (
    Attempt, Event, LabSpec, M2_TRACK, M2Variant, StrictRecord, TASKS, digest, task_kind,
)
from practice_runner.storage import StorageError, Store, safe_path


class Prediction(StrictRecord):
    prompt: str
    choices: list[str]
    correct: str


class LabContent(StrictRecord):
    topic: str
    predictions: list[Prediction]
    explanation: str
    exercise: str
    hint: str
    rubric: str


class Manifest(StrictRecord):
    track: Literal["api-contracts-m2"]
    content_version: Literal["1"]
    assessment_version: Literal["1"]
    generator_version: Literal["1"]
    checker_version: Literal["1"]
    labs: dict[str, LabContent]

    @model_validator(mode="after")
    def coherent(self) -> "Manifest":
        if list(self.labs) != ["2", "3", "4", "5"]:
            raise ValueError("M2 manifest must contain Labs 2-5 in order")
        for content in self.labs.values():
            if not content.predictions:
                raise ValueError("Lab needs prediction variants")
            for prediction in content.predictions:
                if (
                    prediction.correct not in prediction.choices
                    or len(set(prediction.choices)) != len(prediction.choices)
                ):
                    raise ValueError("Invalid manifest prediction choices")
        return self


def manifest() -> Manifest:
    return Manifest.model_validate_json(
        files("practice_runner").joinpath("assets", "m2.json").read_text(encoding="utf-8")
    )


def create_m2_attempt(store: Store, seed: int, lab: int | None = None) -> Attempt:
    if type(seed) is not int or not 0 <= seed <= 2**32 - 1:
        raise PracticeError("Seed must be an integer from 0 through 4294967295")
    if lab is not None and (type(lab) is not int or lab not in (2, 3, 4, 5)):
        raise PracticeError("M2 lab must be 2, 3, 4 or 5")
    content = manifest()
    generator = random.Random(seed)
    price = generator.randint(10, 5000)
    missing = generator.randint(100, 999)
    values = {"price": price, "wrong_price": price + 1, "missing_id": missing}
    specs: dict[str, LabSpec] = {}
    # Generate all labs before selecting scope so a seed has the same lab variant in either scope.
    for identity, entry in content.labs.items():
        prediction = generator.choice(entry.predictions)
        spec = LabSpec(
            topic=entry.topic, prediction=prediction.prompt.format(**values),
            choices=prediction.choices, correct=prediction.correct,
            explanation=entry.explanation, exercise=entry.exercise.format(**values),
            hint=entry.hint, rubric=entry.rubric,
        )
        if lab is None or identity == str(lab):
            specs[identity] = spec
    variant = M2Variant(
        price=price, missing_id=missing, prediction="Lab-specific predictions",
        explanation="Lab-specific explanations", exercise="Lab-specific code tasks",
        manifest_version="1", labs=specs,
    )
    tasks = [f"{identity}.{kind}" for identity in specs for kind in TASKS]
    points = {task: 0 if task_kind(task) == "explanation" else 1 for task in tasks}
    snapshot = {
        "track": content.track, "assessment": content.assessment_version,
        "tasks": tasks, "points": points, "variant": variant.model_dump(),
    }
    timestamp = now()
    record = Attempt.model_validate({
        "record_schema_version": 2, "attempt_id": uuid.uuid4().hex, "track": M2_TRACK,
        "scope": "full" if lab is None else f"lab-{lab}",
        "seed": seed, "variant": variant.model_dump(), "tasks": tasks, "points": points,
        "manifest_digest": digest(json.dumps(snapshot, sort_keys=True)),
        "started_at": timestamp, "updated_at": timestamp, "practice_seconds": 0.0,
    })
    store.save(record)
    try:
        work = safe_path(store.directory(record.attempt_id), "work")
        work.mkdir(exist_ok=False)
        for identity in specs:
            safe_path(work, f"lab{identity}.py").write_text(asset(f"lab{identity}-starter"), encoding="utf-8")
    except (OSError, UnicodeError, StorageError) as error:
        failed = record.model_dump()
        failed.update(status="errored", ended_at=now(), updated_at=now(), error=str(error))
        store.save(Attempt.model_validate(failed))
        raise StorageError(f"Could not prepare fresh M2 workspace: {error}") from error
    return record


class M2Session(Session):
    def spec(self, task: str) -> LabSpec:
        self.available(task)
        variant = self.record.variant
        if not isinstance(variant, M2Variant):
            raise PracticeError("M2 session requires its manifest snapshot")
        return variant.labs[task.split(".")[0]]

    def prompt(self, task: str) -> str:
        spec = self.spec(task)
        return getattr(spec, "exercise" if task_kind(task) == "code" else task_kind(task))

    def submit(self, task: str, answer: str = "") -> Event:
        spec = self.spec(task)
        kind = task_kind(task)
        if kind == "prediction":
            answer = answer.strip()
            if answer not in spec.choices:
                raise PracticeError(f"Enter one of {spec.choices}; no answer recorded")
            event = self.event(
                "submission", task=task, answer=answer,
                outcome="passed" if answer == spec.correct else "learner_failure",
                feedback=f"Expected {spec.correct}. Review the lab contract and explain why.",
            )
        elif kind == "explanation":
            if not answer.strip():
                raise PracticeError("Explanation cannot be blank")
            event = self.event(
                "submission", task=task, answer=answer, outcome="ungraded",
                feedback=f"Saved for rubric review, not automatically graded. {spec.rubric}",
            )
        else:
            identity = task.split(".")[0]
            folder = self.store.directory(self.record.attempt_id)
            try:
                source = safe_path(folder, "work", f"lab{identity}.py").read_text(encoding="utf-8")
            except (OSError, UnicodeError) as error:
                raise StorageError(f"Cannot read exercise file: {error}") from error
            if len(source.encode("utf-8")) > 65536:
                raise PracticeError("Exercise source exceeds 64 KiB")
            result = check_code(folder, source, self.record.variant.price, lab=int(identity))
            prior = self.record.submissions(task)
            event = self.event(
                "check" if prior and prior[-1].answer == source else "submission",
                task=task, answer=source, source_digest=digest(source), **result,
            )
        self.commit(event)
        if event.outcome == "infrastructure_error":
            self.finish("errored", event.feedback)
            raise PracticeError(event.feedback)
        return event

    def assistance(self, task: str, solution: bool = False) -> str:
        spec = self.spec(task)
        if solution and not self.record.submissions(task):
            raise PracticeError("Make a submission before revealing the solution")
        if not solution:
            text = spec.hint
        elif task_kind(task) == "code":
            text = asset(f"lab{task.split('.')[0]}-solution")
        elif task_kind(task) == "prediction":
            text = spec.correct
        else:
            text = spec.rubric
        self.commit(self.event("solution" if solution else "hint", task=task, feedback=text))
        return text
