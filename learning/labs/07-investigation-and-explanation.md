# Lab 7: investigate and explain a test failure

This is a manual evidence-triage and demo lab, not a scored runner track. Use the repository's synthetic fixtures only. Do not weaken contracts or edit production code to make an observation disappear.

## Goal

Given a red test or failed CLI assertion, identify what the evidence actually proves, distinguish a faulty expectation from a contract incompatibility or an environment failure, and explain an appropriate next action.

## Predict

Before running the probes, write down:

1. What would distinguish an incorrect business expectation from an invalid API response?
2. What exact evidence would establish a v1 schema incompatibility?
3. What can you conclude if the CLI reports a refused connection and has no HTTP response?
4. Which evidence would you need before calling any one of these the cause of a real production incident?

## Prepare

From the repository root, use the configured Python environment and install the local Postman CLI if needed:

```powershell
.\.venv\Scripts\python.exe -m pip install -c constraints.txt ".[test]"
npm ci
npm audit
```

Postman probes need the pinned local CLI; run the commands from the repository root. No manual API server, sign-in or real business data is needed.

## Probe A: wrong test expectation

Run the controlled wrong-price example:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_postman.py -k schema_valid_wrong_price_fails_exact_business_assertion -q
```

Pytest should report one passing test. That test deliberately runs a Postman assertion expected to fail, then verifies the exact result in retained raw evidence. Open the newest evidence folder and inspect its output:

```powershell
$run = Get-ChildItem artifacts\postman-parity\postman -Directory |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1
Get-Content (Join-Path $run.FullName 'stdout.txt')
```

Expected signature: one request, zero failed requests, four assertions with one failure. `status`, `media-type` and `schema` pass; `known-values` reports actual `2500` versus expected `2501`.

Diagnosis: the synthetic API response matches the documented seeded price; the controlled test oracle is deliberately wrong. Do not change the API or schema. Identify the independently documented expectation, restore it in the private probe, and rerun.

## Probe B: schema incompatibility

Run the exact fixture probe:

```powershell
.\.venv\Scripts\python.exe scripts\contract_probe.py --example type_changed --consumer v1
```

Exit 1 is expected for this deliberately incompatible fixture. Inspect the JSON: `compatible` is false; exactly one failure has keyword `type`, instance path `["price_cents"]`, and says the string `"2500"` is not an integer.

Diagnosis: this fixture violates the unchanged v1 consumer contract. It is not evidence that a live endpoint currently returns this value. A real incident would require capturing the actual response and matching it to the endpoint/version under investigation. If confirmed, fix the producer to preserve v1 or plan and publish a versioned migration; do not silently weaken v1.

Verify that the repository classifies the controlled compatibility examples precisely:

```powershell
.\.venv\Scripts\python.exe scripts\verify_compatibility.py
```

Expected overall exit 0, with all eight expected compatibility outcomes printed. The `type_changed` example itself remains intentionally incompatible.

## Probe C: environment failure

Run the controlled refused-connection case:

```powershell
$evidence = "artifacts\lab7-connection-$([guid]::NewGuid().ToString('N'))"
.\.venv\Scripts\python.exe -m pytest tests\test_postman.py -k connection_failure_is_not_contract_success -q --basetemp $evidence
$raw = Get-ChildItem $evidence -Filter stdout.txt -File -Recurse | Select-Object -First 1
Get-Content $raw.FullName
```

Pytest should report one passing test because it verifies that the CLI exits nonzero and its output contains `ECONNREFUSED`. The raw output is retained below the unique `artifacts\lab7-connection-*` folder; using a unique base avoids overwriting older evidence.

Diagnosis: no HTTP response was received, so no API status, body or schema was evaluated. This is evidence of a connection failure in this controlled probe, not a product-contract failure. In a real incident, check the intended base URL, service readiness, port, network path and proxy/configuration before drawing a conclusion.

## Triage and explain

For each probe, complete this short incident note in your own local notes:

| Question | Your observation |
|---|---|
| What failed, and in which layer? | |
| What exact output supports that? | |
| What does the evidence not prove? | |
| What is the smallest safe next action? | |
| What command or observation would verify that action? | |

Use this explanation order for a short demo:

1. **Symptom:** state the command and outcome.
2. **Evidence:** name the exact request/assertion or schema keyword/path; distinguish HTTP response from no response.
3. **Diagnosis:** explain why this is an oracle, contract, or environment issue.
4. **Action:** identify the smallest correction without hiding a real contract break.
5. **Verification and limit:** say what you reran and what remains unproven.

Do not claim a root cause from a nonzero exit code alone. A failed assertion, incompatible fixture, unavailable service, CLI setup error or script error can all yield a nonzero result.

## Verify and reflect

The probes above verify diagnosis using controlled synthetic failures; they do not change tracked source. For a passing API baseline, run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_catalog.py -m smoke -v
```

Expected exit 0 for the two smoke tests. This proves the local synthetic health/product checks passed in that run; it does not prove a separate service, deployment or production incident is healthy.

After your attempt, compare with the [separate reference explanation](../solutions/07-investigation-and-explanation.md). Notes and demo explanations are not saved, timed or graded. Lab 7 adds no runner command and does not alter M1B/M2 scoring or history.
