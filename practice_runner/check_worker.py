"""Trusted checker protocol; learner code is trusted local code, not sandboxed."""

import importlib.util
import json
import sys
from pathlib import Path


def main() -> None:
    source, price_text, result_path = sys.argv[1:4]
    lab = int(sys.argv[4]) if len(sys.argv) == 5 else None
    price = int(price_text)
    checks: list[dict[str, object]] = []
    outcome = "passed"
    feedback = (
        "Accepted valid prices and rejected incorrect prices/types."
        if lab is None else f"All selected Lab {lab} behavior checks passed."
    )
    try:
        spec = importlib.util.spec_from_file_location("learner_submission", source)
        if spec is None or spec.loader is None:
            raise RuntimeError("Unable to create learner module")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        name = "check_product" if lab is None else ("compatible" if lab == 5 else "check_response")
        function = getattr(module, name, None)
        if not callable(function):
            raise AttributeError(f"Define the required callable: {name}")
        cases = [
            ("correct", {"price_cents": price}, price, False),
            ("zero", {"price_cents": 0}, 0, False),
            ("wrong-price", {"price_cents": price + 1}, price, True),
            ("string-price", {"price_cents": str(price)}, price, True),
            ("boolean-price", {"price_cents": True}, 1, True),
        ]
        if lab is not None:
            from practice_runner.m2_checks import check_lab
            checks = check_lab(function, lab, price)
        else:
            for name, payload, expected, should_reject in cases:
                rejected = False
                try:
                    function(payload, expected)
                except AssertionError:
                    rejected = True
                passed = rejected == should_reject
                checks.append({"name": name, "passed": passed})
        if not all(check["passed"] for check in checks):
            outcome = "learner_failure"
            feedback = "Some valid/invalid behavior checks failed; inspect checks."
    except (SyntaxError, AssertionError, AttributeError, NameError, TypeError, KeyError) as error:
        outcome = "learner_failure"
        feedback = f"{type(error).__name__}: {error}"
    except Exception as error:
        # Report distinctly; unexpected checker/import/runtime failures earn no points.
        outcome = "infrastructure_error"
        feedback = f"{type(error).__name__}: {error}"
    Path(result_path).write_text(json.dumps({
        "checker_version": "1", "lab": lab,
        "outcome": outcome, "feedback": feedback, "checks": checks,
    }), encoding="utf-8")


if __name__ == "__main__":
    main()
