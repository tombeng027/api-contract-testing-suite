# Reference: meaningful assertions

Read after predicting and attempting [Lab 2](../labs/02-meaningful-assertions.md).

The schema accepts 9999 cents because it is a nonnegative integer. The independent expected-price assertion rejects it because DEMO-001 is documented as 2500 cents.

The runner solution is:

```python
def check_product(payload, expected_price):
    assert type(payload["price_cents"]) is int
    assert payload["price_cents"] == expected_price
```

Here exact `type` is deliberate: `isinstance(True, int)` is true in Python. This exercise requires Python integer values; JSON Schema also accepts mathematically integral numbers such as `2500.0`. Those are distinct policies, not interchangeable tests.

The runner checks valid generated/zero values and three invalid examples. Always failing rejects valid inputs; always passing misses defects; hard-coding 2500 misses generated expectations.

This small function does not check status, headers, the full schema or all product fields. The [live test](../../tests/test_catalog.py) and [helpers](../../tests/contract_helpers.py) cover those separate expectations.
