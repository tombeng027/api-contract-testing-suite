import argparse
import json
import sys
from pathlib import Path

from postman.runner import PostmanError, resource, run_collection
from practice_runner.storage import StorageError


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the trusted synthetic local Postman collection")
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--output", type=Path, default=Path.cwd() / "artifacts")
    arguments = parser.parse_args()
    try:
        result = run_collection(
            json.loads(resource("catalog.postman_collection.json")),
            arguments.base_url, arguments.output,
        )
        print(f"Postman CLI exit: {result.exit_code}")
        print(f"Console evidence: {result.stdout_path}")
        print(f"Error evidence: {result.stderr_path}")
        print("Exit 1 is a failed run, not proof of a particular assertion failure; inspect evidence.")
        return result.exit_code
    except (PostmanError, StorageError, OSError, ValueError) as error:
        print(f"Postman execution error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
