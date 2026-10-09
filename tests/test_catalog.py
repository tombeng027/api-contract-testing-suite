import httpx
import pytest

from tests.contract_helpers import assert_error_response, assert_json_response, assert_known_fields

EXPECTED: list[dict[str, object]] = [
    {"id": 1, "sku": "DEMO-001", "name": "Inspection kit",
     "price_cents": 2500, "available": True},
    {"id": 2, "sku": "DEMO-002", "name": "Replacement seal",
     "price_cents": 0, "available": False},
    {"id": 3, "sku": "DEMO-003", "name": "Test gauge",
     "price_cents": 1099, "available": True},
]


@pytest.mark.smoke
def test_product_contract(client: httpx.Client) -> None:
    response = client.get("/v1/products/1")
    assert_json_response(response, 200, "product")
    product = response.json()
    assert_known_fields(product, EXPECTED[0])


@pytest.mark.smoke
def test_missing_product_contract(client: httpx.Client) -> None:
    response = client.get("/v1/products/999")
    assert_error_response(response, 404, "PRODUCT_NOT_FOUND", "Product not found")


@pytest.mark.regression
@pytest.mark.parametrize("index", [0, 1, 2], ids=["first", "zero-price", "third"])
def test_each_seeded_product(client: httpx.Client, index: int) -> None:
    expected = EXPECTED[index]
    response = client.get(f'/v1/products/{expected["id"]}')
    assert_json_response(response, 200, "product")
    product = response.json()
    assert_known_fields(product, expected)


@pytest.mark.regression
@pytest.mark.parametrize(
    "query,indices",
    [("", [0, 1, 2]), ("?available=true", [0, 2]), ("?available=false", [1])],
    ids=["all", "available", "unavailable"],
)
def test_list_filter(client: httpx.Client, query: str, indices: list[int]) -> None:
    response = client.get(f"/v1/products{query}")
    assert_json_response(response, 200, "products")
    actual = response.json()
    assert len(actual) == len(indices)
    for product, index in zip(actual, indices, strict=True):
        assert_known_fields(product, EXPECTED[index])


@pytest.mark.regression
@pytest.mark.parametrize("value", [
    "", "True", "FALSE", "1", "0", "yes", " true ", "null",
])
def test_invalid_filter(client: httpx.Client, value: str) -> None:
    response = client.get("/v1/products", params={"available": value})
    assert_error_response(response, 422, "INVALID_REQUEST", "Invalid request")


@pytest.mark.regression
@pytest.mark.parametrize("query", [
    "available=true&available=true", "available=true&available=false",
    "unknown=value", "available=true&unknown=value",
])
def test_duplicate_and_unknown_queries(client: httpx.Client, query: str) -> None:
    response = client.get(f"/v1/products?{query}")
    assert_error_response(response, 422, "INVALID_REQUEST", "Invalid request")


@pytest.mark.regression
@pytest.mark.parametrize("path", ["/health", "/v1/products/1"])
def test_other_routes_reject_queries(client: httpx.Client, path: str) -> None:
    response = client.get(path, params={"available": "true"})
    assert_error_response(response, 422, "INVALID_REQUEST", "Invalid request")


@pytest.mark.regression
@pytest.mark.parametrize("identity", [
    "0", "-1", "+1", "01", "1.0", "abc", " 1 ", "\u0661", "2147483648", "9" * 100,
])
def test_invalid_id(client: httpx.Client, identity: str) -> None:
    response = client.get(f"/v1/products/{identity}")
    assert_error_response(response, 422, "INVALID_REQUEST", "Invalid request")


@pytest.mark.regression
def test_largest_valid_id_is_not_found(client: httpx.Client) -> None:
    response = client.get("/v1/products/2147483647")
    assert_error_response(response, 404, "PRODUCT_NOT_FOUND", "Product not found")


@pytest.mark.regression
def test_health_readiness(client: httpx.Client) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.headers["content-type"].split(";", 1)[0] == "application/json"
    assert response.json() == {"status": "ok"}
