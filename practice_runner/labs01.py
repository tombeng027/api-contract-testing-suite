import json
import random
import uuid
from importlib.resources import files
from typing import Literal

from pydantic import model_validator

from practice_runner.engine import PracticeError, asset, now
from practice_runner.m2 import LabContent, M2Session
from practice_runner.models import (
    Attempt, L01_ASSESSMENT_VERSION, L01_CHECKER_VERSION, L01_TRACK,
    LabSpec, M2Variant, StrictRecord, TASKS, digest, task_kind,
)
from practice_runner.storage import StorageError, Store, safe_path


class Labs01Manifest(StrictRecord):
    track: Literal["api-foundations-labs01"]
    content_version: Literal["1"]
    assessment_version: Literal["1"]
    generator_version: Literal["1"]
    checker_version: Literal["1"]
    labs: dict[str, LabContent]

    @model_validator(mode="after")
    def coherent(self) -> "Labs01Manifest":
        if (
            self.assessment_version != L01_ASSESSMENT_VERSION
            or self.checker_version != L01_CHECKER_VERSION
        ):
            raise ValueError("Manifest versions do not match the installed Labs 0-1 checker")
        if list(self.labs) != ["0", "1"]:
            raise ValueError("Labs 0-1 manifest must contain Labs 0 and 1 in order")
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


def labs01_manifest() -> Labs01Manifest:
    return Labs01Manifest.model_validate_json(
        files("practice_runner").joinpath("assets", "labs01.json").read_text(encoding="utf-8")
    )


def create_labs01_attempt(store: Store, seed: int, lab: int | None = None) -> Attempt:
    if type(seed) is not int or not 0 <= seed <= 2**32 - 1:
        raise PracticeError("Seed must be an integer from 0 through 4294967295")
    if lab is not None and (type(lab) is not int or lab not in (0, 1)):
        raise PracticeError("Labs 0-1 lab must be 0 or 1")
    content = labs01_manifest()
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
        "record_schema_version": 2, "attempt_id": uuid.uuid4().hex, "track": L01_TRACK,
        "content_version": content.content_version,
        "assessment_version": content.assessment_version,
        "generator_version": content.generator_version,
        "checker_version": content.checker_version,
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
            safe_path(work, f"lab{identity}.py").write_text(
                asset(f"lab{identity}-starter"), encoding="utf-8",
            )
    except (OSError, UnicodeError, StorageError) as error:
        failed = record.model_dump()
        failed.update(status="errored", ended_at=now(), updated_at=now(), error=str(error))
        store.save(Attempt.model_validate(failed))
        raise StorageError(f"Could not prepare fresh Labs 0-1 workspace: {error}") from error
    return record


class Labs01Session(M2Session):
    checker = L01_CHECKER_VERSION
