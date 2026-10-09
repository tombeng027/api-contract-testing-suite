# Lab 2: meaningful assertions

M2 reference guide. The [M2 runner](../m2-track.md) assesses its companion Lab 2 tasks; the older M1B price task below remains available.

## Concept

A successful HTTP exchange can still return incorrect business data. Status, media type and schema are necessary checks, not substitutes for an independent expected value.

## Predict

The documented price of DEMO-001 is 2500 cents. A response returns the correct fields and types but a price of 9999 cents.

- Will the v1 schema accept it?
- Which assertion should reject it?
- What would a status-only check miss?

Write your answers before running the checks.

## Run

From the repository root after [setup](../../README.md#setup-windows-powershell):

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_schema_guards.py::test_schema_does_not_establish_business_correctness tests\test_catalog.py::test_product_contract -v
```

Expected exit 0: two tests pass. The schema/business guard intentionally catches a precise assertion failure inside a passing regression; it does not leave the normal suite failing.

## Investigate

Read the guard and [assertion helpers](../../tests/contract_helpers.py). Identify where the expected price comes from. It must not be copied from the response being tested.

The selected live test checks the real response. The synthetic wrong-price guard proves the assertion rejects a particular wrong value. Neither proves every possible business rule.

## Change and verify

Use the existing repeatable price task:

```powershell
.\.venv\Scripts\python.exe -m practice_runner start --scope code --seed 42
```

Edit only the printed attempt workspace. Implement `check_product(payload, expected_price)`, then enter `submit code`. It must accept the generated correct price and zero, and reject wrong, string and boolean prices. Type-check before comparing values: Python considers `True == 1`.

Inspect the saved checks before entering `complete`. A completed task can have a failing score; completion is not a correctness claim. No work in the verified suite needs editing.

## Explain

- Why does a schema-valid response still need known-value checks?
- Why is comparing a response price with itself a weak test oracle?
- Why test both valid and invalid examples instead of always raising an assertion?

After your attempt, see the [separate reference](../solutions/02-meaningful-assertions.md). Opening this Markdown reference is not tracked as runner assistance; use `solution code` for a recorded runner reveal.
