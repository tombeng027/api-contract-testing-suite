import json
import os
import re
import uuid
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from pydantic import ValidationError

from practice_runner.models import Attempt


class StorageError(Exception):
    pass


def safe_path(root: Path, *parts: str) -> Path:
    target = root.joinpath(*parts)
    current = target
    while current != current.parent:
        if current.is_symlink() or current.is_junction():
            raise StorageError(f"Links/junctions are not permitted: {current}")
        current = current.parent
    return target


class Store:
    def __init__(self, root: Path) -> None:
        self.root = root.absolute()

    def directory(self, identity: str) -> Path:
        if re.fullmatch(r"[0-9a-f]{32}", identity) is None:
            raise StorageError("Attempt ID must be 32 lowercase hexadecimal characters")
        return safe_path(self.root, "attempts", identity)

    def save(self, record: Attempt) -> None:
        try:
            validated = Attempt.model_validate(record.model_dump())
            folder = self.directory(validated.attempt_id)
            folder.mkdir(parents=True, exist_ok=True)
            destination = safe_path(folder, "attempt.json")
            if destination.exists():
                old = self.load(record.attempt_id)
                if old.status != "in_progress":
                    raise StorageError("Terminal attempts cannot be rewritten")
                old_events = [event.model_dump() for event in old.events]
                if [event.model_dump() for event in record.events[:len(old_events)]] != old_events:
                    raise StorageError("Prior events cannot be rewritten")
                mutable = {
                    "events", "status", "updated_at", "ended_at",
                    "practice_seconds", "timing_complete", "error",
                }
                original_content = {
                    key: value for key, value in old.model_dump().items() if key not in mutable
                }
                current_content = {
                    key: value for key, value in record.model_dump().items() if key not in mutable
                }
                if original_content != current_content:
                    raise StorageError("Attempt identity/content cannot change")
                if record.practice_seconds < old.practice_seconds:
                    raise StorageError("Checkpoint duration cannot decrease")
            temporary = safe_path(folder, f".{uuid.uuid4().hex}.tmp")
            try:
                with temporary.open("x", encoding="utf-8") as stream:
                    stream.write(validated.model_dump_json(indent=2))
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(temporary, destination)
            finally:
                if temporary.exists():
                    temporary.unlink()
        except (OSError, UnicodeError, ValidationError) as error:
            raise StorageError(f"Could not save {record.attempt_id}: {error}") from error

    def load(self, identity: str) -> Attempt:
        path = safe_path(self.directory(identity), "attempt.json")
        try:
            record = Attempt.model_validate_json(path.read_text(encoding="utf-8"))
            if record.attempt_id != identity:
                raise StorageError(f"Record/directory ID mismatch: {path}")
            return record
        except (OSError, UnicodeError, ValidationError) as error:
            raise StorageError(f"Cannot review {path}: {error}") from error

    def history(self) -> tuple[list[Attempt], list[str]]:
        directory = safe_path(self.root, "attempts")
        if not directory.exists():
            return [], []
        records: list[Attempt] = []
        errors: list[str] = []
        try:
            folders = sorted(directory.iterdir())
        except OSError as error:
            raise StorageError(f"Cannot enumerate history: {error}") from error
        for folder in folders:
            try:
                records.append(self.load(folder.name))
            except StorageError as error:
                errors.append(str(error))
        return sorted(records, key=lambda record: (record.started_at, record.attempt_id)), errors

    @contextmanager
    def writer(self) -> Generator[None, None, None]:
        path = safe_path(self.root, ".writer-lock.json")
        token = uuid.uuid4().hex
        acquired = False
        try:
            self.root.mkdir(parents=True, exist_ok=True)
            with path.open("x", encoding="utf-8") as stream:
                acquired = True
                json.dump({"pid": os.getpid(), "token": token}, stream)
        except FileExistsError as error:
            raise StorageError(
                f"Writer lock exists: {path}. Check the owner before using unlock."
            ) from error
        except OSError as error:
            if acquired:
                try:
                    path.unlink()
                except OSError as cleanup_error:
                    raise StorageError(
                        f"Lock write failed: {error}; lock cleanup also failed: {cleanup_error}"
                    ) from cleanup_error
            raise StorageError(f"Cannot create writer lock: {error}") from error
        try:
            yield
        finally:
            self.unlock(token)

    def unlock(self, token: str) -> None:
        path = safe_path(self.root, ".writer-lock.json")
        try:
            owner = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(owner, dict) or owner.get("token") != token:
                raise StorageError("Lock token mismatch; lock was not removed")
            path.unlink()
        except (OSError, ValueError) as error:
            raise StorageError(f"Cannot release writer lock: {error}") from error
