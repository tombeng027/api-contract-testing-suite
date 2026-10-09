import json
from importlib.resources import files

import pytest

from tests.contract_helpers import assert_known_fields, validator

VALID: dict[str, object] = {
    "id": 1, "sku": "DEMO-001", "name": "Inspection kit",
    "price_cents": 2500, "available": True,
}


@pytest.mark.regression
@pytest.mark.parametrize("name", ["product", "products", "error"])
def test_schemas_are_valid(name: str) -> None:
    validator(name)


@pytest.mark.regression
@pytest.mark.parametrize("field", list(VALID))
def test_required_field_guard(field: str) -> None:
    payload = {key: value for key, value in VALID.items() if key != field}
    errors = list(validator("product").iter_errors(payload))
    assert len(errors) == 1
    assert errors[0].validator == "required"
    assert field in errors[0].validator_value
    assert field not in errors[0].instance


@pytest.mark.regression
@pytest.mark.parametrize("field,value,rule", [
    ("id", True, "type"), ("id", 0, "minimum"),
    ("id", 2147483648, "maximum"), ("price_cents", "2500", "type"),
    ("price_cents", -1, "minimum"), ("price_cents", False, "type"),
    ("available", "true", "type"), ("sku", "   ", "pattern"),
    ("name", "\t", "pattern"),
])
def test_invalid_value_guard(field: str, value: object, rule: str) -> None:
    errors = list(validator("product").iter_errors({**VALID, field: value}))
    assert len(errors) == 1
    assert errors[0].validator == rule
    assert list(errors[0].absolute_path) == [field]


@pytest.mark.regression
def test_additive_field_is_compatible() -> None:
    additive = {**VALID, "category": "Synthetic"}
    validator("product").validate(additive)
    assert_known_fields(additive, VALID)


@pytest.mark.regression
def test_schema_does_not_establish_business_correctness() -> None:
    wrong_price = {**VALID, "price_cents": 9999}
    validator("product").validate(wrong_price)
    with pytest.raises(AssertionError, match="Known product values differ"):
        assert_known_fields(wrong_price, VALID)


@pytest.mark.regression
def test_list_item_contract_matches_product() -> None:
    product = json.loads(files("contracts").joinpath("v1", "product.json").read_text())
    listing = json.loads(files("contracts").joinpath("v1", "products.json").read_text())
    rules = {key: value for key, value in product.items() if key not in ("$schema", "title")}
    assert listing["items"] == rules
    validator("products").validate([])
    errors = list(validator("products").iter_errors([{**VALID, "available": "true"}]))
    assert len(errors) == 1
    assert list(errors[0].absolute_path) == [0, "available"]
    assert errors[0].validator == "type"


@pytest.mark.regression
@pytest.mark.parametrize("payload,rule", [
    ({}, "required"),
    ({"error": {"message": "Invalid request"}}, "required"),
    ({"error": {"code": "INVALID_REQUEST"}}, "required"),
    ({"error": {"code": "UNKNOWN", "message": "Invalid request"}}, "enum"),
    ({"error": {"code": "INVALID_REQUEST", "message": 42}}, "type"),
])
def test_error_contract_guards(payload: dict[str, object], rule: str) -> None:
    errors = list(validator("error").iter_errors(payload))
    assert len(errors) == 1
    assert errors[0].validator == rule
