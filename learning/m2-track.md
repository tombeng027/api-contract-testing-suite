# M2: repeatable contract practice

This installed local track covers Labs 2-5. It does not implement the complete Lab 0-7 course, AI grading or an exam.

Read the [reference guides](README.md) alongside practice. Run from the repository root after [installation](../README.md#setup-windows-powershell); reinstall after changing runner source/resources.

## Start fresh

Full M2 attempt:

```powershell
.\.venv\Scripts\python.exe -m practice_runner start --track api-contracts-m2 --seed 42
```

One lab:

```powershell
.\.venv\Scripts\python.exe -m practice_runner start --track api-contracts-m2 --lab 3 --seed 42
```

Omit `--seed` for a newly selected random seed. A fixed seed reproduces generated values/predictions, not previous answers. Lab numbers are 2, 3, 4 and 5 only. Full and focused attempts use identical variants for a given seed, but their statistics are separate.

Each lab has a prediction, an ungraded explanation and a code task. The full track has 12 required tasks and 8 objective points; a single lab has 3 tasks and 2 objective points. Each objective task is all-or-nothing. Completing activities is not the same as getting them right.

The runner prints exact task IDs, prompts and workspace paths. Edit only the new attempt's `work/lab2.py`, `lab3.py`, `lab4.py` or `lab5.py`; it copies fresh starter files and never overwrites prior work.

## Commands

For Lab 3, for example:

```text
submit 3.prediction <one of the displayed choices>
submit 3.explanation <your explanation on one line>
submit 3.code
hint 3.code
solution 3.code
pause
resume
status
complete
quit
```

Replace the placeholders rather than typing angle brackets. Use the task IDs and choices actually displayed. Prediction variants intentionally require different answers, not memorization of a sample.

Hints are recorded. A solution/rubric reveal requires a prior submission for that task; it is recorded but does not edit your file or submit an answer for you. Reading a Markdown reference is outside runner assistance tracking.

Code submissions capture source/digest and checker evidence. Rechecking identical source records a `check`; changing it creates a new submission. First scoring uses the first submission, while final scoring uses the latest submission/check. A failed recheck cannot inherit an earlier passing score.

Explanations are saved with a lab-specific review rubric. They earn no automatic points and still need human review.

## Exercise contracts and evidence

| Lab | Required function | Behavior |
|---|---|---|
| 2: meaningful assertions | `check_response(status, payload, expected)` | Assert status 200, exact Python integer price and independent expected value |
| 3: JSON Schema | `check_response(status, payload, expected)` | Assert status 200 and full v1 schema; no independent price equality required |
| 4: error contracts | `check_response(status, payload, expected)` | Assert error schema plus exact expected status/code/message; `expected` is a dict |
| 5: compatibility | `compatible(payload, version)` | Return an exact bool for selected v1/v2 schema; unknown versions raise ValueError |

Labs 2-4 return normally for accepted examples and raise **AssertionError** for rejected examples. Do not merely return `False`. Lab 5 returns a bool instead.

Five aggregate evidence groups (`valid`, `boundary`, `missing`, `wrong-type`, `wrong-value`) must all pass. Groups can include multiple probes; they are not five score units. The checker tests valid and invalid behavior:

- Lab 2: generated correct/zero prices, status, wrong value, string and boolean prices.
- Lab 3: integral float/zero acceptance, all required fields, price type/fraction/negative bounds, identity bounds, nonblank strings, availability type and status.
- Lab 4: two expected error families, additive metadata, missing/wrong-type fields, wrong status/code/message.
- Lab 5: additive and schema-valid semantic changes, explicit v2 zero acceptance, old-consumer removal/rename/v2 failures, wrong price types, malformed nested price/currency and unknown version rejection.

JSON Schema treats integral numbers mathematically; Lab 2 deliberately tests exact Python integer values. The tasks assess different expectations, not one interchangeable policy.

These are selected synthetic probes, not exhaustive verification or proof of mastery. A syntax/assertion failure is a learner failure; unexpected runtime/import/protocol/timeout errors stop the attempt as errored rather than awarding credit.

## Review and statistics

```powershell
.\.venv\Scripts\python.exe -m practice_runner history
.\.venv\Scripts\python.exe -m practice_runner review <attempt-id>
.\.venv\Scripts\python.exe -m practice_runner stats --track api-contracts-m2
```

History/review support both tracks. `stats` defaults to the original M1B track; explicitly select M2. Groups separate track, assessment version and full/focused scope. Completed-only averages show first/final scores, unassisted samples and practice time; task-level observations show first/final correct counts. Incomplete/error attempts remain visible but do not distort those averages. `null` means N/A.

M2 records use schema 2 with a retained generated lab/manifest snapshot and immutable identity/content. Existing schema-1 M1B attempts remain readable without rewriting. Unsupported/corrupt records produce visible errors and a nonzero summary exit, even if they belong to the other track.

## Shared safety and timing

The [M1B storage, timing, lock and exit policies](practice-slice.md#storage-and-boundaries) still apply: local ignored JSON, one writer, explicit pause, no resume/delete or automatic recovery. Practice time is not measured attention or a speed reward.

Use only trusted local synthetic code. Execution is not sandboxed; do not spawn background processes or call network/services. Personal answers/work/evidence are not committed or uploaded by CI. Custom `--data-dir` locations need their own privacy/backup controls.

Reference-solution verification is a software test, not a personal learning achievement.
