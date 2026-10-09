# Lab 1: read an HTTP exchange

M1 reference guide, not an implemented interactive/scored attempt.

## Concept

The method and path select an operation. Query parameters refine it. Status describes the outcome; headers describe response metadata; JSON contains the business result. Their expectations must agree.

## Predict

Write expected status and key response values for:

1. `GET /v1/products/1`
2. `GET /v1/products/999`
3. `GET /v1/products?available=false`
4. `GET /v1/products?available=True`
5. `GET /v1/products?available=true&available=true`

Explain the difference between a missing valid ID and invalid input.

## Run the reference checks

From this repository's root:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_catalog.py -m smoke -v
.\.venv\Scripts\python.exe -m pytest tests\test_catalog.py -k "list_filter or invalid_filter or duplicate_and_unknown" -v
```

Both commands should exit 0. The first runs 2 success/error cases; the second runs 15 filter/query cases. Deselected tests are intentional selection, not skipped tests.

## Inspect requests manually

In a separate PowerShell terminal:

```powershell
.\.venv\Scripts\python.exe -m catalog_api
```

It binds localhost port 8001. If that port is occupied, stop and identify the conflict; do not kill an unrelated process.

In your original terminal:

```powershell
curl.exe -i "http://127.0.0.1:8001/v1/products/1"
curl.exe -i "http://127.0.0.1:8001/v1/products/999"
curl.exe -i "http://127.0.0.1:8001/v1/products?available=false"
curl.exe -i "http://127.0.0.1:8001/v1/products?available=True"
curl.exe -i "http://127.0.0.1:8001/v1/products?available=true&available=true"
```

`-i` displays status/headers/body. curl can exit 0 on HTTP 404/422: transfer success is not an assertion that the business request succeeded. Read the HTTP status. Stop only your manual server with Ctrl+C when finished.

Manual server data is independent of test fixtures. There is no stored database to reset in M1.

## Investigate and change

Compare actual responses with [the contract](../../docs/api-contract.md). Write a proposed check for unknown query `unexpected=value`, including status and error body, in your notes before opening the [reference](../solutions/01-http-exchange.md).

Run the existing unknown-query regression as part of the second command. It verifies rejection rather than accepting silently ignored parameters.

## Explain

- Why does valid-but-missing product 999 return 404 while `available=True` returns 422?
- Why parse the media type instead of demanding one exact Content-Type string?
- If curl exits 0 on a 404, what determines whether your test should pass?

Code-edit starter workspaces, objective scoring and saved submissions are now available in the separate [M1B three-task slice](../practice-slice.md). This reference guide is not automatically assessed by that runner.
