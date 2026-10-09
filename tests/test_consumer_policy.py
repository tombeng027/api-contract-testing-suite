import httpx
import pytest

from contracts.compatibility import consumer
from tests.contract_helpers import assert_error_response


@pytest.mark.regression
def test_error_assertions_tolerate_additive_metadata() -> None:
    response = httpx.Response(
        422, headers={"Content-Type": "application/json; charset=utf-8"},
        json={
            "error": {"code": "INVALID_REQUEST", "message": "Invalid request", "reference": "SYNTHETIC"},
            "request_id": "SYNTHETIC",
        },
    )
    assert_error_response(response, 422, "INVALID_REQUEST", "Invalid request")


@pytest.mark.regression
def test_error_assertions_still_reject_wrong_known_fields() -> None:
    response = httpx.Response(
        422, headers={"Content-Type": "application/json"},
        json={"error": {"code": "PRODUCT_NOT_FOUND", "message": "Product not found"}},
    )
    with pytest.raises(AssertionError):
        assert_error_response(response, 422, "INVALID_REQUEST", "Invalid request")


@pytest.mark.regression
def test_schema_integer_policy_is_not_lexical_json_format() -> None:
    payload = {
        "id": 1, "sku": "DEMO-001", "name": "Inspection kit",
        "price_cents": 2500.0, "available": True,
    }
    consumer("v1").validate(payload)
    payload["price_cents"] = 2500.5
    errors = list(consumer("v1").iter_errors(payload))
    assert len(errors) == 1
    assert errors[0].validator == "type"
    assert list(errors[0].absolute_path) == ["price_cents"]
