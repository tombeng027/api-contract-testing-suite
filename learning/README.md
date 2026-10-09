# Guided API-testing learning track

**Status: Lab 0-5 reference guides, the M1B practice slice and the M2 interactive Lab 2-5 track are available. The full Lab 0-7 interactive course remains unimplemented.**

Goal: turn conceptual understanding into checks you can write, debug and explain. Work through one small task at a time; do not memorize a completed framework.

## Learning loop

**Understand -> predict -> run -> inspect -> change -> verify -> explain.**

Before a run, write down what you expect. Afterward, use the actual response/test output to explain the result. If you are unsure, state what is unknown and identify the next observation that would settle it.

## Learning sequence

| Lab | Question you should be able to answer afterward |
|---|---|
| 0. Environment and test anatomy | Which interpreter runs this test, what sets it up, and which assertion determines the result? |
| 1. HTTP exchange | What do method, path, query, status, headers and JSON each tell me? |
| 2. Meaningful assertions | How can a 200 response still contain incorrect data, and which check detects it? |
| 3. JSON Schema | Which required field, type or boundary failed, and where in the response did it fail? |
| 4. Error contracts | Is this an expected rejection, a contract defect or a test-environment failure? |
| 5. Compatibility | Which consumer expectation breaks when the response changes, and what does schema validation miss? |
| 6. Postman/Newman parity | How do I express and run the same critical expectation in another tool? |
| 7. Investigation and explanation | Can I reproduce a precise failure and explain the evidence, cause and limitation? |

Each implemented lab will provide an exact command, expected exit behavior, a small exercise, a separate reference solution and common incorrect approaches.

Start with [Lab 0: test anatomy](labs/00-test-anatomy.md), then [Lab 1: HTTP exchange](labs/01-http-exchange.md). These guides use manual prediction notes and verified reference commands. The separate [M1B practice slice](practice-slice.md) provides one prediction, one saved explanation and one editable code task with fresh workspaces and objective checks.

Continue with [Lab 2: meaningful assertions](labs/02-meaningful-assertions.md), [Lab 3: JSON Schema](labs/03-json-schema.md), [Lab 4: error contracts](labs/04-error-contracts.md) and [Lab 5: compatibility](labs/05-compatibility.md). Their reference solutions are linked separately in each guide. The [M2 interactive track](m2-track.md) provides full/focused attempts, numeric Lab 2-5 selection, saved explanations and objective code checks. Reading a Markdown solution is not a logged assistance event. Labs 6/7 remain planned.

## Repeatable attempts

Both current tracks start every attempt with unanswered prompts and fresh exercise files while preserving prior history. They save answers/revisions, hints/solution reveals, exercise evidence and reproducible variants incrementally in ignored local JSON.

You can review slice attempts and see completion counts, first/final objective scores, practice duration and topic observations. Written explanations are saved for rubric review, not automatically graded. Scores/time averages group comparable assessment versions/scopes and exclude incomplete attempts; history still shows them. This is not yet adaptive analysis of the full course.

Pause is explicit; practice duration includes thinking and checks while unpaused, not measured attention. Faster completion is not awarded points. New attempts never delete previous work, and interrupted attempts are not counted as completed.

Full design, record fields, formulas, limitations and test gates: [runner plan](runner-plan.md).

Optional Ollama/agentic coaching is a deferred improvement, not an initial dependency. It could provide explanation feedback and suggest follow-up practice; deterministic checks would still own scores and completion. See the [deferred coaching scope](runner-plan.md#deferred-extension-optional-aiagentic-coaching).

This is local practice, not encrypted storage or a sandbox. Use synthetic answers and only trusted local exercise code. Personal history will not be committed or uploaded.

## Completion means understanding

For each lab:

- [ ] Predict the behavior before execution.
- [ ] Run it yourself and identify the relevant evidence.
- [ ] Complete the change without copying the reference solution.
- [ ] Demonstrate that the assertion catches the intended wrong behavior.
- [ ] Explain why the check exists and one limitation.

Looking at a solution is allowed after an honest attempt. Then close it and repeat the exercise in your own words/code.

Lab completion is personal practice, not an employment credential or a claim of production experience. AI-assisted reference code remains something to review and verify, not an authority to trust automatically.
