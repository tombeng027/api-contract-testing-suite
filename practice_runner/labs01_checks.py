"""Independent synthetic behavior oracles for the bounded Lab 0-1 exercises."""

from collections.abc import Callable
from copy import deepcopy

from practice_runner.models import M2_CHECKS

KNOWN_IDS = (1, 2, 3)


def check_lab01(function: Callable[..., object], lab: int, price: int) -> list[dict[str, object]]:
    product: dict[str, object] = {
        "id": 1, "sku": "SYNTHETIC", "name": "Practice part",
        "price_cents": price, "available": True,
    }
    groups: dict[str, list[tuple[tuple[object, ...], object]]]
    if lab == 0:
        incomplete = {key: value for key, value in product.items() if key != "price_cents"}
        groups = {
            "valid": [
                ((200, product, price), None),
                ((200, {**product, "category": "DEMO"}, price), None),
            ],
            "boundary": [
                ((200, {**product, "price_cents": 0}, 0), None),
            ],
            "missing": [
                ((200, incomplete, price), "schema"),
                ((200, {key: value for key, value in product.items() if key != "sku"}, price), "schema"),
            ],
            "wrong-type": [
                ((200, {**product, "price_cents": str(price)}, price), "price"),
                ((200, {**product, "price_cents": True}, 1), "price"),
                ((404, product, price), "status"),
                # Status is checked before structure, so it reports first even here.
                ((500, incomplete, price), "status"),
            ],
            "wrong-value": [
                ((200, {**product, "price_cents": price + 1}, price), "price"),
            ],
        }
    elif lab == 1:
        groups = {
            "valid": [
                ((1, [], KNOWN_IDS), 200),
                ((None, [], KNOWN_IDS), 200),
                ((None, [("available", "false")], KNOWN_IDS), 200),
            ],
            "boundary": [
                ((3, [], KNOWN_IDS), 200),
                ((None, [("available", "true")], KNOWN_IDS), 200),
                ((0, [], KNOWN_IDS), 422),
            ],
            "missing": [
                ((100 + price % 900, [], KNOWN_IDS), 404),
                ((2147483647, [], KNOWN_IDS), 404),
            ],
            "wrong-type": [
                ((True, [], KNOWN_IDS), 422),
                (("1", [], KNOWN_IDS), 422),
                ((1.0, [], KNOWN_IDS), 422),
                ((None, [("available", "True")], KNOWN_IDS), 422),
                ((None, [("available", "FALSE")], KNOWN_IDS), 422),
            ],
            "wrong-value": [
                ((-5, [], KNOWN_IDS), 422),
                ((None, [("available", "true"), ("available", "true")], KNOWN_IDS), 422),
                ((None, [("unexpected", "value")], KNOWN_IDS), 422),
                ((None, [("available", "true"), ("unexpected", "value")], KNOWN_IDS), 422),
                ((None, [("available", " true")], KNOWN_IDS), 422),
            ],
        }
    else:
        raise ValueError(f"Unknown lab: {lab}")
    results = []
    for name in M2_CHECKS:
        passed = True
        for arguments, expected in groups[name]:
            actual = function(*deepcopy(arguments))
            if lab == 0:
                matched = actual is None if expected is None else (
                    type(actual) is str and actual == expected
                )
            else:
                matched = type(actual) is int and actual == expected
            passed = passed and matched
        results.append({"name": name, "passed": passed})
    return results
