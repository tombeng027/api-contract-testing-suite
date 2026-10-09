# Reference: JSON Schema

For [Lab 3](../labs/03-json-schema.md):

| Change | Keyword | Instance path |
|---|---|---|
| Missing price_cents | required | `[]` |
| String price | type | `["price_cents"]` |
| Negative price | minimum | `["price_cents"]` |
| String availability in first list item | type | `[0, "available"]` |

For a missing root field, the schema path is `["required"]`. For a price type violation, it is `["properties", "price_cents", "type"]`.

A proposed pair of schema tests, using the existing helper and synthetic baseline:

```python
from tests.contract_helpers import validator
from tests.test_schema_guards import VALID

def test_zero_price():
    validator("product").validate({**VALID, "price_cents": 0})

def test_negative_price():
    errors = list(validator("product").iter_errors({**VALID, "price_cents": -1}))
    assert len(errors) == 1
    assert errors[0].validator == "minimum"
    assert list(errors[0].absolute_path) == ["price_cents"]
```

These are reference proposals, not files automatically created by the guide. Existing guards/live tests already verify the stated boundaries.

JSON Schema's integer rule is mathematical, not a check of lexical JSON formatting. An integral numeric value can pass; a fractional value cannot. Boolean prices still fail.

Avoid broad "any exception" checks: a missing import is not proof the intended schema rejected the payload. Keep the fixture local, the validator valid and the expected failure precise.
