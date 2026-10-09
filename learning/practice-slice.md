# M1B: repeatable practice slice

The first working runner has **three tasks**, not the full Lab 0-7 course:

1. Predict the status for a valid-but-missing catalog ID (1 point).
2. Explain why structural validation is not business correctness (ungraded).
3. Improve a price assertion and check correct/incorrect cases (1 point).

Each start creates a new unanswered attempt and exercise workspace. Old answers/work remain available for review. This is trusted local practice, not an exam, sandbox or certification.

## Start

Use [repository setup](../README.md#setup-windows-powershell) and run from the repository root:

```powershell
.\.venv\Scripts\python.exe -m practice_runner start
```

Optional reproducible seed:

```powershell
.\.venv\Scripts\python.exe -m practice_runner start --seed 42
```

The runner prints its attempt ID, exact workspace and prompts. Edit **only that attempt's** `work/answer.py` in another editor/terminal. Keep the signature `check_product(payload, expected_price)`, raising AssertionError for invalid data and returning normally for valid data.

The checker uses an expected price generated for the attempt, zero price, wrong price, string price and boolean price. Hard-coding one example or always failing does not satisfy the checks. The starting assertion is deliberately too weak.

## Interactive commands

```text
submit prediction 404
submit explanation <your explanation on one line>
submit code
hint prediction
hint explanation
hint code
solution code
pause
resume
status
complete
quit
```

Do not copy the sample prediction instead of reasoning; review the published contract first. Answers can be revised by submitting again. Code submission captures the source; rechecking identical source records a check without replacing its first submission.

Final scoring uses the latest submission or repeat check, not a stale earlier pass. A failed repeat check can lower the final score; an infrastructure failure stops the attempt without counting it as completed. Only explanations can have an ungraded outcome.

- Hints are explicit and recorded.
- Solutions require a prior submission for that task and are recorded separately.
- Paused sessions allow resume/status/quit only.
- Completion requires all selected tasks, not a perfect score.
- Written explanations remain awaiting rubric review; no keyword grading.
- `quit`, EOF and Ctrl+C preserve accepted progress as abandoned. There is no resume in this version; start again for a clean attempt.

To focus on one task, use `--scope prediction`, `--scope explanation` or `--scope code`. Default `slice` selects all three. These scopes have separate statistics. This track ID remains `api-foundations-m1b`; numeric Lab 2-5 selection belongs to the separate [M2 track](m2-track.md). The planned full `api-foundations` Lab 0-7 course remains unimplemented.

## Review and statistics

```powershell
.\.venv\Scripts\python.exe -m practice_runner history
.\.venv\Scripts\python.exe -m practice_runner review <attempt-id>
.\.venv\Scripts\python.exe -m practice_runner stats
```

Replace `<attempt-id>` with the printed ID; don't type the angle brackets. Output is readable JSON:

- History lists state, seed/scope, timing and completed scores.
- Review includes the retained prompts, answers/revisions, assistance, source snapshots/digests and checker evidence.
- Stats group track/assessment version/scope, reporting completion counts/rate, mean first/final scores, completed practice duration, unassisted counts/results and topic observations.

`null` means **N/A**, not zero. Incomplete attempts appear in counts/history but do not enter completed-score/time averages. Explanations-only completions have no objective score. Unassisted describes recorded runner usage, not outside help.

First and final objective scores use 1 point per objective task. For a slice, first wrong prediction plus correct code yields 50%; revising the prediction correctly yields final 100%. First-answer evidence remains unchanged.

Practice duration uses a monotonic clock, excludes explicit pauses and includes unpaused thinking/typing/checks. It cannot measure attention or offline editing. It is not a speed target.

## Storage and boundaries

Default storage is `.practice-data/` under the current working directory. Run from the repository root so its ignore rule applies. To select another location, put `--data-dir <path>` **before** the subcommand; manage that location's privacy/backups yourself.

Each attempt has validated `attempt.json`, `work/answer.py` and separate checker evidence directories. The JSON record is the review/statistics source of truth: it retains prompt/assessment snapshots, code sources and up to 4 KiB each of stdout/stderr per check, with truncation noted. Raw local checker output files may contain more; do not publish them blindly.

Atomic replacement preserves the prior valid JSON if saving fails. The runner acknowledges only successfully saved submissions. Terminal attempts are not rewritten through the runner; this is not tamper-proof storage. Manually edited, corrupt or unsupported records are explicitly reported; summaries warn about exclusions and exit nonzero.

Only trusted synthetic local code should be executed. There is no sandbox or protection from malicious code, disk exhaustion, spawned background processes or OS access. Exercises must not spawn processes or use network/services. Checks use isolated Python, a five-second timeout and owned-process-tree termination on timeout/interruption; output capture is not a resource quota.

## Writer lock recovery

Only one start may write at a time. If `.writer-lock.json` exists, verify its PID and whether that practice process is still active. Do not remove an active lock. A forced kill can leave a stale lock and an unfinished record.

After verifying the owner has stopped, inspect the lock's token and explicitly run:

```powershell
.\.venv\Scripts\python.exe -m practice_runner unlock --token <recorded-token>
```

This removes only the matching lock, never history or work. Mismatched/corrupt locks produce an explicit error; there is no automatic deletion or repair. Manual recovery of a corrupt lock needs careful inspection of that exact file.

## Exit behavior

| Exit | Meaning |
|---|---|
| 0 | Activities completed, or successful history/review/stats/unlock |
| 1 | Explicit quit or EOF: abandoned |
| 2 | Storage/checker/argument failure or incomplete summary due to invalid records |
| 130 | Ctrl+C: accepted work saved as abandoned if storage is available |

A completed run can have an objective score of zero. A broken checker/import/timeout does not earn credit and stops the attempt as errored when saving is possible. Hard crashes can leave partial checkpoint timing and `in_progress`; neither counts as completion.

## Review rubric for your explanation

- Does it distinguish field/type/bound validation from expected business values?
- Does it give a structurally valid but incorrect price example?
- Does it identify an independent expected-price assertion?
- Does it avoid claiming that a green schema check proves correctness?

Automatic explanation assessment, model coaching, all eight labs, spaced scheduling and cross-device history remain deferred.
