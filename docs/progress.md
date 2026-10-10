# Repository 2 progress

Updated October 9, 2026. Record verified work separately from planned features.

## Milestone status

| Milestone | Status |
|---|---|
| M1 API foundation | Implemented, reviewed and locally verified |
| M1B repeatable-learning slice | Implemented; local verification recorded below |
| M2 version evolution / remaining contract labs | Implemented, published and locally/hosted verified: compatibility plus interactive/reference Labs 2-5 |
| M3 Postman parity | Revised user-approved scope implemented and locally/hosted verified: official CLI, portable collection, manual Lab 6; automatic scoring deferred |
| M4 clean-install portability, hosted CI and presentation | Local/Windows/Ubuntu verification and source publication done early; broader presentation remains pending |

## M1 delivered

- Documented [seed values, route/input/error policy](api-contract.md).
- Minimal independent FastAPI catalog with per-app seeds; no database/auth/UI.
- GET product/list/filter/readiness; invalid ID/filter, duplicate and unknown-query rejection.
- Independent local Draft 2020-12 product/list/error schemas.
- Live HTTP checks for status/media type/schema and exact known values.
- Schema guards assert exact failure rules/paths for missing fields, types and boundaries.
- Additive response tolerance matches the consumer policy, including known-field business assertions.
- Wrong-price example passes structural validation but fails the semantic assertion for the precise expected reason.
- Function-scoped server/client fixtures, pre-bound ports, bounded readiness/shutdown and explicit thread-error propagation.
- Lifecycle logs, pytest-html/JUnit reporting, independent venv, dependency snapshot and package resources.
- [Lab 0](../learning/labs/00-test-anatomy.md) / [Lab 1](../learning/labs/01-http-exchange.md) guides and separately linked explanations.

## Execution evidence

Windows 11 / Python 3.14.3; HTTPX 0.28.1, jsonschema 4.26.0, pytest 9.1.1.

| Execution | Result |
|---|---|
| Initial suite | 59 passed in 18.80s |
| Follow-up suite | 59 passed in 18.50s |
| Final installed-target run outside source checkout, importlib mode | 59 passed in 18.50s |
| Lab 0 product command | 1 passed |
| Lab 0 schema/business guard | 1 passed |
| Lab 1 smoke command | 2 passed, 32 deliberately deselected |
| Lab 1 filter/query selection | 15 passed, 19 deliberately deselected |
| Dependency consistency | `pip check` passed |
| Manual entrypoint and five documented curl requests | 200, 404, 200, 422, 422 with expected responses |

Final JUnit: 59 cases, zero failures/errors/skips. Composition: 34 live-HTTP cases and 25 schema/oracle cases; parameterized variations are not separate business features. All 34 lifecycle log files ended with `app_stopped`.

From a working directory outside checkout, explicitly selected the repo interpreter and verified `catalog_api`/`contracts` imported from site-packages and all three packaged schemas were valid. This uses the new repository's initial non-editable installation, not a second independent clean-install certification.

Manual server responsiveness was verified and the owned preview process was stopped afterward. It is not left running.

Pylance syntax checks found no syntax errors in the app and fixture. Editor diagnostics reported missing pytest because Pylance still selected another parent-workspace environment; the editor test tool found no tests. No claim of clean project-wide type analysis or fixed editor discovery. Repo-local settings and explicit executable commands are provided.

## M1 review against the plan

| Gate | Evidence / conclusion |
|---|---|
| Explicit API expectations | Documented canonical ID bounds, exact query policy, seeded ordering and error codes/messages |
| Independent checks | Schemas/expected seeds are maintained in contracts/tests, not imported from app logic |
| Schema versus semantics | Exact known-value guard demonstrated against structurally valid wrong price |
| Isolation and lifecycle | Each HTTP case gets a fresh app/socket/client; successful-run shutdown evidence inspected |
| Learning clarity | Small reference commands executed; predictions and explanations are separate |
| Honest scope | No interactive answers/scoring, v2 service, cloud, AI grading or hosted-CI claims |

No urgent blocker observed for this scoped foundation. Subsequent review added an explicit assertion-failure probe and a regression validating its exact failure, zero teardown errors and `app_stopped`. This proves that selected failure path, not all startup/teardown possibilities.

## Next

M1/M1B review is complete. Continue the bounded M2 learning expansion after the review verification below; compatibility examples are already implemented.

The slice's reset, persistence, grading and interruption checks pass. Preserve those gates while expanding: [runner acceptance plan](../learning/runner-plan.md).

Source is now published to the user-approved GitHub destination; hosted evidence is recorded below. Personal attempt data remains ignored by design. Learner rehearsal/mastery remains user-owned and unverified.

## M1 full review and M1B implementation

Directly reviewed the API, schemas, fixture lifecycle, assertions, packaging and Lab 0/1 instructions against the agreed plan. No urgent API contract mismatch found. Added explicit failing-test cleanup verification rather than extrapolating from successful-run logs.

M1B provides:

- Local CLI start/history/review/stats and explicit token-based stale-lock recovery.
- One seeded status prediction, one ungraded explanation and one code assertion task.
- Unique fresh workspaces; retained prompt/assessment snapshots and submissions/revisions.
- Strict schema-versioned records, atomic saves, append-preserving history and terminal-record immutability through the runner.
- Source snapshots/digests, exact checker outcomes/evidence, recorded hints/solution reveals.
- First/final objective scores, explicit pause/monotonic duration and version/scope-separated statistics.
- EOF/Ctrl+C/quit handling, infrastructure-error classification and visible corruption exclusions.
- Isolated bounded exercise subprocesses for trusted local code, not a sandbox.

The slice is not the full eight-lab track. Scope selectors choose individual tasks, not numeric labs. Content/manifests are snapshotted by code; an external course-manifest authoring system is not yet provided.

Verification covers fresh starts preserving old work, revisions/rechecks, all-or-nothing objective scoring, assistance gates, wrong-answer completion, missing-task rejection, exact statistics, pauses and wall-clock changes, interrupted records, atomic write failures, invalid UTF-8/corrupt history, locking, path escape, checker timeout/output truncation and CLI flows.

A synthetic installed-runner CLI walkthrough outside checkout completed all three tasks with a revised prediction: first score 50%, final 100%; saved source/check evidence reviewed afterward, writer lock released. This was reference-driven verification using temporary synthetic history, not a user practice achievement.

Runner model/engine/storage/CLI/checker diagnostics contained no errors. Pylance marks the Unix cleanup branch inactive on this Windows environment; Unix behavior remains unverified. The editor's test runner still found no tests; explicit venv commands remain the verified runner.

Final combined installed-target run outside checkout: **89 passed in 25.29s**, zero failures/errors/skips. Composition: 34 HTTP + 25 schema/oracle + 1 failure-cleanup regression + 29 runner cases. An earlier combined run passed 88 cases in 25.92s before the invalid-UTF-8 regression was added. `pip check` passed; 32 relative documentation links checked.

All 35 inspected lifecycle files ended with `app_stopped`: 34 ordinary HTTP cases plus the explicit-only failing probe invoked by the cleanup regression. Its nested expected failure is not a failure in the default suite. Runner tests and CLI verification used synthetic temporary histories, not real user answers.

Known boundaries: unencrypted local history, no resume/delete/UI/cloud/AI, one writer, no anti-cheating guarantees, no resource sandbox and no full-course mastery claims. Incorrect completed attempts legitimately have low scores. Unsupported record versions report errors rather than silently migrating.

## M2 partial delivery and recovery verification

The background learning-expansion task was cancelled without producing M2 track files. Numeric lab selection and Labs 2-5 remain unfinished; no completion claim is made for them.

Delivered independent v1/v2 fixture consumer contracts, additive/removal/rename/type-change examples, an eight-scenario precise expected-failure verifier, consumer-policy regressions and a configured Windows/Ubuntu CI workflow. Hosted CI has not yet run.

Review reproduced a stale-success bug: a code submission passed, a same-source repeat check reported an infrastructure error, and completion/scoring still consulted the earlier submission. The record model now uses the latest submission/check for final scoring and completion, while preserving the first-submission score. Repeat checks must match the latest code snapshot. Four regressions cover learner failures, infrastructure failures, terminal error handling and mismatched repeat source.

Recovery verification against a second clean non-editable Windows/Python 3.14.3 installation, outside checkout:

- Runner selection: **33 passed in 5.63s**.
- Combined suite: **122 passed in 28.73s**, zero failures/errors/skips.
- Composition: 34 HTTP + 25 schema/oracle + 1 failure cleanup + 33 runner + 26 compatibility + 3 consumer-policy cases.
- All 35 lifecycle logs ended with `app_stopped`; `pip check` passed.
- All eight compatibility scenarios passed their precise verifier against the clean installation.
- An actual pre-M2 schema-v1 history artifact remained readable with first score 0 and final score 100; it was not migrated or rewritten.

Next: implement the bounded M2 learning track directly, verify packaged resources and CLI flows, then publish and inspect actual hosted CI.

## Post-recovery full review

Directly reviewed API input/response contracts, schema/oracle checks, fixture lifecycle, runner event validation/scoring, storage preservation, CLI interruption paths, checker protocol/process handling, packaging and publication configuration.

Found and reproduced an additional record-validation gap: code submissions/rechecks could carry `ungraded` outcomes and still be accepted as completed records. That outcome is now rejected for code, while explanation-only practice remains deliberately ungraded. Two regressions first failed against the old model and then passed after the fix. Two additional regressions verify storage rejects changed seeds and prompt snapshots even if the modified manifest is otherwise valid.

Verified baseline after the fix:

- **126 passed in 31.98s**, outside checkout against the second clean installed package; JUnit has zero failures/errors/skips.
- 37 runner + 26 compatibility + 3 consumer-policy + 34 HTTP + 25 schema/oracle + 1 failure-cleanup cases.
- Eight review/recheck regressions passed separately.
- All 35 lifecycle logs ended with `app_stopped`; installed resource checks and dependency checks passed.
- Original pre-M2 v1 history remained readable with unchanged scores. No default-data writer lock remained.
- Pylance still reports `reportMissingImports` for pytest/Pydantic while its environment tool selects the parent workspace interpreter. Explicit installed-repository/clean-environment execution passes; editor selection is not claimed fixed.

No urgent blocker remains for the bounded M2 continuation. Uncommitted source/publication and unexecuted hosted CI are explicitly pending, not hidden completion claims. The cancelled learning task is not running; implementation is proceeding directly.

M2 resumed with four reference guides and four separate solutions for Labs 2-5. Verified selections produced 2, 25, 1, 13, 5, 2 and 26 passing cases respectively; the eight-case verifier passed and the single type-change probe failed with exactly its expected type/path evidence. 84 relative documentation targets resolved. These are reference guides, not new runner-managed lab attempts; numeric lab selection, manifests and full M2 objective checks still require implementation.

## M2 interactive implementation

Implemented directly after recovery, without a replacement background task:

- Packaged strict version-1 course manifest for `api-contracts-m2`, generated lab snapshots and schema-2 attempt records.
- Full M2 selection or numeric `--lab 2/3/4/5`; same seed produces the same lab variant in either scope.
- 12 full-track tasks: four predictions, four rubric-reviewed explanations and four objective coding tasks. Full objective maximum is eight points; single-lab maximum is two.
- Fresh starter files per attempt, retained revisions/source/checker output/digests and recorded hints/solution reveals.
- Lab-specific code checks for independent business assertions, full v1 schema, exact error contracts and explicit v1/v2 consumer compatibility.
- First/final scoring preserves failed/revised answers; latest rechecks cannot inherit stale success. Unexpected runtime/protocol/import/timeout errors stop the attempt without credit.
- History/review support both record schemas without rewriting old records. Statistics select the track and separate full/focused scopes, with task-level first/final counts.
- Shared atomic persistence, content immutability, pause/timing, locking and interruption behavior remain in place.

Verification on Windows/Python 3.14.3:

| Gate | Result |
|---|---|
| Initial combined runner integration | 63 passed in 23.83s |
| Expanded M2 objectives/full CLI/resources | 31 passed in 18.28s before three final reliability cases were added |
| Final full installed suite outside checkout | **160 passed in 47.96s**, zero failures/errors/skips |
| Composition | 59 foundation + 1 failure cleanup + 37 M1B runner + 34 M2 learning + 26 compatibility + 3 consumer policy |
| Packaged manifest/templates/schemas | Verified in site-packages in both repository and second clean environments |
| Dependencies/lifecycle | `pip check` passed; all 35 logs ended with `app_stopped` |
| Old history | Actual pre-M2 v1 JSON read successfully, first score 0/final 100 unchanged |
| Full installed CLI | All 12 submissions saved, reference-driven first/final score 100, no leftover writer lock |
| Call compatibility | Pylance resolved all eight call sites for the extended `check_code` signature as compatible |
| Documentation | 94 relative paths resolved before final checkpoint edits |

The final M2 cases also verify intended starter failures, shortcut rejection, seeded variant diversity, first/final revisions, assistance gates, exact averages/paused duration, wrong-answer completion, fresh resets, scope isolation, corrupt/versioned history, workspace errors and CLI exit behavior.

M2 is locally complete for its bounded Lab 2-5 scope. The complete eight-lab interactive course, AI coach and Postman/Newman remain out of scope for this milestone. Hosted execution/publication is the next verification gate; local success is not a CI claim.

## Source publication and hosted evidence

Initial source commit: `f70f305342e45a691320e3670c1a5b7823a2acd6`, pushed normally to [the approved repository](https://github.com/tombeng027/api-contract-testing-suite). Only 78 intended source/test/config/documentation files were staged. Practice history, local reports, virtual environments and private job-search documents were excluded.

[Hosted run 37922477474](https://github.com/tombeng027/api-contract-testing-suite/actions/runs/37922477474) completed successfully for that exact source commit:

| Platform | Interpreter | Pytest result |
|---|---|---|
| Windows hosted | Python 3.14.7 | 160 passed in 28.39s |
| Ubuntu hosted | Python 3.14.8 | 160 passed in 22.55s |

Both jobs completed constrained non-editable installation, dependency checks, installed resources outside checkout, the full suite outside checkout, explicit compatibility verification and artifact upload.

Downloaded both artifacts and matched ZIP SHA-256 digests:

- Windows artifact 11612353288: `beacb2c7bdae4c04c4b9259dbff01adae0212a37ec421d8e97926d67c8c207cd`.
- Ubuntu artifact 11611754634: `07ba4dd1ec35203d023bb277fb84849ef7f650997b1d6dddf07cdaabe7abf2a0`.

Inspected retained HTML/JUnit evidence: each has 160 tests, zero failures/errors/skips, all 35 lifecycle logs ending with `app_stopped`, and the eight compatibility cases with expected exits `0,0,1,1,1,1,0,0`. JUnit suite durations are 28.372s and 22.541s respectively; the table uses pytest's displayed total duration. The artifacts include synthetic verification only and expire after seven days.

This verifies the selected Ubuntu process-cleanup/path behavior as well as Windows regressions. It does not certify every possible subprocess, platform, Python 3.12/3.13 or user-written exercise. No user learning-achievement claim follows from reference-solution tests. M3 Postman/Newman is next; the full Lab 0-7 course and broader presentation remain pending.

## Post-M2 review and assessment hardening

The published 160-case baseline passed again, but direct review reproduced three incorrect learner implementations receiving credit: Lab 2 allowed an integral float despite its exact Python-int requirement; Lab 3 rejected permitted additive fields; Lab 5 checked prices without full product identity/availability and accepted only zero-valued v2 prices. Overall prediction counters also reported zero for four correctly answered M2 predictions, although task-level counts were correct.

Added regressions first: all five selected checker/statistics cases failed against the installed old package. Hardened the selected behavior probes without weakening the consumer schemas or changing the prompt/point maximum. Prediction aggregation now enumerates every selected prediction task and uses its first submission in completed attempts.

New M2 attempts explicitly snapshot assessment/checker version 2 from the packaged manifest. Version-1 M2 and original M1B records remain readable, with no rewriting/regrading; old/new assessment averages stay separate. Mixed assessment/checker versions are rejected, and historical M2 sessions cannot submit against the new checker. Status/history now expose both versions. Content/generator versions remain 1.

Local Windows/Python 3.14.3 verification after hardening:

| Gate | Result |
|---|---|
| Practice regressions before final additional matrix/count cases | 115 passed in 33.13s |
| Full installed suite outside checkout | **215 passed in 58.73s**, zero failures/errors/skips; preceding integration runs passed 214 in 63.53s and 59.36s |
| Composition | 59 foundation + 1 failure cleanup + 37 M1B runner + 89 M2 learning + 26 compatibility + 3 consumer policy |
| Selected regression additions | 55 cases covering false passes, required/invalid fields, valid-payload rejection, history/version separation, focused totals and startup readiness |
| Starters/reference solutions | All four starters fail; all four reference solutions pass, including full CLI completion |
| Compatibility | All eight exact expected outcomes verified separately |
| Resources/dependencies/lifecycle | Installed package resources verified; `pip check` passed; all 35 lifecycle logs ended with `app_stopped` |
| Historical readback | Actual pre-M2 schema-1 JSON unchanged, first 0/final 100; version-1 M2 synthetic history/CLI review/stats unchanged and separated from version 2 |
| Final documentation/diff review | 98 relative paths resolved; `git diff --check` passed |

Also replaced the CLI integration test's blocking startup read with a bounded workspace-readiness deadline. The implementation does not add AI, M3, automatic history migration or resume. The hosted 160-case evidence above belongs to the pre-hardening commits; local success alone is not a claim of hosted verification for these changes.

The first hardening [hosted run](https://github.com/tombeng027/api-contract-testing-suite/actions/runs/37926627871), source `a191a95467a07094f714acce9460ec58f7351061`, passed Ubuntu but found a Windows startup race in that new test: history was enumerated between directory allocation and the first atomic record write (213 passed, one test failure). The fix waits for `attempt.json` and all four workspace files before reading history; production corruption reporting remains unchanged. Added a deterministic provisional-directory/readiness regression. After the full 215-case local run, both readiness/full-CLI tests passed in five additional consecutive runs. This failed hosted run is retained as diagnostic evidence, not described as green.

Follow-up source `666350ca54debe22a13b44358d5e4e62b1068d01` [hosted run 37927167145](https://github.com/tombeng027/api-contract-testing-suite/actions/runs/37927167145) passed all steps: Windows 215 passed in 49.91s and Ubuntu 215 passed in 37.67s, with eight exact compatibility outcomes inspected in both logs.

## M3 revised implementation

The [tool decision](postman-parity.md) records three explicit user choices:

1. Do not adopt Newman after its initial dependency check flagged 19 packages including a critical advisory; retain the collection and assess a maintained alternative.
2. Adopt pinned project-local official Postman CLI 1.71.0 and verify no-login execution/reporting first.
3. After actual `--output` reporting required login, deliver collection execution and a manual Lab 6 guide, deferring automatic Lab 6 scoring rather than parsing terminal output into grades.

Newman dependencies and the provisional Newman runner were removed before publication. The final npm lockfile installs only the official CLI and its platform binary; `npm audit` reports zero findings in the npm tree. This does not audit vendor binary internals.

Delivered a ten-request portable Postman v2.1 collection and synthetic local environment, shared JavaScript assertions and reproducible exporter. Four named tests per request cover status, media type, selected v1 structural constraints and independent exact product/list/error values. No live v2 or schema weakening was introduced. The Python wrapper uses local files and explicit localhost URLs, disables run-event reporting/proxies/redirects, checks the pinned CLI version, bounds execution and retains raw source/stdout/stderr. It propagates failed-run exits rather than presenting them as learning outcomes.

The separate manual [Lab 6 guide](../learning/labs/06-postman-parity.md) and reference explanation walk through predictions, a successful run, a schema-valid wrong-price failure and the distinction from connection/tool failure. There is no `--lab 6` practice-runner command or automatic persistence/score; M1B/M2 history and assessments remain unchanged.

Local Windows/Python 3.14.3 / Node 24.14.0 / npm 11.9.0 verification:

| Gate | Result |
|---|---|
| Targeted Postman regressions | 16 passed in 16.80s |
| Full non-editable installed suite outside checkout | **231 passed in 74.91s**, zero failures/errors/skips |
| Composition | Existing 215 cases + 16 Postman cases |
| Documented manual wrapper | Exit 0; ten requests, forty assertions, zero failures without login |
| Controlled business failure | One request, four assertions, exactly one failure; status/media/schema pass, known-values fails for 2500 versus 2501 |
| Selected structural probes | Additive/integral-float acceptance; missing fields, wrong types/bounds, status/media mismatch rejection |
| Infrastructure | Missing binary/version mismatch visible; refused connection is a failed run, not contract success; owned timeout process stops |
| Dependency/install resources | `npm ci`, `npm audit` (zero findings), `pip check`, installed Postman collection export/resource consistency passed |
| Isolation and compatibility | All 37 server lifecycle logs stop; all eight precise compatibility outcomes pass |
| Documentation | 128 relative paths resolved in final publication check |

The manually started verification API was stopped. CI now installs Node 24 and the pinned local CLI on Windows/Ubuntu, runs the installed suite outside checkout and retains synthetic raw parity evidence. Workflow configuration/local success alone is not a hosted verification claim.

### M3 publication and hosted evidence

Source `848b982243ebf1799864ea5ef1c8371cf0ee3b0e` published normally to the approved remote. [Run 37930136864](https://github.com/tombeng027/api-contract-testing-suite/actions/runs/37930136864) passed all steps:

| Platform | Full suite |
|---|---|
| Windows / Python 3.14 | **231 passed in 66.70s** |
| Ubuntu / Python 3.14 | **231 passed in 35.93s** |

Downloaded both synthetic evidence artifacts and matched the published SHA-256 ZIP digests:

- Ubuntu artifact 11615613104: `5d6af443e82ffd181789f1fe686f0d589357bb5d43b84ec42a43b08a5117d632`.
- Windows artifact 11615464616: `b98c5099468a9608f698c2614d0d7c4788469dba27263db77b47c9e95e5b54ce`.

Each JUnit reports 231 tests, zero failures/errors/skips, and all 37 lifecycle logs end with `app_stopped`. Inspected raw Postman evidence per runner: critical collection 10 requests/40 assertions/zero failures; wrong-price demonstration 1 request/4 assertions/exactly one known-value failure; selected structural demonstration 20 requests/80 assertions/34 intentional assertion failures. The latter two are expected controlled outcomes inside passing pytest regressions, not failing CI. All eight precise Python compatibility outcomes also passed in both hosted logs.

These results verify the revised bounded M3 scope, not automatic Lab 6 scores, the complete eight-lab course, vendor-binary security, universal schema equivalence, macOS or all permitted runtimes. Artifacts expire after seven days; no personal practice history is included.

### Post-M3 parity hardening

Review reproduced cross-language nonblank disagreements: Python rejected whitespace-only U+0085 while the actual pinned Postman CLI accepted it; U+FEFF showed the reverse. New regressions failed for SKU, name and error message before the fix, also detecting U+001C-U+001F. The added list/error envelope regressions already passed against the previous implementation.

The shared JavaScript nonblank helper now uses an explicit class matching the existing Python Unicode whitespace policy. Python schemas, M2 assessment/checker versions and saved-history behavior are unchanged. The portable collection was regenerated and the non-editable package refreshed. Tests verify all 29 Python whitespace characters, selected valid boundaries, empty/mixed strings and padded text; list-item probes cover U+0085 rejection/U+FEFF acceptance. Malformed list/error envelopes, required fields, types, code/message constraints and valid additive/empty responses also have selected regressions.

Local Windows/Python 3.14.3 verification:

- Targeted Postman suite after the shared fix: **21 passed in 44.74s**. Two further list-item Unicode probes were then included in the final full-suite run.
- Full installed suite outside checkout: **236 passed in 101.03s**, zero failures/errors/skips; HTML/JUnit evidence under ignored `artifacts/post-m3-hardening-*`.
- Installed resource/export consistency checks, `pip check`, all eight precise compatibility outcomes and npm audit passed; audit reported zero findings in the npm tree.
- All 37 lifecycle logs ended with `app_stopped`; 132 relative documentation paths resolved, collection re-export was deterministic and `git diff --check` passed.
- Editor Problems reported no errors for the changed Python test and JavaScript source. The VS Code test tool still did not discover these tests; explicit repo-venv execution was used.

The reproducibility guide now describes Node 24, pinned CLI installation/audit, outside-checkout binary configuration and synthetic parity retention. This follow-up is locally verified; publication and hosted verification are not yet claimed. Automatic Lab 6 scoring remains deliberately deferred.
