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
- Postman assertions, independent expectations and portable exports are also packaged resources. After editing their source, run `npm run export:postman` and reinstall Python; the suite checks export/source agreement.

## Postman tooling

Install Node 24 and run `npm ci`, then `npm audit`, from the checkout. This installs the pinned project-local official Postman CLI 1.71.0, not Newman. Audit results cover the npm package tree, not the bundled vendor binary's internals.

For installed-package tests outside the checkout, set `CATALOG_POSTMAN_CLI` to the absolute pinned executable path first:

```powershell
$env:CATALOG_POSTMAN_CLI = (Resolve-Path .\node_modules\@postman\pm-bin-windows-x64\bin\postman.exe).Path
```

On Ubuntu x64 the binary is `node_modules/@postman/pm-bin-linux-x64/bin/postman`. Local collection execution requires no login; machine-readable `--output` reporting is login-gated and is not used. See [the tooling and manual Lab 6 boundaries](postman-parity.md).

## Hosted workflow

[Workflow](../.github/workflows/qa.yml) uses Windows/Ubuntu with Python 3.14 and Node 24:

1. Pinned project-local CLI installation via `npm ci`, current npm audit gate and absolute `CATALOG_POSTMAN_CLI` configuration.
2. Constrained non-editable Python installation, dependency check and installed-package snapshot.
3. Resource check and default suite, including synthetic Postman parity regressions, outside checkout in importlib mode.
4. Exact controlled compatibility verifier.
5. Seven-day retention of synthetic reports, lifecycle logs, compatibility and Postman parity evidence.

Ordinary failures fail the job. Expected compatibility failures are accepted only by the precise verifier. Personal attempt history/work and raw local learner evidence are not uploaded.

No AI services, credentials or externally hosted target API are required at test runtime. Tests use synthetic localhost targets; disabled run-event reporting is not a certification of zero vendor telemetry. A future npm advisory can fail the audit gate without a source regression.

Actual run IDs/results and evidence inspections must be recorded separately in progress; a workflow file or a configured remote is not a green-CI claim.

## Local evidence and privacy

Reports live in ignored `artifacts/`; `.practice-data/` is ignored local learning history. Reference verification uses synthetic temporary records. Manual `--data-dir` paths outside the repository are not covered by this repository's ignore rule.

Do not share personal answers, arbitrary exercise output or real employer data. Local history is not encrypted. Backup history yourself before moving environments; unsupported formats are reported rather than silently transformed.
