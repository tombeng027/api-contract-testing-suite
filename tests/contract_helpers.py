import json
from importlib.resources import files

import httpx
from jsonschema import Draft202012Validator


def validator(name: str) -> Draft202012Validator:
    schema = json.loads(
        files("contracts").joinpath("v1", f"{name}.json").read_text(encoding="utf-8")
    )
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def assert_json_response(response: httpx.Response, status: int, schema: str) -> None:
    assert response.status_code == status, response.text
    media_type = response.headers["content-type"].split(";", 1)[0].strip().lower()
    assert media_type == "application/json"
    validator(schema).validate(response.json())


def assert_known_fields(actual: dict[str, object], expected: dict[str, object]) -> None:
    assert {key: actual[key] for key in expected} == expected, "Known product values differ"


def assert_error_response(
    response: httpx.Response, status: int, code: str, message: str
) -> None:
    assert_json_response(response, status, "error")
    error = response.json()["error"]
    assert error["code"] == code
    assert error["message"] == message
