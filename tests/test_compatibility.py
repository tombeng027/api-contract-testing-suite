import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest
from jsonschema.exceptions import ValidationError

from contracts.compatibility import consumer, payload, probe
from contracts.verification import CASES, verify_result


@pytest.mark.regression
@pytest.mark.parametrize("_name,example,version,keyword", CASES, ids=[case[0] for case in CASES])
def test_selected_consumer_change(
    _name: str, example: str, version: str, keyword: str | None
) -> None:
    result = probe(example, version)
    verify_result(result, 0 if result["compatible"] else 1, example, version, keyword)


@pytest.mark.regression
@pytest.mark.parametrize("field", ["amount_cents", "currency"])
def test_v2_required_price_fields(field: str) -> None:
    baseline = payload("v2")
    assert isinstance(baseline, dict)
    price = baseline["price"]
    assert isinstance(price, dict)
    del price[field]
    errors = list(consumer("v2").iter_errors(baseline))
    assert len(errors) == 1
    assert errors[0].validator == "required"
    assert list(errors[0].absolute_path) == ["price"]
    assert field not in errors[0].instance


@pytest.mark.regression
@pytest.mark.parametrize("value,keyword", [
    (-1, "minimum"), ("2500", "type"), (True, "type"),
])
def test_v2_amount_boundaries(value: object, keyword: str) -> None:
    baseline = payload("v2")
    assert isinstance(baseline, dict)
    price = baseline["price"]
    assert isinstance(price, dict)
    price["amount_cents"] = value
    errors = list(consumer("v2").iter_errors(baseline))
    assert len(errors) == 1
    assert errors[0].validator == keyword
    assert list(errors[0].absolute_path) == ["price", "amount_cents"]


@pytest.mark.regression
def test_v2_zero_and_currency_policy() -> None:
    baseline = payload("v2")
    assert isinstance(baseline, dict)
    price = baseline["price"]
    assert isinstance(price, dict)
    price["amount_cents"] = 0
    consumer("v2").validate(baseline)
    price["currency"] = "EUR"
    errors = list(consumer("v2").iter_errors(baseline))
    assert len(errors) == 1
    assert errors[0].validator == "const"
    assert list(errors[0].absolute_path) == ["price", "currency"]


@pytest.mark.regression
def test_v1_v2_contracts_do_not_silently_accept_renames() -> None:
    with pytest.raises(ValidationError, match="'price' is a required property"):
        consumer("v2").validate(payload("baseline"))
    with pytest.raises(ValidationError, match="'price_cents' is a required property"):
        consumer("v1").validate(payload("v2"))


@pytest.mark.regression
@pytest.mark.parametrize("modification", [
    "exit", "identity", "keyword", "instance_path", "schema_path", "missing_field", "extra_failure",
])
def test_verifier_rejects_unrelated_failures(modification: str) -> None:
    result = copy.deepcopy(probe("removed", "v1"))
    exit_code = 1
    if modification == "exit":
        exit_code = 2
    elif modification == "identity":
        result["example"] = "baseline"
    elif modification == "extra_failure":
        result["failures"].append(copy.deepcopy(result["failures"][0]))
    else:
        failure = result["failures"][0]
        if modification == "keyword":
            failure["keyword"] = "type"
        elif modification == "instance_path":
            failure["instance_path"] = ["unrelated"]
        elif modification == "schema_path":
            failure["schema_path"] = ["properties", "name"]
        else:
            failure["missing_fields"] = ["name"]
    with pytest.raises(ValueError):
        verify_result(result, exit_code, "removed", "v1", "required")


@pytest.mark.regression
def test_verifier_rejects_false_positive_success() -> None:
    result = probe("baseline", "v1")
    with pytest.raises(ValueError, match="exit"):
        verify_result(result, 1, "baseline", "v1", None)
    result["failures"] = probe("removed", "v1")["failures"]
    with pytest.raises(ValueError, match="contains failures"):
        verify_result(result, 0, "baseline", "v1", None)


@pytest.mark.regression
def test_explicit_compatibility_verifier(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, str(root / "scripts" / "verify_compatibility.py"),
         "--output", str(tmp_path)],
        cwd=tmp_path, capture_output=True, text=True, timeout=45,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert not result.stderr
    summaries = list(tmp_path.glob("*/summary.json"))
    assert len(summaries) == 1
    evidence = json.loads(summaries[0].read_text(encoding="utf-8"))
    assert [case["case"] for case in evidence] == [case[0] for case in CASES]
    assert [case["exit_code"] for case in evidence] == [0, 0, 1, 1, 1, 1, 0, 0]


@pytest.mark.regression
@pytest.mark.parametrize("argument", ["../elsewhere", "v3"])
def test_unknown_contract_inputs_are_explicit(argument: str) -> None:
    with pytest.raises(ValueError):
        consumer(argument)
    with pytest.raises(ValueError):
        payload(argument)
