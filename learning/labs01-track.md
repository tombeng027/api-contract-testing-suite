# Labs 0-1: repeatable foundation practice

This installed local track covers Labs 0 and 1. It does not implement the complete Lab 0-7 course, AI grading or an exam; Labs 2-5 belong to the separate [M2 track](m2-track.md) and Labs 6-7 remain manual.

Read the [reference guides](README.md) alongside practice. Run from the repository root after [installation](../README.md#setup-windows-powershell); reinstall after changing runner source/resources.

## Start fresh

Both labs:

```powershell
.\.venv\Scripts\python.exe -m practice_runner start --track api-foundations-labs01 --seed 42
```

One lab:

```powershell
.\.venv\Scripts\python.exe -m practice_runner start --track api-foundations-labs01 --lab 0 --seed 42
```

Omit `--seed` for a newly selected random seed. A fixed seed reproduces generated values/predictions, not previous answers. Lab numbers are 0 and 1 only. Full and focused attempts use identical variants for a given seed, but their statistics are separate.

Each lab has a prediction, an ungraded explanation and a code task. The full track has 6 required tasks and 4 objective points; a single lab has 3 tasks and 2 objective points. Each objective task is all-or-nothing. Completing activities is not the same as getting them right.

The runner prints exact task IDs, prompts and workspace paths. Edit only the new attempt's `work/lab0.py` or `lab1.py`; it copies fresh starter files and never overwrites prior work.

## Commands

For Lab 0, for example:

```text
submit 0.prediction <one of the displayed choices>
submit 0.explanation <your explanation on one line>
submit 0.code
hint 0.code
solution 0.code
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
| 0: test anatomy | `failing_assertion(status, payload, expected)` | Return the first failing ordered check: `"status"`, then `"schema"`, then `"price"`, otherwise `None` |
| 1: HTTP exchange | `expected_status(product_id, filters, known_ids)` | Return the exact documented status: 422 for invalid input, 404 for a valid missing ID, otherwise 200 |

Lab 0 returns the name of the first failing assertion rather than raising, so the order itself is the observable behavior: a wrong status is reported before a structural defect, and a structural defect before a wrong business value. `"schema"` here means all five v1 fields are present on an object; full keyword-level JSON Schema validation belongs to Lab 3. The price check requires an exact Python integer; bool is an int subclass and must not pass.

Lab 1 classifies requests against the documented contract. Product requests (`product_id` is not `None`) return 422 for non-integer, boolean or nonpositive IDs, 200 for IDs in `known_ids` and otherwise 404. List requests (`product_id` is `None`) accept at most one `available` filter with the exact lower-case value `true` or `false`; duplicate filters, unknown parameters and any other value return 422. Returned statuses must be exact ints, not bools.

Five aggregate evidence groups (`valid`, `boundary`, `missing`, `wrong-type`, `wrong-value`) must all pass. Groups can include multiple probes; they are not five score units. Selected probes include additive-field tolerance, a zero price, boolean/string/float IDs and prices, capitalized and padded filter values, duplicate and unknown parameters, and out-of-order assertion checks.

These are selected synthetic probes, not exhaustive verification or proof of mastery. A syntax/assertion failure is a learner failure; unexpected runtime/import/protocol/timeout errors stop the attempt as errored rather than awarding credit.

## Review and statistics

```powershell
.\.venv\Scripts\python.exe -m practice_runner history
.\.venv\Scripts\python.exe -m practice_runner review <attempt-id>
.\.venv\Scripts\python.exe -m practice_runner stats --track api-foundations-labs01
```

History/review support all tracks. `stats` defaults to the original M1B track; explicitly select this track. Groups separate track, assessment version and full/focused scope. Completed-only averages show first/final scores, unassisted samples and practice time; task-level observations show first/final correct counts. Incomplete/error attempts remain visible but do not distort those averages. `null` means N/A.

This track uses assessment/checker version **1** and schema-2 records with a retained generated lab/manifest snapshot, exactly like the M2 record format. Existing M1B and M2 histories remain readable and separate; no prior record is rewritten or regraded.

## Shared safety and timing

The [M1B storage, timing, lock and exit policies](practice-slice.md#storage-and-boundaries) still apply: local ignored JSON, one writer, explicit pause, no resume/delete or automatic recovery. Practice time is not measured attention or a speed reward.

Use only trusted local synthetic code. Execution is not sandboxed; do not spawn background processes or call network/services. Personal answers/work/evidence are not committed or uploaded by CI. Custom `--data-dir` locations need their own privacy/backup controls.

Reference-solution verification is a software test, not a personal learning achievement.
