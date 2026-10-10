# Coverage and limits

This maps selected risks to observable assertions. Test counts include parameterized variations, not code-coverage percentages or distinct business features.

## API and consumer checks

| Risk | What is checked | Source |
|---|---|---|
| Structurally correct but wrong product | Live status/media type/schema plus independent known seeded values | [HTTP checks](../tests/test_catalog.py), [helpers](../tests/contract_helpers.py) |
| Inputs silently coerced/ignored | Canonical ID bounds, exact boolean filter, duplicate/unknown query rejection and expected error fields | [HTTP checks](../tests/test_catalog.py), [API contract](api-contract.md) |
| Schema too weak to detect violations | Required fields, wrong types (including boolean-as-price), bounds, whitespace, error envelope and nested list path | [Schema guards](../tests/test_schema_guards.py) |
| Additive response field incorrectly classified as breaking | Unknown product/error fields accepted by tolerant consumer; known field values still asserted | [Schema guards](../tests/test_schema_guards.py), [compatibility cases](../tests/test_compatibility.py), [consumer policy](../tests/test_consumer_policy.py) |
| JSON Schema integer confused with lexical number formatting | Integral numbers accepted; fractional prices rejected at the precise field | [Consumer policy](../tests/test_consumer_policy.py), [API contract](api-contract.md) |
| Required response field removed/renamed or type changed | Exact keyword, instance/schema path and missing field; old consumer stays unchanged | [Compatibility cases](../tests/test_compatibility.py), [explicit verifier](../scripts/verify_compatibility.py) |
| New consumer accepts malformed nested price | v2 required nested fields, nonnegative integer amount and synthetic USD policy | [Compatibility cases](../tests/test_compatibility.py) |
| Any unrelated failure mistaken for defect detection | Identity/protocol/exit checks; verifier rejects wrong fields, paths, extra errors and false success | [Verifier regressions](../tests/test_compatibility.py) |
| Assertion failure leaks app/server | Explicit-only nested failing probe has exact assertion, zero teardown errors and stopped lifecycle | [Fixture cleanup regression](../tests/test_fixture_cleanup.py) |
| A ported check loses Python's critical expectations | Ten local requests/four assertions each, exact independent values/order/error code/message, packaged export consistency | [Postman source](../postman/checks.js), [parity regressions](../tests/test_postman.py) |
| CLI failure misrepresented as precise contract detection | Schema-valid wrong-price probe proves status/media/schema pass and known-values fail; connection refusal is separately detected | [Postman regressions](../tests/test_postman.py) |
| Structural port rejects additive/integral values or misses violations | Selected additive/integral positives and field/type/bound/status/media negatives against synthetic local probe server | [Postman regressions](../tests/test_postman.py) |
| JavaScript/Python disagree on nonblank Unicode strings | Explicit Python-compatible whitespace class; all 29 whitespace characters and selected valid/invalid boundaries for SKU/name/error message, checked with both validators | [Postman source](../postman/checks.js), [parity regressions](../tests/test_postman.py) |
| Structural port misses malformed list/error responses | Envelope/item/type/required-field/code/message negatives; empty-list and additive list/error positives with named schema outcomes | [Postman regressions](../tests/test_postman.py) |

## Practice reliability

The M1B/M2 runners are tested with synthetic temporary histories, not personal answers. Tests cover new attempts retaining prior work, revisions and assistance, pause/monotonic timing, score/sample arithmetic, scope/version separation, interrupted/error states, atomic write failure, corrupt history, locking and local path boundaries.

Objective coding tasks must accept specified valid examples and reject specified wrong behavior. Structured predictions are deterministic; explanations are saved for rubric review. Starter/solution checks and topic variants belong to the [learning track](../learning/README.md).

The [M2 regressions](../tests/test_m2_learning.py) cover all four starters/reference solutions, shortcuts, full CLI completion, full/focused seed equivalence, fresh-work preservation, schema-1/2 coexistence, invalid records, exact averages/paused timing and failed repeat checks. The [M2 guide](../learning/m2-track.md) lists the selected behavior probes and their limits.

Assessment/checker version 2 adds regression evidence for the three review false passes, v1/v2 identity/availability omissions and invalid values, rejection of valid zero/positive/integral/additive examples, full/focused prediction totals, old/new version separation and historical readback. CLI integration waits for its workspace with a bounded deadline, not an unbounded startup `readline()`. This is selected behavior coverage, not a universal proof that arbitrary learner code is correct.

Personal `.practice-data/` never belongs in commits or CI artifacts. Local exercise execution is trusted code, not sandboxed submissions or anti-cheating verification.

## Deliberate gaps

- Production authentication, writes, persistent inventory, roles, concurrency/load and security audit.
- Live v2 service, universal API/schema diff analysis and real consumer migration.
- Complete malformed-HTTP or framework error normalization beyond documented GET routes.
- Automated explanation grading, adaptive AI coach or full Lab 0-7 assessment.
- Automatic Lab 6 scoring or a local machine-readable CLI assertion protocol; current official CLI export requires login. Console inspection is used in selected regressions, not learner scoring.
- Guarantees of retained knowledge, equivalent difficulty across every random variation or trustworthy self-managed attention time.

Current executed platforms, counts and hosted results are recorded in [progress](progress.md). Workflow configuration alone is not evidence of CI success.
