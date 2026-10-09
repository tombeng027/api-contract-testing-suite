# Lab 4: errors are contracts

M2 reference guide. Use the [M2 runner](../m2-track.md) for saved companion Lab 4 tasks; notes proposed in this guide are not automatically imported.

## Concept

An expected rejection can be a passing test. The test decides whether the observed status and error body match the documented requirement. Failure to reach the server is a different problem.

## Predict

For each situation, identify expected response or infrastructure failure:

1. `GET /v1/products/999`
2. `GET /v1/products/0`
3. `GET /v1/products/1?unknown=value`
4. Connection refused before an HTTP response is received.

For actual HTTP responses, predict the status, error code and message using [the API contract](../../docs/api-contract.md).

## Run

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_catalog.py -k "missing_product_contract or invalid_id or other_routes_reject_queries" -v
.\.venv\Scripts\python.exe -m pytest tests\test_schema_guards.py -k error_contract_guards -v
```

Both commands should exit 0. The first selects 13 live error cases; the second selects five error-schema cases. Tests start their own server; do not start a manual server for them.

## Investigate

Read [assert_error_response](../../tests/contract_helpers.py). It checks status, JSON media type, schema and exact expected code/message.

The shared error schema permits documented codes, but it does not prove a particular operation returned the correct one. That is why the helper also checks known values.

## Change

In your notes, propose a test for `GET /v1/products/1?unexpected=value`. Write the full status/code/message expectations before looking at the reference.

Also describe how you would report a connection failure. Do not catch it and manufacture a 404/422 response.

## Verify

The first command covers unknown-query rejection on the detail route. For tolerance without weakening known-field assertions:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_consumer_policy.py -k error_assertions -v
```

Expected exit 0: two cases pass. Additive metadata is accepted, but incorrect known error fields are rejected.

## Explain

- Why can a 404 or 422 be a passing test?
- What distinguishes an error-contract defect from a server-readiness failure?
- Why is a schema-valid code/message insufficient for a specific operation?

See the [separate reference](../solutions/04-error-contracts.md) after your prediction and proposed test. Notes are not saved or graded by the current runner.
