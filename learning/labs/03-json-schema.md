# Lab 3: diagnose JSON Schema failures

M2 reference guide. Use the [M2 runner](../m2-track.md) for saved companion Lab 3 tasks; notes proposed in this guide are not automatically imported.

## Concept

Schema validation describes shape, required fields, types and boundaries. A useful failure explanation names both the rule and the location; "validation failed" is not enough.

## Predict

Starting from the [v1 product contract](../../contracts/v1/product.json), predict the keyword and instance path for:

1. Removing `price_cents`.
2. Replacing its value with `"2500"`.
3. Setting it to `-1`.
4. Setting `available` to `"true"` in the first item of a product list.

Required-field errors point to the containing object, not to a nonexistent child value.

## Run

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_schema_guards.py -v
```

Expected exit 0: 25 guard/oracle cases pass. Several test invalid payloads and assert exact error evidence; invalid fixtures are not mistaken for successful responses.

## Investigate

Compare `validator`, `absolute_path` and the relevant schema rule in [the guards](../../tests/test_schema_guards.py). Distinguish `absolute_path` (payload location) from `absolute_schema_path` (constraint location).

The list schema embeds product rules. Its drift guard checks that these remain aligned with the standalone product schema.

## Change

Before opening the solution, write a small test in your own notes that sets `price_cents` to zero and requires validation to succeed. Then outline a negative-price test that asserts exactly one `minimum` error at `["price_cents"]`.

Do not weaken the published consumer schema to make an invalid example pass. The current guide does not save or automatically grade your notes.

## Verify

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_catalog.py -k zero-price -v
```

Expected exit 0: one live zero-price case passes. The schema guards above cover the negative boundary; a live API response and a schema-only fixture establish different facts.

## Explain

- Why is a missing-field error located at the parent object?
- How does a nested list path help locate the defect?
- Why can `2500.0` satisfy JSON Schema's integer type while a fractional price cannot?

See the [separate reference](../solutions/03-json-schema.md) after writing your prediction and proposed tests.
