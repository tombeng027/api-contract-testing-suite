# Lab 6: port a critical API check to Postman

This is a manual reference lab, not a scored practice-runner track. M1B/M2 saved attempts remain unchanged. The approved M3 tool is the official Postman CLI, not Newman; see [the tool decision](../../docs/postman-parity.md).

## Predict

Before running anything, write your answers in your own local notes:

1. Product 1 returns HTTP 200 with an integer price of 2500. Independently expected price is 2501. Which assertion should fail?
2. A valid missing ID returns HTTP 404 and the documented error. Is that a failed request or a successful negative test?
3. The target is not listening. Can exit 1 alone prove a contract defect?
4. A response adds `category`. Should the selected v1 consumer reject it?

## Execute

From the repository root after [Python setup](../../README.md#setup-windows-powershell):

```powershell
npm ci
npm audit
.\.venv\Scripts\python.exe -m catalog_api
```

Keep that server terminal open. In a second terminal at the repository root:

```powershell
.\.venv\Scripts\python.exe scripts\run_postman.py --base-url http://127.0.0.1:8001
```

The wrapper prints the CLI exit and paths to retained raw console/error evidence. Open those files. Expect ten requests and forty assertions, with zero failures. The CLI may print a login reminder: no login is required for this local run. Do not sign in to obtain reports or upload your notes. Stop the manual API with Ctrl+C afterward.

For automatic isolated verification, without a manual server:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_postman.py -q
```

The tests start their own ephemeral targets. The controlled negative examples are expected failures inside the tests, not failures of the ordinary suite.

## Inspect

Import [the collection](../../postman/catalog.postman_collection.json) and [the local environment](../../postman/catalog.postman_environment.json) into Postman if you already use the app. No app installation is required for CLI execution.

Read the collection-level post-response script. It runs four named tests for every request:

| Test | Responsibility |
|---|---|
| `status` | Exact documented HTTP status |
| `media-type` | JSON media type, allowing charset parameters |
| `schema` | Selected equivalent v1 structure/type/bounds rules |
| `known-values` | Independent seeded values/order or exact error code/message |

The JavaScript structural assertions are not a Draft 2020-12 validator. Python keeps the independent JSON Schemas. Port the expectation, not merely the syntax, and retain additive response tolerance.

## Change, verify, explain

1. Make a private copy of the collection outside the tracked source.
2. In `product-one`'s pre-request script, change only its independently expected `price_cents` from 2500 to 2501.
3. Run the copy using the pinned CLI and explicit local environment. Do not use `--suppress-exit-code`, `--bail` or `--output`.
4. Confirm that transport/status/media/schema succeed and the **known-values** assertion fails with actual 2500 versus expected 2501.
5. Restore the expected value in your copy and rerun. Never edit the API to make a wrong expected price appear correct.
6. Explain why a wrong price can remain schema-valid. Explain why a refused connection is an environment failure, not the same evidence.

Raw CLI example for a copy in the current directory:

```powershell
.\node_modules\.bin\postman.cmd collection run .\my-collection.json --env-var base_url=http://127.0.0.1:8001 --no-report-events --disable-unicode --ignore-redirects --timeout 20000 --timeout-request 2000 --timeout-script 2000 --no-insecure-file-read --working-dir .
```

Only run trusted synthetic collections. Script execution is not a security sandbox. The wrapper restricts its base URL, but arbitrary trusted scripts may still initiate other requests; do not add network calls, secrets or real business data.

## Common incorrect approaches

- Checking only HTTP 200: misses business values and expected error contracts.
- Treating any nonzero exit as proof of the intended failure: also hides connection/script/tool failures.
- Using JavaScript integer checks without rejecting booleans/types first.
- Forbidding unknown response fields: changes the agreed tolerant consumer policy.
- Confusing selected equivalent constraints with universal cross-validator parity.
- Parsing terminal output into personal scores: automatic Lab 6 scoring is deliberately deferred.

After your attempt, compare with the [separate reference explanation](../solutions/06-postman-parity.md). Answers, repetition counts and timing for this lab are manual; there is no `--lab 6` runner command.
