# Reproducibility and publication

Use [README setup](../README.md#setup-windows-powershell) with this repository's independent environment.

## Packaging and dependency policy

- Non-editable install uses `pyproject.toml` plus `constraints.txt`.
- Consumer schemas, compatibility fixtures and learning resources must be included as package data; tests run outside the checkout to expose accidental source shadowing.
- `scripts/check_package.py` checks installed package locations and local resources.
- Its M2 check validates the packaged course manifest and compiles all four starter/solution pairs; full behavior is verified by synthetic runner regressions, not by compilation alone.
- Constraints are an environment version snapshot, not a hash-verified universal lockfile.
- Python metadata permits 3.12-3.14; executed versions/platforms are recorded in [progress](progress.md). Do not assume the metadata range is a tested matrix.
- Reinstall after app/schema/learning source changes; tests importing an old installed package would otherwise be misleading.

## Hosted workflow

[Workflow](../.github/workflows/qa.yml) uses Windows/Ubuntu with Python 3.14:

1. Constrained non-editable installation, dependency check and installed-package snapshot.
2. Resource check and default suite outside checkout in importlib mode.
3. Exact controlled compatibility verifier.
4. Seven-day retention of synthetic reports, lifecycle logs and compatibility evidence.

Ordinary failures fail the job. Expected compatibility failures are accepted only by the precise verifier. Personal attempt history/work and raw local learner evidence are not uploaded.

No Postman/Newman step until M3 is implemented and verified. No AI services, credentials or externally hosted API are required at test runtime.

Actual run IDs/results and evidence inspections must be recorded separately in progress; a workflow file or a configured remote is not a green-CI claim.

## Local evidence and privacy

Reports live in ignored `artifacts/`; `.practice-data/` is ignored local learning history. Reference verification uses synthetic temporary records. Manual `--data-dir` paths outside the repository are not covered by this repository's ignore rule.

Do not share personal answers, arbitrary exercise output or real employer data. Local history is not encrypted. Backup history yourself before moving environments; unsupported formats are reported rather than silently transformed.
