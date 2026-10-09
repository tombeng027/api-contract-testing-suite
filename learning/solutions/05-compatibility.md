# Reference: compatibility

For [Lab 5](../labs/05-compatibility.md):

- Adding `category` passes the selected tolerant v1 schema.
- Removing/renaming `price_cents` fails `required` at the root, with missing field `price_cents`.
- Making its value a string fails `type` at `["price_cents"]`.
- Nested v2 price fails unchanged v1, but passes the explicit v2 schema.
- Restoring the baseline passes v1 again.

The v2 schema requires `price.amount_cents` as a nonnegative integer and `price.currency` equal to synthetic `"USD"`. Zero is valid; a negative amount fails `minimum`; another currency fails `const`.

A proposed zero-price check:

```python
from contracts.compatibility import consumer, payload

def test_v2_zero_price():
    product = payload("v2")
    product["price"]["amount_cents"] = 0
    consumer("v2").validate(product)
```

The proposal relies on the known fixture shape. The [existing typed tests](../../tests/test_compatibility.py) check shape before accessing nested values and verify negative/type/currency cases. Do not substitute the v2 schema into every v1 check: that would hide the old consumer's failure instead of demonstrating it.

Accepting any process exit 1 is insufficient. The verifier requires the named example/consumer, exact exit, protocol, one intended error and precise paths/missing field. Unexpected stderr is rejected.

Limits remain: selected fixtures and schemas do not prove real consumer migration, latency, order, availability or business prices. No live v2 endpoint or general schema-diff engine is implemented.
