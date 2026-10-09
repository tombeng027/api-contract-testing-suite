# Lab 1 reference

| Request | Expected |
|---|---|
| Product 1 | 200, complete seeded product |
| Product 999 | 404, PRODUCT_NOT_FOUND / Product not found |
| available=false | 200, one product: id 2, zero price, unavailable |
| available=True | 422, INVALID_REQUEST / Invalid request |
| Duplicate available=true | 422, same invalid-request body |

A valid request can identify no existing resource (404). An invalid parameter fails the input policy before lookup/filtering (422). Different APIs can choose different policies; test the published contract, not an assumed universal convention.

Proposed unknown-query check:

```python
response = client.get("/v1/products?unexpected=value")
assert response.status_code == 422
assert response.json()["error"]["code"] == "INVALID_REQUEST"
assert response.json()["error"]["message"] == "Invalid request"
```

The suite also validates the error schema and JSON media type. Known error fields are checked without forbidding additive metadata. A charset suffix may legitimately accompany application/json.

curl's success exit can mean it transferred an HTTP error response successfully. pytest decides whether that response matches the scenario expectation. A not-found negative test passes on the expected 404, not on 200.
