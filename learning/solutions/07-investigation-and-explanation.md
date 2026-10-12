# Lab 7 reference explanation

Use this after completing [Lab 7](../labs/07-investigation-and-explanation.md). The probes are controlled synthetic examples, not live incident evidence.

## Probe A: wrong test expectation

The wrong-price probe receives HTTP 200. Status, media type and schema pass. Only `known-values` fails: the response contains `price_cents: 2500`, while the deliberately changed expectation is `2501`.

That establishes a disagreement with this test oracle, not a defect in the API. The repository contract lists product 1 at 2500 cents. The correct action is to restore the independent expected value after checking the contract source—not to change the API or loosen the schema. The pytest test passes because it asserts that the synthetic failure is precise.

## Probe B: schema incompatibility

The fixture's `price_cents` value is the string `"2500"`. The v1 consumer requires an integer, so the exact failure is `type` at `["price_cents"]`. Exit 1 is expected for this single deliberately incompatible probe.

This says that this fixture is incompatible with this consumer policy. It says nothing about a live service unless the response was actually captured from the intended endpoint, environment and version. Keep the old v1 expectation stable; either preserve it in the producer or deliberately version and migrate the contract. The eight-case verifier exits 0 because it checks both expected-compatible and expected-incompatible outcomes.

## Probe C: connection failure

The test briefly reserves a localhost port, closes it, and targets that port. The CLI reports `ECONNREFUSED`; no HTTP status or JSON body exists to validate. Its nonzero exit is expected, so the pytest regression passes after confirming that failure signature.

That diagnoses the controlled test setup only. In an actual incident, investigate the requested URL, server readiness, listener/port, network route and proxy configuration. Do not translate transport failure into a fabricated HTTP error or a product-contract result.

## Demo summary

A concise, evidence-led explanation might be:

> “I separated three different causes of a red run. The wrong-price case passed transport and schema checks but failed the independently known business value, so the deliberate fault was in the oracle. The type-change fixture failed the v1 integer constraint at `price_cents`, proving that fixture is incompatible with that consumer—not that a live endpoint is broken. The refused-connection case had no HTTP response, so it is an environment/transport failure. I would verify the source contract and target environment before changing production behavior.”

Good investigations also state limits: the examples are synthetic; the schema fixture is not live traffic; a CLI exit alone does not identify root cause; and a passing localhost smoke test does not certify a deployed service.
