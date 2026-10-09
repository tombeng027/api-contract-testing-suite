import argparse
import json
import secrets
import sys
from pathlib import Path

from pydantic import ValidationError

from practice_runner.engine import PracticeError, Session, create_attempt, statistics
from practice_runner.models import Attempt, TRACK, M2_TRACK, task_kind
from practice_runner.m2 import M2Session, create_m2_attempt
from practice_runner.storage import StorageError, Store


def display(value: object) -> None:
    print(json.dumps(value, indent=2, ensure_ascii=True))


def summary(record: Attempt) -> dict[str, object]:
    return {
        "attempt_id": record.attempt_id, "track": record.track, "scope": record.scope,
        "assessment_version": record.assessment_version, "checker_version": record.checker_version,
        "seed": record.seed, "status": record.status,
        "first_score": record.score(first=True) if record.status == "completed" else None,
        "final_score": record.score() if record.status == "completed" else None,
        "practice_seconds": record.practice_seconds,
        "timing": "complete" if record.timing_complete else "partial checkpoint only",
        "assisted": record.assisted(),
        "explanations": "saved; awaiting rubric review" if any(
            record.submissions(task) for task in record.tasks if task_kind(task) == "explanation"
        ) else "none",
    }


def interact(session: Session) -> int:
    record = session.record
    print("Trusted local practice only. No sandbox, AI grading or mastery claim.")
    print(f"Attempt: {record.attempt_id}")
    print(f"Workspace: {session.store.directory(record.attempt_id) / 'work'}")
    for task in record.tasks:
        print(f"{task}: {session.prompt(task)}")
    print(
        "Commands: submit <task-id> <answer>, submit <code-task-id>,\n"
        "hint <task>, solution <task>, pause, resume, status, complete, quit.\n"
        "Use the printed task IDs and workspace files. null score means N/A."
    )
    try:
        while True:
            text = input("practice> ").strip()
            action, _, remainder = text.partition(" ")
            try:
                if action == "submit":
                    task, _, answer = remainder.partition(" ")
                    event = session.submit(task, answer)
                    display(event.model_dump())
                elif action in ("hint", "solution"):
                    print(session.assistance(remainder, solution=action == "solution"))
                elif action == "pause":
                    session.pause()
                    print("Paused; only resume, status or quit is available.")
                elif action == "resume":
                    session.resume()
                    print("Resumed.")
                elif action == "status":
                    display(summary(session.record))
                elif action == "complete":
                    session.finish()
                    display(summary(session.record))
                    print("Activities completed; explanations still require review.")
                    return 0
                elif action == "quit":
                    session.finish("abandoned")
                    print("Abandoned; accepted progress saved.")
                    return 1
                else:
                    raise PracticeError("Unknown command; no submission saved")
            except PracticeError as error:
                print(f"Practice: {error}", file=sys.stderr)
                if session.record.status == "errored":
                    return 2
    except (EOFError, KeyboardInterrupt) as error:
        session.finish("abandoned")
        print("\nInterrupted; accepted work saved as abandoned.")
        return 130 if isinstance(error, KeyboardInterrupt) else 1
    except (StorageError, OSError, ValidationError) as error:
        print(f"Attempt stopped: {error}", file=sys.stderr)
        if session.record.status == "in_progress":
            try:
                session.finish("errored", str(error))
            except (StorageError, OSError, ValidationError) as save_error:
                print(
                    f"Could not persist error status: {save_error}. Last valid record may remain in_progress.",
                    file=sys.stderr,
                )
        return 2


def main() -> int:
    parser = argparse.ArgumentParser(description="Deterministic API practice tracks")
    parser.add_argument("--data-dir", type=Path, default=Path.cwd() / ".practice-data")
    commands = parser.add_subparsers(dest="command", required=True)
    start = commands.add_parser("start")
    start.add_argument("--track", choices=[TRACK, M2_TRACK], default=TRACK)
    start.add_argument("--scope", choices=["slice", "prediction", "explanation", "code"], default="slice")
    start.add_argument("--seed", type=int, default=None)
    start.add_argument("--lab", type=int, choices=[2, 3, 4, 5])
    commands.add_parser("history")
    stats = commands.add_parser("stats")
    stats.add_argument("--track", choices=[TRACK, M2_TRACK], default=TRACK)
    review = commands.add_parser("review")
    review.add_argument("attempt_id")
    unlock = commands.add_parser("unlock", help="Explicit stale lock recovery; verify owner first")
    unlock.add_argument("--token", required=True)
    arguments = parser.parse_args()
    store = Store(arguments.data_dir)
    try:
        if arguments.command == "start":
            if arguments.track == TRACK and arguments.lab is not None:
                raise PracticeError("--lab requires --track api-contracts-m2")
            if arguments.track == M2_TRACK and arguments.scope != "slice":
                raise PracticeError("M2 uses --lab rather than --scope")
            with store.writer():
                seed = secrets.randbits(32) if arguments.seed is None else arguments.seed
                if arguments.track == M2_TRACK:
                    record = create_m2_attempt(store, seed, arguments.lab)
                    return interact(M2Session(store, record))
                record = create_attempt(store, seed, arguments.scope)
                return interact(Session(store, record))
        if arguments.command == "review":
            record = store.load(arguments.attempt_id)
            display({"summary": summary(record), "record": record.model_dump()})
            return 0
        if arguments.command == "unlock":
            store.unlock(arguments.token)
            print("Removed selected lock only; history/work unchanged.")
            return 0
        records, errors = store.history()
        display(
            [summary(record) for record in records]
            if arguments.command == "history" else statistics(
                [record for record in records if record.track == arguments.track]
            )
        )
        for error in errors:
            print(f"INCOMPLETE SUMMARY: excluded record: {error}", file=sys.stderr)
        return 2 if errors else 0
    except (StorageError, PracticeError, OSError, ValidationError) as error:
        print(f"Practice runner error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
