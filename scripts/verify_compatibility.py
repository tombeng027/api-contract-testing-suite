import argparse
import json
import subprocess
import sys
import uuid
from pathlib import Path

from contracts.verification import CASES, verify_result


def main() -> int:
    parser = argparse.ArgumentParser(description="Prove exact compatible/incompatible consumer examples")
    parser.add_argument("--output", type=Path)
    options = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = options.output or root / "artifacts" / "compatibility"
    output.mkdir(parents=True, exist_ok=True)
    # Preserve earlier evidence and avoid stale successful summaries after a failed rerun.
    run_directory = output / uuid.uuid4().hex
    run_directory.mkdir(exist_ok=False)
    summary: list[dict[str, object]] = []
    for name, example, version, keyword in CASES:
        result = subprocess.run(
            [sys.executable, str(root / "scripts" / "contract_probe.py"),
             "--example", example, "--consumer", version],
            cwd=run_directory, capture_output=True, text=True, timeout=15,
        )
        (run_directory / f"{name}.stdout.json").write_text(result.stdout, encoding="utf-8")
        (run_directory / f"{name}.stderr.txt").write_text(result.stderr, encoding="utf-8")
        if result.stderr:
            raise RuntimeError(f"{name}: unexpected stderr; inspect {run_directory}")
        parsed = json.loads(result.stdout)
        verify_result(parsed, result.returncode, example, version, keyword)
        summary.append({"case": name, "exit_code": result.returncode, "result": parsed})
        print(f"PASS {name}: expected consumer result and exact failure identity verified")
    (run_directory / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Evidence: {run_directory}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
