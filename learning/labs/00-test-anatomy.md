# Lab 0: environment and test anatomy

M1 reference guide. These steps use local prediction notes, not scored attempts. A separate [M1B three-task runner slice](../practice-slice.md) is available; it does not automatically record this guide's activities.

## Concept

A requirement describes expected behavior. A test creates a situation, performs an action and checks an observable result. A fixture supplies the repeatable setup and cleanup.

Here, pytest discovers tests, HTTPX sends local requests, and JSON Schema validates response structure. No browser or cloud service is involved.

## Predict

Before executing:

1. Which Python interpreter should run the test?
2. What should product 1 return?
3. Would a response with a correct schema but the wrong price be acceptable?

## Run

Open PowerShell in this repository's root, complete [setup](../../README.md#setup-windows-powershell), then:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_catalog.py::test_product_contract -v
```

Expected exit code: 0; one test passes. The fixture starts its own temporary localhost server and stops it afterward. You do not need to run the manual server first.

## Investigate

Read [the test](../../tests/test_catalog.py), [helpers](../../tests/contract_helpers.py) and [fixtures](../../tests/conftest.py).

- Setup: `client` depends on `app_url`, which creates the local app/server.
- Action: `client.get("/v1/products/1")`.
- Assertions: status 200, JSON media type, product schema and exact known seeded values.
- Cleanup: HTTP client closes, server exits and its thread is joined.

Compare with your predictions before reading the [reference explanation](../solutions/00-test-anatomy.md).

## Small exercise

Without editing the verified suite, identify what additional check is needed if `price_cents` is 9999 instead of 2500. Write your proposed assertion in local notes.

Execute the existing proof:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_schema_guards.py::test_schema_does_not_establish_business_correctness -v
```

Expected: one pass. The test first accepts a structurally valid wrong-price payload, then verifies the semantic assertion raises its expected failure. It passes because the guard works, not because the wrong price is correct.

## Explain

- Why is `200` insufficient?
- What does the schema check, and what do exact seeded assertions add?
- Why use this repo's executable rather than bare `python`?

## Common problems

Missing pytest/HTTPX/jsonschema: confirm setup was installed into this repo's venv. A connection/startup error is an environment failure, not proof of a catalog-contract defect. Inspect the reported lifecycle log and captured traceback.

VS Code may retain another interpreter in the parent workspace. The explicit command above uses the repo environment even if editor discovery is wrong. Open this repo directly and select its `.venv\Scripts\python.exe` for editor use; selection/discovery must still be verified.
