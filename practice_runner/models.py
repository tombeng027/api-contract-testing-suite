import hashlib
import json
import math
import re
from datetime import datetime
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

TRACK = "api-foundations-m1b"
VERSION = "1"
TASKS = ("prediction", "explanation", "code")
M2_TRACK = "api-contracts-m2"
M2_ASSESSMENT_VERSION = "2"
M2_CHECKER_VERSION = "2"
M2_CHECKS = ("valid", "boundary", "missing", "wrong-type", "wrong-value")
STATUS = Literal["in_progress", "completed", "abandoned", "errored"]
OUTCOME = Literal["passed", "learner_failure", "infrastructure_error", "ungraded"]


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def utc_timestamp(value: str) -> None:
    moment = datetime.fromisoformat(value)
    if moment.utcoffset() is None or moment.utcoffset().total_seconds() != 0:
        raise ValueError("Timestamp must have a UTC offset")


class StrictRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, validate_assignment=True)


class Variant(StrictRecord):
    price: int = Field(ge=0)
    missing_id: int = Field(ge=4)
    prediction: str
    explanation: str
    exercise: str


class LabSpec(StrictRecord):
    topic: str
    prediction: str
    choices: list[str]
    correct: str
    explanation: str
    exercise: str
    hint: str
    rubric: str

    @model_validator(mode="after")
    def coherent(self) -> Self:
        if not self.choices or len(set(self.choices)) != len(self.choices):
            raise ValueError("Prediction choices must be distinct")
        if self.correct not in self.choices:
            raise ValueError("Correct prediction must be an offered choice")
        return self


class M2Variant(Variant):
    manifest_version: Literal["1"]
    labs: dict[str, LabSpec]


def task_kind(task: str | None) -> str:
    return (task or "").rsplit(".", 1)[-1]


class Event(StrictRecord):
    sequence: int = Field(ge=1)
    timestamp: str
    kind: Literal["submission", "hint", "solution", "pause", "resume", "check"]
    task: str | None = None
    answer: str | None = None
    outcome: OUTCOME | None = None
    feedback: str = ""
    source_digest: str | None = None
    stdout: str = ""
    stderr: str = ""
    truncated: bool = False
    checks: dict[str, bool] = Field(default_factory=dict)
    exit_code: int | None = None

    @model_validator(mode="after")
    def coherent(self) -> Self:
        utc_timestamp(self.timestamp)
        if self.kind in ("submission", "check"):
            if self.task is None or self.answer is None or self.outcome is None:
                raise ValueError("Submission/check needs task, answer and outcome")
            code = task_kind(self.task) == "code"
            if code and self.outcome == "ungraded":
                raise ValueError("Code results cannot be ungraded")
            if code and self.source_digest != digest(self.answer):
                raise ValueError("Code snapshot digest mismatch")
            names = (
                ("correct", "zero", "wrong-price", "string-price", "boolean-price")
                if self.task == "code" else M2_CHECKS
            )
            if code and self.outcome == "passed" and (
                self.checks != {name: True for name in names} or self.exit_code != 0
            ):
                raise ValueError("Code pass missing successful checker evidence")
        elif self.kind in ("hint", "solution") and self.task is None:
            raise ValueError("Assistance requires a task")
        return self


class Attempt(StrictRecord):
    record_schema_version: Literal[1, 2] = 1
    attempt_id: str
    track: Literal["api-foundations-m1b", "api-contracts-m2"] = TRACK
    content_version: Literal["1"] = VERSION
    assessment_version: Literal["1", "2"] = VERSION
    generator_version: Literal["1"] = VERSION
    checker_version: Literal["1", "2"] = VERSION
    scope: Literal["slice", "prediction", "explanation", "code", "full", "lab-2", "lab-3", "lab-4", "lab-5"] = "slice"
    seed: int = Field(ge=0, le=2**32 - 1)
    variant: M2Variant | Variant
    manifest_digest: str
    tasks: list[str]
    points: dict[str, int]
    status: STATUS = "in_progress"
    started_at: str
    updated_at: str
    ended_at: str | None = None
    practice_seconds: float = Field(ge=0, allow_inf_nan=False)
    timing_complete: bool = False
    events: list[Event] = Field(default_factory=list)
    error: str | None = None

    @model_validator(mode="after")
    def coherent(self) -> Self:
        if re.fullmatch(r"[0-9a-f]{32}", self.attempt_id) is None:
            raise ValueError("Invalid attempt ID")
        if self.track == M2_TRACK:
            if self.assessment_version != self.checker_version:
                raise ValueError("M2 assessment/checker versions must match")
            if self.record_schema_version != 2 or not isinstance(self.variant, M2Variant):
                raise ValueError("M2 requires schema 2 and its manifest snapshot")
            labs = ["2", "3", "4", "5"] if self.scope == "full" else [self.scope.removeprefix("lab-")]
            if self.scope not in ("full", "lab-2", "lab-3", "lab-4", "lab-5"):
                raise ValueError("Invalid M2 scope")
            if list(self.variant.labs) != labs:
                raise ValueError("Lab snapshot does not match scope")
            expected = [f"{lab}.{kind}" for lab in labs for kind in TASKS]
        else:
            if self.assessment_version != VERSION or self.checker_version != VERSION:
                raise ValueError("M1B requires its original assessment/checker versions")
            if self.record_schema_version != 1 or isinstance(self.variant, M2Variant):
                raise ValueError("M1B requires schema 1 and its original variant")
            if self.scope not in ("slice", *TASKS):
                raise ValueError("Invalid M1B scope")
            expected = list(TASKS) if self.scope == "slice" else [self.scope]
        if self.tasks != expected or self.points != {
            task: (0 if task_kind(task) == "explanation" else 1) for task in expected
        }:
            raise ValueError("Tasks/points do not match assessment")
        manifest = {
            "track": self.track, "assessment": self.assessment_version,
            "tasks": self.tasks, "points": self.points,
            "variant": self.variant.model_dump(),
        }
        if self.manifest_digest != digest(json.dumps(manifest, sort_keys=True)):
            raise ValueError("Manifest snapshot digest mismatch")
        for timestamp in (self.started_at, self.updated_at, self.ended_at):
            if timestamp is not None:
                utc_timestamp(timestamp)
        if (self.status == "in_progress") != (self.ended_at is None):
            raise ValueError("Terminal state/end timestamp mismatch")
        if [event.sequence for event in self.events] != list(range(1, len(self.events) + 1)):
            raise ValueError("Event sequence mismatch")
        paused = False
        submitted: set[str] = set()
        latest_code: dict[str, Event] = {}
        for event in self.events:
            if event.task is not None and event.task not in self.tasks:
                raise ValueError("Event outside selected scope")
            if event.kind == "pause":
                if paused:
                    raise ValueError("Already paused")
                paused = True
            elif event.kind == "resume":
                if not paused:
                    raise ValueError("Not paused")
                paused = False
            elif paused:
                raise ValueError("Learning event while paused")
            if event.kind == "submission":
                submitted.add(event.task or "")
            if event.kind == "solution" and event.task not in submitted:
                raise ValueError("Solution revealed before submission")
            if event.kind == "check" and event.task not in submitted:
                raise ValueError("Check without code submission")
            if event.kind == "check" and task_kind(event.task) != "code":
                raise ValueError("Only code checks can be repeated")
            if event.kind == "check":
                previous = latest_code.get(event.task or "")
                if (
                    previous is None or event.answer != previous.answer
                    or event.source_digest != previous.source_digest
                ):
                    raise ValueError("Repeated check must match the latest code submission")
            if event.kind == "submission" and task_kind(event.task) == "code":
                latest_code[event.task or ""] = event
            if event.kind in ("submission", "check"):
                if task_kind(event.task) == "prediction":
                    choices = ["200", "404", "422"]
                    correct = "404"
                    if isinstance(self.variant, M2Variant):
                        spec = self.variant.labs[(event.task or "").split(".")[0]]
                        choices, correct = spec.choices, spec.correct
                    if event.answer not in choices:
                        raise ValueError("Invalid prediction format")
                    result = "passed" if event.answer == correct else "learner_failure"
                    if event.outcome != result:
                        raise ValueError("Prediction outcome mismatch")
                if task_kind(event.task) == "explanation":
                    if not event.answer or not event.answer.strip() or event.outcome != "ungraded":
                        raise ValueError("Invalid explanation submission")
        if self.status == "completed":
            if not self.timing_complete or paused:
                raise ValueError("Incomplete completed timing")
            for task in self.tasks:
                answers = self.results(task)
                if not answers or answers[-1].outcome == "infrastructure_error":
                    raise ValueError("Missing required valid final submission")
        if not math.isfinite(self.practice_seconds):
            raise ValueError("Invalid duration")
        return self

    def submissions(self, task: str) -> list[Event]:
        return [event for event in self.events if event.kind == "submission" and event.task == task]

    def results(self, task: str) -> list[Event]:
        return [
            event for event in self.events
            if event.kind in ("submission", "check") and event.task == task
        ]

    def score(self, first: bool = False) -> float | None:
        possible = sum(self.points.values())
        if not possible:
            return None
        earned = 0
        for task, points in self.points.items():
            answers = self.submissions(task) if first else self.results(task)
            if answers and answers[0 if first else -1].outcome == "passed":
                earned += points
        return 100 * earned / possible

    def assisted(self) -> bool:
        return any(event.kind in ("hint", "solution") for event in self.events)
