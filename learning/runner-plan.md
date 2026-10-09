# Repeatable practice runner: design and acceptance plan

Planning reviewed October 9, 2026. Requirements below describe the broader target, not a blanket claim of implemented or verified behavior.

Implementation checkpoint: the M1B three-task slice and M2 Lab 2-5 full/focused track are implemented. See [M1B commands](practice-slice.md), [M2 commands](m2-track.md) and [executed evidence](../docs/progress.md). This document still describes the broader target; the full `api-foundations` Lab 0-7 commands below remain unavailable.

## Purpose and boundaries

A local command-line runner creates fresh practice attempts, saves answers/evidence and summarizes learning history. It supports repeated retrieval and diagnosis, not certification, competitive scoring or proof of mastery.

Initial scope:

- One local learner, one writer at a time, no account or network service.
- Full-track attempts and explicitly selected lab attempts, reported separately.
- Versioned content, deterministic variations, objective checks and saved explanations.
- No UI dashboard, Supabase, AI grading, automatic scheduling or cross-device sync.
- No timed exam, background surveillance or automatic detection of outside assistance.

The API suite remains the main portfolio deliverable. Build the runner with a small complete vertical slice before authoring all labs.

## User journey and planned commands

Commands below describe the intended interface; they are not available yet:

```text
python -m practice_runner start --track api-foundations
python -m practice_runner start --track api-foundations --lab 1
python -m practice_runner history
python -m practice_runner review <attempt-id>
python -m practice_runner stats --track api-foundations
```

Starting always means a new attempt, not resuming old answers. The runner:

1. Validates the installed track, scoring definitions and local storage before starting.
2. Creates a unique attempt ID and saves its selected scope/version/seed.
3. Creates a private-to-that-attempt working directory from starter templates.
4. Presents unanswered prompts, without prior answers or reference solutions.
5. Saves every accepted submission, revision, assistance event and exercise check.
6. Presents feedback and lets the learner revise while preserving first-answer evidence.
7. Saves completion only after all required tasks have valid submissions and all required explanation prompts have nonblank answers.
8. Shows separate objective results, assistance usage and pending explanation review.

Completion means finishing the required activities, not achieving a passing score. Wrong answers may be retained as final answers. Exercise syntax/assertion failures are legitimate learning outcomes; verifier/startup/storage failures are infrastructure errors, not wrong answers.

After completion, answer records are immutable in the initial version. A new attempt is required to practice again. Review displays recorded answers, feedback, assistance and saved exercise evidence without rewriting scores.

## State and interruptions

States: `in_progress`, `completed`, `abandoned`, `errored`.

- Explicit quit, EOF or Ctrl+C saves accepted progress and marks an attempt abandoned if storage is working. An unanswered prompt at interruption is not a submission.
- An infrastructure error is surfaced explicitly and marks the attempt errored when possible.
- A forced process kill may leave `in_progress`. History reports that it is not completed and may have been interrupted; it never silently declares success.
- No resume feature in version 1. Preserved unfinished records can be reviewed; starting again creates a clean attempt.
- A storage failure stops progression. Do not claim that an answer was saved or that an attempt completed if the write failed.
- A local writer lock rejects overlapping starts with an actionable message. Stale-lock recovery is explicit and documented; never automatically kill a process or delete history.

## Fresh-state and reset safety

Fresh state resets unanswered prompts and copies only starter files into the new attempt workspace. It does not modify:

- The verified API suite or contracts.
- Original starter templates or reference solutions.
- A prior attempt's answers, work or evidence.

Attempt/question IDs are validated opaque identifiers, not filesystem paths. User-provided paths and answer strings never become shell commands or deletion targets. Workspace files are enumerated explicitly; links/junctions pointing outside the attempt workspace must be rejected for captured exercise files.

No broad reset/delete command in version 1. If cleanup is later needed, add explicit selection, preview and confirmation separately. Existing manual work must not be overwritten to obtain a base state.

## Storage format and privacy

Store under an ignored repository-local `.practice-data/` directory:

```text
.practice-data\
  attempts\
    <attempt-id>\
      attempt.json
      work\
      evidence\
```

This is local storage, not encrypted/private-by-permission storage. Users should enter synthetic examples only. History is not uploaded to GitHub or CI; no analytics or telemetry.

One schema-versioned UTF-8 JSON record per attempt is the source of truth. Human-readable review and statistics are derived from validated records, not a second mutable summary file.

Required information:

| Section | Fields/purpose |
|---|---|
| Record | `record_schema_version`, unique `attempt_id`, status |
| Content identity | Track ID, content version, assessment version, selected lab/question IDs, manifest digest |
| Reproduction | Variant seed, generator version and actual generated prompts/fixtures or their retained snapshots |
| Time | UTC start/update/end timestamps; accumulated practice duration and timing completeness |
| Submission history | Question ID, submission ID, sequence, UTC timestamp, answer, evaluation and feedback |
| Assistance | Hint/solution events, target question and sequence before/after submissions |
| Exercises | Enumerated relative source snapshots, digest, checker version, exit outcome, checks and output/evidence references |
| Completion | Final submission IDs, earned/possible objective points, first-answer result and explanation-review status |

Keep previous submissions; do not overwrite a wrong first answer with the later correct answer. Validate types, required fields, IDs, point ranges and evidence references when writing/reading. Output limits for checker stdout/stderr must be explicit; note truncation while keeping result identity and useful failure evidence.

Persistence uses a temporary file beside the destination and atomic replacement after validation. Save before acknowledging a submission. If an interruption occurs during replacement, readers should see a valid previous or new record, not half-written JSON. This is not a promise against hardware failure or every filesystem failure.

Corrupt/unsupported records produce a visible diagnostic identifying the file. History/statistics may report valid records only if they clearly disclose excluded records and an incomplete-summary warning; never silently treat corrupt records as zero-score or successful attempts. Review of that record fails explicitly. No automatic repair or deletion.

## Evaluation and scoring

Each assessment version defines task IDs, accepted structured answers, checker expectations and points before the attempt starts.

An exercise's first submitted code snapshot is its first submission, even when it fails a learner-level check. Rerunning the same snapshot is another recorded check, not a replacement first answer. Evaluation evidence and checker outputs are persisted before credit is reported.

| Task | Evaluation |
|---|---|
| Choice/structured prediction | Deterministic accepted value with documented normalization; invalid answer format prompts correction without consuming a submission |
| Coding exercise | Trusted checker evaluates learner source on specified correct and incorrect behavior; baseline success alone is insufficient |
| Written explanation | Recorded with rubric/reference; not automatically graded and excluded from objective points |

All submissions remain available. Display:

- **First-submission score:** objective points earned on the first valid submission for every scored task.
- **Final objective score:** points from each task's final selected submission at completion.
- **First-answer accuracy:** correct structured predictions / answered structured predictions, with numerator and denominator.
- **Assistance:** hints, solution reveals and whether assistance occurred before a task's first submission.
- **Explanations:** answered, awaiting review; self-review is separate from objective scoring.

Missing tasks prevent completion; they do not reduce a completed attempt's denominator. A completed track with no scored tasks has score `N/A`, not 0 or 100.

Initial scoring uses explicit all-or-nothing points per objective task; there is no undocumented partial credit or pass threshold. Exercise credit requires all specified correct/incorrect behavior checks. An infrastructure error prevents finalization and is reported separately rather than becoming a zero or a pass.

Solution-assisted attempts remain visible, but an unassisted statistics view excludes attempts with recorded hints/solution reveals. Outside help cannot be detected; these labels describe recorded runner usage only. Avoid claims of exam integrity.

Checker outcomes distinguish `passed`, `learner_failure` and `infrastructure_error`. An unrelated import failure, unavailable server, timeout or checker crash must not earn credit for detecting a deliberately broken API.

Use bounded subprocesses and owned-process cleanup for exercises. Execute only local learner code the user trusts. Subprocess execution is not a sandbox; never accept remote/untrusted submissions in this design.

## Timing

Call the measure **practice duration**, not pure active attention or coding speed.

- Use UTC timestamps for review and a monotonic clock for elapsed durations.
- Provide explicit pause/resume within an attempt; paused time is excluded.
- While paused, the runner accepts only resume, status or quit; submissions, hints, solution reveals and exercise checks require resume. This does not prevent offline thinking/editing, so duration remains self-managed practice evidence, not an exam-integrity measure.
- Reading, typing, deliberate thinking and learner-triggered checks count while unpaused. Idle attention cannot be inferred.
- Initialize timing after startup preparation; terminal review after completion does not count.
- Checkpoint accumulated duration on submissions, assistance, checks and pause/quit/completion.
- For a hard crash, only checkpointed duration is known; label timing partial. Do not inflate it using elapsed time until the next launch.
- Clock injection lets tests check timing without sleep-based assertions.

No duration points, speed ranking or arbitrary SLA. Faster is not inherently better learning.

## Statistics and comparability

Group by track ID, assessment version and scope (full track versus the exact selected lab set). Record content version/variant seed and show variant details; never merge changed scoring into the same average.

For each group show:

- Attempts started, completed, abandoned, errored and still in progress.
- Completion rate: completed / all started attempts in the valid group.
- Mean final objective score: sum of per-attempt percentages / number of completed scored attempts.
- Mean first-submission score using the same completed scored group.
- Structured first-answer accuracy reported separately from weighted objective points.
- Mean completed practice duration: sum of complete-timing completed durations / eligible completed attempts.
- Separate unassisted results and sample counts.
- Per-topic first-answer accuracy, assistance and repeated failed checks.

Display sample counts and exclusions. Incomplete attempts appear in history/counts, not completion-score or duration averages. For incomplete attempts, per-topic observations may appear separately, never mixed silently into completed-attempt metrics. Empty denominators yield `N/A`.

Implemented slice acceptance fixture: two comparable completions score 50% and 100% (two equal-weight objective tasks), with complete durations of 120s and 180s. A third attempt is abandoned. Expected: 3 started, 2 completed, 66.67% completion, 75% mean final score, 150s mean completed duration. The abandoned record contributes to neither average. Calculation retains precision; any display rounding occurs afterward.

## Repeated learning without rote memorization

- Keep Lab 0 orientation fixed and begin with a stable learning sequence.
- Vary synthetic IDs, values, boundary positions and missing/wrong-type fields deterministically.
- Retain the actual variant so past reviews work after content changes.
- Use equivalent difficulty/check rubrics within one assessment version; seeds alone do not prove difficulty equivalence.
- Mix prediction, code changes and explanations. Ask why a response is wrong even when its status/schema passes.
- Solutions appear only through an explicit reveal action after at least one valid submission, with assistance recorded. Local source remains inspectable; this is a learning aid, not access control.
- Review identifies suggested topics to repeat; spaced scheduling and adaptive question selection are deferred.

## Verification matrix

| Scenario | Required result |
|---|---|
| Start twice | Two unique attempts, unanswered prompts and clean workspaces; first history/work unchanged |
| Submit/revise | Both answers retained; first score unchanged; final score follows final selected answer |
| Hint/solution reveal | Persisted sequence and correct assistance label; normal start reveals neither |
| Repeat seed | Same prompts/fixtures within version; retained evidence enables later review |
| Invalid input | Clear validation feedback; no accidental submission or point award |
| Complete with wrong answers | Completed with accurate low score, not falsely labeled mastery |
| Missing required explanation/task | Cannot complete; response remains available to finish or quit |
| Ctrl+C/quit | Accepted work preserved, abandoned status, no leaked owned server/process |
| Forced interruption/write failure | No false completion; prior JSON valid; partial timing/error shown |
| Corrupt record/version | Explicit warning/failure; no silent deletion or misleading aggregate |
| Pause/clock change | Paused time excluded; UTC wall-clock changes do not change monotonic duration |
| Actions while paused/EOF | Learning actions require resume; EOF preserves accepted work as abandoned without submitting unanswered text |
| Statistics example/zero history | Exact expected counts/means; empty denominators `N/A` |
| Different scopes/assessments | Separate aggregates and visible sample counts |
| Wrong exercise/unrelated failure | Intended mistake detected; infrastructure failures never earn detection points |
| Parallel start/path escape | Second writer/path escape rejected; prior work and source stay intact |
| Default suite/CI | Learning verification uses synthetic temporary histories; no personal data or unfinished exercises discovered |

## Delivery order

1. API foundation and documented contract; first reference checks.
2. Runner vertical slice: one prediction, one saved explanation, one exercise, fresh attempts, review and stats.
3. Verify reset/persistence/scoring/timing/interruptions against the matrix before expanding labs.
4. Add remaining contracts, variants, labs and Postman/Newman parity incrementally.
5. Clean-install and CI verification for suite and runner; document exact outcomes and known limits.

Before release, separately verify materials work and ask the learner to rehearse. Passing runner tests prove record/scoring behavior, not retained knowledge.

## Deferred extension: optional AI/agentic coaching

Discussed October 9, 2026; not part of initial implementation. Repeated execution, history and statistics need deterministic automation, not an agent.

After the core runner is verified and actual practice reveals a need, consider an optional local Ollama coach:

- User-requested explanation feedback and progressive hints.
- Follow-up questions tied to submitted reasoning.
- Suggested existing labs based on recorded topic mistakes.
- A bounded adaptive loop: review selected evidence, propose practice, obtain learner approval and reassess after submission.

Begin with a single advisory feedback call before adding an agent loop. Suggestions do not automatically start exercises, modify source files, execute generated commands or rewrite history.

Objective grading, completion, timing and statistics remain under deterministic code. AI feedback is separately labeled and records model identity, generation settings, prompt/rubric version and selected evidence references; this does not guarantee reproducible output.

Only explicitly selected synthetic content is sent to a configured local service. Remote model services require a separate consent/privacy decision. Model unavailability, timeout or invalid output is reported explicitly; the normal runner remains usable without AI.

Before implementing, assess hardware/model feasibility, coaching quality against reviewed examples, solution leakage, misleading feedback and bounded execution. An agent is justified only if adaptive decisions improve practice beyond a simpler rule-based recommendation.
