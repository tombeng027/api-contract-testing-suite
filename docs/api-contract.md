# Catalog API contract: M1

All values are synthetic. Read-only HTTP API; no auth, database, browser UI or production deployment.

## Seeded products

| id | sku | name | price_cents | available |
|---|---|---|---|---|
| 1 | DEMO-001 | Inspection kit | 2500 | true |
| 2 | DEMO-002 | Replacement seal | 0 | false |
| 3 | DEMO-003 | Test gauge | 1099 | true |

Seeds are fresh in every application factory invocation. Prices are nonnegative integer cents; currency/exchange arithmetic is out of scope.

## Routes

| Request | Result |
|---|---|
| GET /health | 200, `{"status":"ok"}`; readiness only |
| GET /v1/products | 200, all products ordered by ascending id |
| GET /v1/products?available=true | 200, products 1 and 3 |
| GET /v1/products?available=false | 200, product 2 |
| GET /v1/products/1 | 200, complete seeded product 1 |
| GET /v1/products/2147483647 | 404, valid ID with no seeded match |

IDs use canonical ASCII decimal digits, 1 through 2147483647 inclusive. Zero, signs, leading zeros, whitespace, fractions, non-ASCII digits and values outside the range return 422. Bound input length before conversion.

Only list requests accept a query parameter: `available`, exactly once, with the exact lowercase string `true` or `false`. Empty/mixed-case/numeric values, duplicate keys (even identical values) and unknown parameters return 422. Detail/health requests reject all query parameters.

All documented responses use the application/json media type. A charset parameter is permitted; don't assert the raw header string unnecessarily.

## Errors

404:

```json
{"error":{"code":"PRODUCT_NOT_FOUND","message":"Product not found"}}
```

422:

```json
{"error":{"code":"INVALID_REQUEST","message":"Invalid request"}}
```

Errors do not echo supplied values. These contracts apply to documented GET routes; framework 405, unknown routes, redirects and OpenAPI documentation responses are not normalized or covered in M1.

## Consumer schemas and semantic checks

Independent Draft 2020-12 schemas: [product](../contracts/v1/product.json), [list](../contracts/v1/products.json), [error](../contracts/v1/error.json). They are maintained from this contract, not generated from the application's models.

Unknown response fields are tolerated to allow additive evolution. Required known fields retain their types/bounds. Strict query validation is a separate producer policy, not a reason to forbid new response fields.

Tests check exact known seeded field values in addition to schema validation. A wrong price can still satisfy the schema. Unknown fields are not compared as business expectations. The list item schema is self-contained to avoid network references; a regression checks it remains identical to the standalone product contract's validation rules.

JSON Schema integer semantics permit numerically integral JSON numbers; tests reject booleans as integer fields and reject string numbers. This is not a lexical JSON-number-format constraint.

## M2 evolution examples

The live endpoint contract above is unchanged. A [separate v2 fixture schema](../contracts/v2/product.json) replaces `price_cents` with `price.amount_cents` and `price.currency` (synthetic USD only).

Local baseline/additive/removal/rename/type-change/v2 payloads demonstrate the chosen consumer compatibility policy. The [controlled verifier](compatibility-example.md) validates exact success/failure identities, not merely a nonzero exit. There is no live v2 endpoint or automatic upgrade of v1 consumers.
