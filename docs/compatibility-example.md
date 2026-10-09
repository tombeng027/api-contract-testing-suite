# Controlled contract evolution: M2

This is a synthetic fixture demonstration, not a production incident or universal compatibility analyzer. The live API remains v1.

## Consumer policy

v1 consumers require `price_cents` as a nonnegative integer alongside the existing product identity/availability fields. Unknown response fields are tolerated. Changing a field's name or type is not additive.

[The v2 fixture schema](../contracts/v2/product.json) requires `price.amount_cents` and `price.currency` instead of `price_cents`. This deliberately new contract uses synthetic USD amounts; it does not implement currency conversion or a live v2 endpoint.

| Example | Consumer | Expected |
|---|---|---|
| Baseline | v1 | Pass |
| Add category | v1 | Pass |
| Remove price_cents | v1 | Required-field failure at root |
| Rename price_cents to cost_cents | v1 | Same required-field failure |
| Change price_cents to a string | v1 | Type failure at price_cents |
| v2 nested price | v1 | Required price_cents failure |
| v2 nested price | v2 | Pass |
| Restored baseline | v1 | Pass |

The old consumer stays unchanged for all v1 checks. Adapting the consumer to v2 is explicit; silently weakening v1 expectations would hide the break.

## Reproduce

After [installation](../README.md#setup-windows-powershell), from the repository root:

```powershell
.\.venv\Scripts\python.exe scripts\verify_compatibility.py
```

The verifier starts separate processes using the same consumer probe and packaged fixtures. It accepts only each specified exit code and exact schema keyword, instance path, schema path and missing field. An unrelated startup/import failure does not count as detecting the mutation.

Expected overall exit: 0. The incompatible probes themselves exit 1; this is intentional and verified, not blanket ignored failure.

Every run writes a new evidence directory under `artifacts/compatibility/`, with per-case JSON stdout, stderr and a summary only after all cases are verified. Previous evidence remains intact.

For one intentionally failing probe:

```powershell
.\.venv\Scripts\python.exe scripts\contract_probe.py --example type_changed --consumer v1
```

Expected exit 1; one `type` failure at instance path `["price_cents"]`. This command is not the ordinary test suite.

## Limits

Schema compatibility does not prove business correctness, ordering, availability, latency or real consumer behavior. Adding fields is compatible only with this selected tolerant consumer policy. The baseline exact-value HTTP checks remain separate.

All schemas and payload examples are local package resources with no network-resolved references. Error-schema guards and semantic-value checks remain part of the foundation suite. See [API contract](api-contract.md).
