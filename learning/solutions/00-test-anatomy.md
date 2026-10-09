# Lab 0 reference

Read after attempting the predictions.

- Interpreter: this repository's `.venv\Scripts\python.exe`; a bare PATH command may select a different environment.
- Product 1: id 1, SKU DEMO-001, Inspection kit, 2500 integer cents, available true.
- A wrong nonnegative integer price can satisfy the schema. An independent expected value is still necessary.

One minimal proposed assertion is:

```python
assert response.json()["price_cents"] == 2500
```

The reference suite checks all known seeded fields through `assert_known_fields`. It does not import expected seed values from the app implementation.

In the schema-versus-business guard, `pytest.raises` expects the semantic assertion to fail for the wrong price. An unrelated exception or missing expected failure would make that guard test fail.

The fixture avoids shared manual-server state, binds an ephemeral port before startup and closes its owned socket/server. Successful-run lifecycle evidence does not establish every possible failure-path cleanup.
