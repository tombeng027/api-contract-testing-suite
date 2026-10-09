"""Selected consumer examples, not a general API compatibility analyzer."""

import json
from importlib.resources import files
from typing import TypedDict

from jsonschema import Draft202012Validator

EXAMPLES = ("baseline", "additive", "removed", "renamed", "type_changed", "v2")


class SchemaFailure(TypedDict):
    keyword: str
    instance_path: list[str | int]
    schema_path: list[str | int]
    missing_fields: list[str]
    message: str


class ProbeResult(TypedDict):
    protocol_version: int
    example: str
    consumer: str
    compatible: bool
    failures: list[SchemaFailure]


def consumer(version: str) -> Draft202012Validator:
    if version not in ("v1", "v2"):
        raise ValueError(f"Unknown consumer version: {version}")
    schema = json.loads(
        files("contracts").joinpath(version, "product.json").read_text(encoding="utf-8")
    )
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def payload(example: str) -> object:
    if example not in EXAMPLES:
        raise ValueError(f"Unknown compatibility example: {example}")
    return json.loads(
        files("contracts").joinpath("examples", f"{example}.json").read_text(encoding="utf-8")
    )


def probe(example: str, version: str) -> ProbeResult:
    failures: list[SchemaFailure] = []
    for error in consumer(version).iter_errors(payload(example)):
        missing: list[str] = []
        if error.validator == "required" and isinstance(error.instance, dict):
            missing = [field for field in error.validator_value if field not in error.instance]
        failures.append({
            "keyword": error.validator,
            "instance_path": list(error.absolute_path),
            "schema_path": list(error.absolute_schema_path),
            "missing_fields": missing,
            "message": error.message,
        })
    failures.sort(key=lambda item: json.dumps(item, sort_keys=True))
    return {
        "protocol_version": 1, "example": example, "consumer": version,
        "compatible": not failures, "failures": failures,
    }
