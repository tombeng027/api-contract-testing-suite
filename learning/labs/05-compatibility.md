# Lab 5: reason about consumer compatibility

M2 reference guide. Use the [M2 runner](../m2-track.md) for saved companion Lab 5 tasks. v2 is a fixture contract, not a live service.

## Concept

Compatibility is relative to a consumer's expectations. Adding a response field is safe for this tolerant consumer; removing or changing a required field is not. Passing a schema still does not establish all business behavior.

## Predict

For the v1 consumer, classify adding `category`, removing `price_cents`, renaming it to `cost_cents`, and changing its value to a string.

Then predict how the nested v2 price fares against the unchanged v1 consumer and against the explicit v2 consumer. Write the expected failing keyword/path before running.

## Run

```powershell
.\.venv\Scripts\python.exe scripts\verify_compatibility.py
```

Expected overall exit 0: all eight specified outcomes are verified, including intentional incompatible probes. Each run retains a separate evidence directory; inspect its `summary.json` and per-case stdout/stderr.

For one explicit incompatible probe:

```powershell
.\.venv\Scripts\python.exe scripts\contract_probe.py --example type_changed --consumer v1
```

Expected exit 1, exactly one `type` failure at `["price_cents"]`. This is a diagnostic command, not the ordinary passing suite.

## Investigate

Compare [the fixtures](../../contracts/examples), [v1](../../contracts/v1/product.json), [v2](../../contracts/v2/product.json) and [precise verifier expectations](../../contracts/verification.py).

An import error also produces a nonzero process exit, but does not meet the expected protocol, keyword, paths and missing-field evidence.

## Change

Before opening the solution, outline a consumer check for v2 that accepts zero amount, rejects a negative amount and rejects unsupported currency. Explain why you must not modify v1 to silently accept the rename.

The guide does not edit schemas, save notes or grade this proposal.

## Verify

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_compatibility.py -v
```

Expected exit 0: 26 cases pass, including nested v2 boundaries and verifier rejection of unrelated failures. Reference proposals must detect the intended wrong behavior, not just accept the happy path.

## Explain

- Compatible with which consumer, version and policy?
- Why does explicit v2 acceptance not repair an old consumer?
- What business changes could remain invisible to schema validation?

See the [separate reference](../solutions/05-compatibility.md) after your attempt, plus the [demonstration's limits](../../docs/compatibility-example.md#limits).
