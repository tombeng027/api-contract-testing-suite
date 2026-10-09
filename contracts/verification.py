"""Independent expectations for the explicit controlled-change demonstration."""

CASES = (
    ("baseline", "baseline", "v1", None),
    ("additive", "additive", "v1", None),
    ("removed", "removed", "v1", "required"),
    ("renamed", "renamed", "v1", "required"),
    ("type_changed", "type_changed", "v1", "type"),
    ("old_consumer_v2", "v2", "v1", "required"),
    ("new_consumer_v2", "v2", "v2", None),
    ("restored", "baseline", "v1", None),
)


def verify_result(
    result: object, exit_code: int, example: str, version: str, keyword: str | None
) -> None:
    if not isinstance(result, dict):
        raise ValueError("Probe did not return an object")
    if (
        result.get("protocol_version") != 1 or result.get("example") != example
        or result.get("consumer") != version or type(result.get("compatible")) is not bool
    ):
        raise ValueError("Probe identity/protocol mismatch")
    expected = keyword is None
    if exit_code != (0 if expected else 1) or result["compatible"] is not expected:
        raise ValueError("Unexpected process exit or compatibility result")
    failures = result.get("failures")
    if expected:
        if failures != []:
            raise ValueError("Passing example contains failures")
        return
    if not isinstance(failures, list) or len(failures) != 1:
        raise ValueError("Expected exactly one precise schema failure")
    failure = failures[0]
    if not isinstance(failure, dict):
        raise ValueError("Schema failure is not an object")
    schema_path = ["required"] if keyword == "required" else ["properties", "price_cents", "type"]
    instance_path = [] if keyword == "required" else ["price_cents"]
    missing = ["price_cents"] if keyword == "required" else []
    if (
        failure.get("keyword") != keyword or failure.get("schema_path") != schema_path
        or failure.get("instance_path") != instance_path or failure.get("missing_fields") != missing
        or not isinstance(failure.get("message"), str) or not failure["message"]
    ):
        raise ValueError("Failure differs from the intended contract defect")
