# Reference: error contracts

For [Lab 4](../labs/04-error-contracts.md):

| Situation | Expectation |
|---|---|
| Valid missing ID 999 | 404 / PRODUCT_NOT_FOUND / Product not found |
| Nonpositive ID 0 | 422 / INVALID_REQUEST / Invalid request |
| Unknown detail query | 422 / INVALID_REQUEST / Invalid request |
| Connection refused | Transport/infrastructure failure; no HTTP status received |

A proposed detail-query test:

```python
from tests.contract_helpers import assert_error_response

def test_unknown_detail_query(client):
    response = client.get("/v1/products/1", params={"unexpected": "value"})
    assert_error_response(response, 422, "INVALID_REQUEST", "Invalid request")
```

The existing `other_routes_reject_queries` regression exercises the same rule. This snippet is a reference proposal, not a new test automatically added by the guide.

Schema acceptance establishes the envelope and allowed code set. Independent code/message assertions establish the expected operation outcome. Additive metadata can be accepted without ignoring incorrect known fields.

Do not treat a curl process exit 0 as proof of HTTP 200. Do not accept any exception as an expected rejection. Unknown routes, unsupported methods and framework-generated errors are outside this project's normalized GET-route contract.
