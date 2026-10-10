# API Contract Testing Suite

[![QA verification](https://github.com/tombeng027/api-contract-testing-suite/actions/workflows/qa.yml/badge.svg)](https://github.com/tombeng027/api-contract-testing-suite/actions/workflows/qa.yml)

Personal QA learning and portfolio project: understand and test API response contracts, errors and compatibility as schemas evolve.

**Status: M1/M1B, bounded M2 and revised M3 Postman parity implemented and verified locally and on Windows/Ubuntu hosted CI.** M3 uses the official Postman CLI rather than Newman. Lab 6 automatic scoring and the full Lab 0-7 course remain deferred; see [the approved tool/scope decision](docs/postman-parity.md).

## Implemented foundation

- Read-only FastAPI catalog with fixed synthetic products, lookup/filtering and consistent errors.
- Independent Draft 2020-12 consumer schemas bundled with the package.
- Exact known-value assertions alongside schema checks; wrong-but-schema-valid price detection.
- Per-test application/server instances on pre-bound ephemeral localhost sockets.
- Bounded readiness/shutdown, lifecycle evidence, HTML and JUnit reports.
- [API contract](docs/api-contract.md) and [Lab 0-5 reference guides](learning/README.md).
- [Repeatable practice slice](learning/practice-slice.md): fresh workspaces, retained JSON answers/code evidence, first/final scores, pauses and history/statistics.
- [Controlled compatibility demonstration](docs/compatibility-example.md): eight precise consumer outcomes, including a fixture-only v2 contract.
- [M2 interactive practice](learning/m2-track.md): versioned packaged manifest, full/single-lab attempts, seeded prediction variants, four code exercises, saved explanations and task-level observations.
- [Postman parity](docs/postman-parity.md): portable ten-request collection, forty critical assertions, pinned project-local CLI, raw console evidence, selected failure regressions and a manual [Lab 6](learning/labs/06-postman-parity.md).

Development and documentation are AI-assisted. Executed results are recorded separately from planned capabilities; learner mastery is not claimed.

## Setup (Windows PowerShell)

Open this repository as your working directory:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -c constraints.txt ".[test]"
.\.venv\Scripts\python.exe -m pip check
```

Uses a non-editable installation. After changing application/schema source, rerun the install command. Constraints capture the verified environment's versions, not a hash-verified universal lockfile.

Python metadata permits 3.12-3.14; executed versions are Windows 3.14.3 locally, Windows 3.14.7 and Ubuntu 3.14.8 in hosted CI. On Linux/macOS use `python3 -m venv .venv` and `.venv/bin/python`; macOS and Python 3.12/3.13 remain unverified.

For the combined suite including Postman checks, install Node 24, then:

```powershell
npm ci
npm audit
```

This installs the pinned Postman CLI locally; no global install or login is required. `npm audit` covers the npm package tree, not the vendor binary's internals. See [tooling boundaries](docs/postman-parity.md).

No browser download, Docker, cloud credentials or Repo 1 dependency is required. Installation needs internet/package availability; tests use localhost with environment proxies disabled.

## Run tests

```powershell
.\.venv\Scripts\python.exe -m pytest --html=artifacts/report.html --self-contained-html --junitxml=artifacts/results.xml
.\.venv\Scripts\python.exe -m pytest -m smoke -v
```

Smoke: 2 selected success/error cases. The default suite includes the API/schema foundation and runner regressions; see [current results](docs/progress.md). Tests start their own servers; no manually running API is needed. Assertions determine expected success or rejection, not HTTP status alone.

Generated evidence is ignored under `artifacts/`; lifecycle logs are named by test identity hash. Each run replaces that test's lifecycle evidence, so copy it before rerunning if needed.

## Try the API

```powershell
.\.venv\Scripts\python.exe -m catalog_api
```

In another terminal:

```powershell
curl.exe -i "http://127.0.0.1:8001/v1/products/1"
```

Stop your manual server with Ctrl+C. It binds localhost only; do not deploy this synthetic target publicly. Port conflicts are explicit errors, not reasons to kill another user's process.

## Verified evidence and limitations

- Current local post-M3 hardening suite: **236 passed in 101.03s** outside checkout against the non-editable repository environment; zero failures/errors/skips. Five added parameterized cases cover Python-compatible Unicode nonblank checks and selected malformed/additive list/error responses using the pinned CLI. M2 assessment/checker versions remain unchanged. Hosted verification of these follow-up changes is not yet claimed.
- Revised M3 baseline: **231 passed in 74.91s** outside checkout against the non-editable repository environment; zero failures/errors/skips. The added 16 Postman cases verify the export, critical live checks, selected positive/negative oracles, refused connections, missing/versioned tooling, URL restrictions and owned-process timeout cleanup.
- M2 hardening baseline: **215 passed in 58.73s** outside checkout against the non-editable repository environment; zero failures/errors/skips. Includes 37 M1B runner cases, 89 M2 learning cases, 26 compatibility cases, three consumer-policy cases and one failure-cleanup regression alongside the 59-case foundation.
- Pre-hardening clean-install baseline: **160 passed in 47.96s** outside checkout against the second clean non-editable environment.
- [Verified hosted source run](https://github.com/tombeng027/api-contract-testing-suite/actions/runs/37922477474): Windows/Python 3.14.7 **160 passed in 28.39s**; Ubuntu/Python 3.14.8 **160 passed in 22.55s**. Both downloaded artifacts matched their SHA-256 digests; inspected JUnit, reports, all 35 shutdown logs and eight compatibility outcomes per runner.
- Repeat checks now supersede stale passing scores; an infrastructure-error recheck cannot complete an attempt. Original pre-M2 v1 history was read without rewriting and retained its first/final scores.
- Every M2 starter failed its intended objective checks; all four reference solutions passed. A full installed CLI run saved all 12 activities and score/check evidence, then released the writer lock. This was synthetic reference-driven verification, not learner achievement.
- Review false passes for exact Python integer prices, additive tolerance and full v1/v2 compatibility now have regressions. New M2 assessment/checker version 2 keeps historical version-1 scores separate rather than regrading them. Overall prediction totals now count all selected tasks and agree with task-level counts.
- [M2 hardening hosted run](https://github.com/tombeng027/api-contract-testing-suite/actions/runs/37927167145): Windows **215 passed in 49.91s**, Ubuntu **215 passed in 37.67s**, including eight exact compatibility outcomes on both platforms.
- M3 local collection run: ten requests / forty assertions / zero failures, without login; all 37 combined server lifecycle logs stop. Selected intentional failures are retained separately under ignored synthetic parity evidence. Automatic Lab 6 scoring remains deferred by user decision.
- [M3 hosted source run](https://github.com/tombeng027/api-contract-testing-suite/actions/runs/37930136864): Windows **231 passed in 66.70s**, Ubuntu **231 passed in 35.93s**. Both downloaded artifact digests matched; inspected JUnit, all 37 shutdown logs, eight compatibility outcomes and successful/controlled-negative Postman evidence per runner.
- Synthetic full-slice CLI run verified saved answers/code evidence, first score 50% versus revised final 100%, review and writer-lock release.
- Initial default suite: 59 passed in 18.80s; follow-up default suite: 59 passed in 18.50s.
- Final suite outside the checkout using importlib mode and installed target: 59 passed in 18.50s, zero failures/errors/skips.
- All 34 server-backed lifecycle logs ended with `app_stopped`.
- Bundled schemas and installed package locations checked from outside the checkout.
- Lab 0/1 reference commands/manual requests and Lab 2-5 pytest selections/compatibility commands executed successfully. The Lab 5 single incompatible probe intentionally exits 1 with its precise type failure.
- `pip check` passed.

The reviewed assertion-failure probe also stopped its owned server with zero teardown errors; all 35 ordinary/probe lifecycle logs ended in `app_stopped`. This verifies that selected failure path, not every possible failure.

See [current progress/review](docs/progress.md). This verifies the selected Windows/Ubuntu Python 3.14 jobs, not every permitted runtime/platform, a mutation coverage percentage or a security audit.

VS Code's test tool found no tests and Pylance reported missing pytest while selecting another parent-workspace interpreter. Explicit repo-venv commands are verified; editor selection/discovery is not claimed fixed. Open this repository directly and select `.venv\Scripts\python.exe`.

## Later scope

- Automatic Lab 6 scoring with maintained, complete local machine-readable reporting that requires no login. Current CLI `--output` is login-gated; no console-output grading workaround is used.
- Lab 0/1/6/7 interactive assessments and the complete eight-lab course.
- Lab 7 guide, broader failure-path evidence and additional runtime/platform portability.

## Run the Postman collection

With the manually started API above running, use another terminal at the repository root:

```powershell
.\.venv\Scripts\python.exe scripts\run_postman.py --base-url http://127.0.0.1:8001
```

Expect ten requests and forty assertions with zero failures in the printed console-evidence file. Exit 1 means a failed run; inspect its precise cause. Tool/setup/timeout errors are explicit exit 2. The default pytest suite starts its own isolated targets, so it needs no manual API. See [Lab 6](learning/labs/06-postman-parity.md) for the controlled wrong-price exercise.

This complements the UI/API work-order project rather than duplicating its browser workflows. It is not a production service, security audit or universal compatibility analyzer.

## Learn alongside the suite

The [guided learning track](learning/README.md) will connect each concept to a small prediction, execution, investigation and coding exercise.

Start all four M2 labs or select one:

```powershell
.\.venv\Scripts\python.exe -m practice_runner start --track api-contracts-m2 --seed 42
.\.venv\Scripts\python.exe -m practice_runner start --track api-contracts-m2 --lab 3 --seed 42
.\.venv\Scripts\python.exe -m practice_runner stats --track api-contracts-m2
```

Use the printed task IDs and workspace paths; [M2 instructions](learning/m2-track.md) explain code signatures, scoring, history and boundaries. Existing M1B commands remain available unchanged.

The working suite and learner exercises are separate. Unfinished learner code is not discovered by the ordinary passing test command. Runner solution reveals are explicitly logged; reading Markdown references is not tracked. Generated materials are not proof of learner mastery. See [the working slice](learning/practice-slice.md) for commands and [the broader runner plan](learning/runner-plan.md) for future scope.

All examples use synthetic data and local services. No employer information or cloud credentials are required.
