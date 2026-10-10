# Postman parity: M3 tool decision and boundaries

## Approved change from the original plan

The original M3 proposed Newman. Initial installation of the latest release, 6.2.3, produced an npm audit result flagging 19 dependency packages, including a critical advisory. This is dependency metadata, not a claim that this synthetic project was exploited.

The user chose not to adopt Newman or force dependency overrides. Newman was removed from the project. The user then approved project-local official **Postman CLI 1.71.0**, pinned with a committed npm lockfile. `npm audit` reports zero findings in that package tree. The CLI is a vendor binary: this result is **not** an audit of its bundled internals or security certification.

Local execution was verified without login, credentials or a cloud collection ID. The wrapper uses a local unlinked collection file, an explicit `127.0.0.1` base URL, `--no-report-events`, bounded request/script/process timeouts, disabled redirects and file-read restrictions. It disables inherited HTTP proxies for these localhost runs.

The CLI's `--output` machine-readable YAML export rejected execution without login. The user explicitly chose to defer automatic Lab 6 scoring rather than add account/cloud requirements or a fragile console-output grading parser. Accordingly:

- M3 delivers the portable collection/environment, pinned local execution, selected parity/failure regressions and Lab 6 guide/reference explanation.
- No Lab 6 runner track, answer persistence, statistics or automatic score is claimed.
- M1B/M2 versioned history, scope, scoring and commands are unchanged.
- Raw console/evidence is retained locally. Regression tests inspect selected pinned output; production code does not parse it into scores.
- No sign-in, API key, cloud publication or linked collection is used. Disabling run-event reporting is not a proof of zero vendor telemetry; use synthetic data only.

## Setup and execution

Install Python using the [main setup](../README.md#setup-windows-powershell). Install Node 24, then run from this repository:

```powershell
npm ci
npm audit
```

This is a local dependency installation, not a global CLI install. The executed local versions are Node 24.14.0 / npm 11.9.0 / Postman CLI 1.71.0. Other permitted Node/platform combinations are not certified by those local results.

Start the synthetic API in one terminal:

```powershell
.\.venv\Scripts\python.exe -m catalog_api
```

Run in another:

```powershell
.\.venv\Scripts\python.exe scripts\run_postman.py --base-url http://127.0.0.1:8001
```

The wrapper returns CLI exit 0 or 1 unchanged. Setup/version/timeout/process errors are explicit exit 2. Exit 1 can mean a contract assertion **or** another failed run; inspect the retained stdout/stderr rather than infer the cause from the code alone. No success summary is manufactured from a failed run.

The wrapper finds the platform-local pinned binary under `node_modules/@postman`. When running outside checkout, set `CATALOG_POSTMAN_CLI` to its absolute executable path:

```powershell
$env:CATALOG_POSTMAN_CLI = (Resolve-Path .\node_modules\@postman\pm-bin-windows-x64\bin\postman.exe).Path
```

On Ubuntu x64 the equivalent binary is `node_modules/@postman/pm-bin-linux-x64/bin/postman`. CI sets the appropriate absolute path before running the installed Python suite outside checkout.

Re-export after editing [request expectations](../postman/requests.json) or [assertions](../postman/checks.js):

```powershell
npm run export:postman
.\.venv\Scripts\python.exe -m pip install -c constraints.txt ".[test]"
```

The exporter normalizes Windows newlines. The self-contained [collection](../postman/catalog.postman_collection.json) and [environment](../postman/catalog.postman_environment.json) can also be imported into Postman. Only the base URL is an environment variable; per-request expected values are independent test oracles.

## Selected parity

Ten requests, four named assertions each: product 1, zero-priced product 2, all products, both availability filters, valid missing ID, invalid ID, invalid filter, duplicate filter and unknown query.

Every response checks status, parsed JSON media type, structural constraints and independently expected known values. Successful lists also check expected length/order. Error bodies check exact code/message. Unknown response fields remain tolerated.

The JavaScript `schema` test manually implements the selected v1 constraints; it is not an invocation of the Python Draft 2020-12 validator. Numeric integral floats are accepted mathematically; booleans, fractions and string numbers are rejected. The [regressions](../tests/test_postman.py) verify selected positive/negative examples and matching packaged expectations, not universal schema-engine equivalence.

Nonblank strings follow the existing Python Unicode `\S` behavior using an explicit JavaScript character class. Whitespace-only U+0085 and U+001C-U+001F fail; U+FEFF and U+200B remain structurally valid. This preserves the Python contract rather than imposing a new visual-text policy. Regressions exercise all 29 Python whitespace characters, empty/mixed strings, non-whitespace boundaries and padded text for SKU, name and error message against both Python schemas and the actual pinned CLI.

Additional list/error probes check malformed envelopes/items, missing fields, wrong types, blank messages and unknown error codes, plus valid empty lists and additive list/error fields. Every probe checks transport/status/media success and the expected named schema outcome; valid cases also pass independent known-value checks. These are synthetic test oracles, not learner grades.

Synthetic raw parity evidence is ignored under `artifacts/postman-parity/` and retained by CI. Personal histories and learner collection copies are never included. The wrapper's manual evidence defaults to unique directories under `artifacts/postman/`. Custom output locations need their own privacy/backup controls.

## Remaining gate

Automatic Lab 6 assessment is deferred. Before introducing it, select a maintained local reporting mechanism that can provide complete structured execution/assertion identities without login, preserve first/final source evidence, and distinguish learner assertions from infrastructure failure. Do not silently replace M2 scoring with CLI exit codes.

## Sources checked for the tool decision

- [Official CLI installation](https://learning.postman.com/docs/postman-cli/postman-cli-installation/): npm package `postman-cli`, vendor platform binaries.
- [Official local collection execution](https://learning.postman.com/docs/postman-cli/postman-cli-run-collection/): collection-file execution without an API key.
- [Collection command/options](https://learning.postman.com/docs/postman-cli/postman-cli-collections/): local/unlinked collections and run-event reporting options.

Actual pinned runtime verification overrides a documentation-only assumption: local execution worked, but `--output` required login. No authentication workaround was attempted.
