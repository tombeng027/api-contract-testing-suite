"""Independent synthetic behavior oracles for the bounded M2 exercises."""

from collections.abc import Callable
from copy import deepcopy

from practice_runner.models import M2_CHECKS


def check_lab(function: Callable[..., object], lab: int, price: int) -> list[dict[str, object]]:
    product: dict[str, object] = {
        "id": 1, "sku": "SYNTHETIC", "name": "Practice part",
        "price_cents": price, "available": True,
    }
    cases: list[tuple[tuple[object, ...], bool]]
    if lab == 2:
        cases = [
            ((200, product, price), False),
            ((200, {**product, "price_cents": 0}, 0), False),
            ((404, product, price), True),
            ((200, {**product, "price_cents": True}, 1), True),
            ((200, {**product, "price_cents": price + 1}, price), True),
        ]
    elif lab == 3:
        missing = {key: value for key, value in product.items() if key != "price_cents"}
        cases = [
            ((200, {**product, "price_cents": float(price)}, price + 1), False),
            ((200, {**product, "price_cents": 0}, price), False),
            ((200, missing, price), True),
            ((200, {**product, "available": "true"}, price), True),
            ((200, {**product, "price_cents": -1}, price), True),
        ]
    elif lab == 4:
        expected_error = {"status": 404, "code": "PRODUCT_NOT_FOUND", "message": "Product not found"}
        error = {"error": {"code": expected_error["code"], "message": expected_error["message"]}}
        cases = [
            ((404, error, expected_error), False),
            ((422, {"error": {"code": "INVALID_REQUEST", "message": "Invalid request", "ref": "DEMO"}},
              {"status": 422, "code": "INVALID_REQUEST", "message": "Invalid request"}), False),
            ((404, {"error": {"message": expected_error["message"]}}, expected_error), True),
            ((404, {"error": {"code": expected_error["code"], "message": 42}}, expected_error), True),
            ((422, error, expected_error), True),
        ]
    elif lab == 5:
        v2 = {key: value for key, value in product.items() if key != "price_cents"}
        v2["price"] = {"amount_cents": 0, "currency": "USD"}
        cases = [
            (({**product, "category": "DEMO"}, "v1"), True),
            ((v2, "v2"), True),
            ((v2, "v1"), False),
            (({**product, "price_cents": str(price)}, "v1"), False),
            (({**v2, "price": {"amount_cents": -1, "currency": "USD"}}, "v2"), False),
        ]
    else:
        raise ValueError(f"Unknown lab: {lab}")
    results = []
    for name, (arguments, expected) in zip(M2_CHECKS, cases, strict=True):
        if lab == 5:
            actual = function(*deepcopy(arguments))
            passed = type(actual) is bool and actual is expected
        else:
            rejected = False
            try:
                function(*deepcopy(arguments))
            except AssertionError:
                rejected = True
            passed = rejected is expected
        results.append({"name": name, "passed": passed})
    # Extra cases remain part of the required aggregate evidence, not a new score unit.
    if lab == 2:
        try:
            function(200, {**product, "price_cents": str(price)}, price)
        except AssertionError:
            pass
        else:
            results[3]["passed"] = False
    if lab == 3:
        invalid = [
            {**product, "price_cents": value} for value in (price + 0.5, str(price), True)
        ] + [
            {**product, "id": value} for value in (0, True, 2147483648)
        ] + [
            {**product, field: "   "} for field in ("sku", "name")
        ] + [
            {key: value for key, value in product.items() if key != field}
            for field in product
        ]
        for changed in invalid:
            try:
                function(200, changed, price)
            except AssertionError:
                pass
            else:
                results[3]["passed"] = False
        try:
            function(404, product, price)
        except AssertionError:
            pass
        else:
            results[4]["passed"] = False
    if lab == 4:
        for field in ("code", "message"):
            changed = deepcopy(error)
            changed["error"][field] = "WRONG"
            try:
                function(404, changed, expected_error)
            except AssertionError:
                pass
            else:
                results[4]["passed"] = False
    if lab == 5:
        invalid_prices = [
            {"amount_cents": 0, "currency": "EUR"},
            {"amount_cents": "0", "currency": "USD"},
            {"amount_cents": True, "currency": "USD"},
            {"amount_cents": 0}, {"currency": "USD"},
        ]
        for changed_price in invalid_prices:
            if function({**v2, "price": changed_price}, "v2") is not False:
                results[4]["passed"] = False
        removed = {key: value for key, value in product.items() if key != "price_cents"}
        for changed in (removed, {**removed, "cost_cents": price}):
            if function(changed, "v1") is not False:
                results[2]["passed"] = False
        # A semantic change remains structurally valid for this selected consumer.
        if function({**product, "price_cents": price + 1}, "v1") is not True:
            results[0]["passed"] = False
        try:
            function(product, "v3")
        except ValueError:
            pass
        else:
            results[4]["passed"] = False
    return results
