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
    groups = {name: [case] for name, case in zip(M2_CHECKS, cases, strict=True)}
    # Extra probes remain aggregate evidence, not additional score units.
    if lab == 2:
        groups["wrong-type"].extend(
            ((200, {**product, "price_cents": value}, price), True)
            for value in (str(price), float(price), price + 0.5, None)
        )
    if lab == 3:
        groups["valid"].append(((200, {**product, "category": "DEMO"}, price), False))
        groups["boundary"].extend(
            ((200, {**product, "id": identity, "available": False}, price), False)
            for identity in (1.0, 2147483647)
        )
        invalid = [
            {**product, "price_cents": value} for value in (price + 0.5, str(price), True)
        ] + [
            {**product, "id": value} for value in (0, True, 2147483648, "1", 1.5)
        ] + [
            {**product, field: value} for field in ("sku", "name") for value in ("", "   ", 42)
        ] + [
            {**product, "available": value} for value in (0, None)
        ] + [
            {key: value for key, value in product.items() if key != field}
            for field in product
        ]
        groups["wrong-type"].extend(((200, changed, price), True) for changed in invalid)
        groups["wrong-value"].append(((404, product, price), True))
    if lab == 4:
        for field in ("code", "message"):
            changed = deepcopy(error)
            changed["error"][field] = "WRONG"
            groups["wrong-value"].append(((404, changed, expected_error), True))
    if lab == 5:
        groups["valid"].extend([
            (({**product, "price_cents": 0}, "v1"), True),
            (({**product, "price_cents": price + 1}, "v1"), True),
            (({**product, "price_cents": float(price)}, "v1"), True),
            (({**v2, "category": "DEMO", "price": {
                "amount_cents": price, "currency": "USD", "metadata": "DEMO",
            }}, "v2"), True),
            (({**v2, "price": {"amount_cents": float(price), "currency": "USD"}}, "v2"), True),
        ])
        for version, payload in (("v1", product), ("v2", v2)):
            groups["boundary"].extend(
                (({**payload, "id": identity, "available": False}, version), True)
                for identity in (1.0, 2147483647)
            )
            groups["missing"].extend(
                (({key: value for key, value in payload.items() if key != field}, version), False)
                for field in payload
            )
            groups["wrong-type"].extend(
                (({**payload, field: value}, version), False)
                for field, values in (
                    ("id", ("1", True, 1.5)),
                    ("sku", (42, None)), ("name", (42, None)),
                    ("available", ("true", 0, None)),
                ) for value in values
            )
            groups["wrong-type"].extend(
                ((value, version), False) for value in (None, [], "product")
            )
            groups["wrong-value"].extend(
                (({**payload, field: value}, version), False)
                for field, values in (
                    ("id", (0, 2147483648)), ("sku", ("", "   ")), ("name", ("", "   ")),
                ) for value in values
            )
        groups["wrong-type"].extend(
            (({**product, "price_cents": value}, "v1"), False)
            for value in (True, price + 0.5, None)
        )
        groups["wrong-value"].append((({**product, "price_cents": -1}, "v1"), False))
        invalid_prices = [
            {"amount_cents": 0, "currency": "EUR"},
            {"amount_cents": "0", "currency": "USD"},
            {"amount_cents": True, "currency": "USD"},
            {"amount_cents": price + 0.5, "currency": "USD"},
            {"amount_cents": None, "currency": "USD"},
            {"amount_cents": 0, "currency": None},
            {"amount_cents": 0}, {"currency": "USD"}, None, [], 0,
        ]
        groups["wrong-type"].extend(
            (({**v2, "price": changed_price}, "v2"), False) for changed_price in invalid_prices
        )
        removed = {key: value for key, value in product.items() if key != "price_cents"}
        groups["missing"].append((({**removed, "cost_cents": price}, "v1"), False))
        try:
            function(deepcopy(product), "v3")
        except ValueError:
            unknown_rejected = True
        else:
            unknown_rejected = False
    results = []
    for name, probes in groups.items():
        passed = True
        for arguments, expected in probes:
            if lab == 5:
                actual = function(*deepcopy(arguments))
                matched = type(actual) is bool and actual is expected
            else:
                rejected = False
                try:
                    function(*deepcopy(arguments))
                except AssertionError:
                    rejected = True
                matched = rejected is expected
            passed = passed and matched
        if lab == 5 and name == "wrong-value":
            passed = passed and unknown_rejected
        results.append({"name": name, "passed": passed})
    return results
