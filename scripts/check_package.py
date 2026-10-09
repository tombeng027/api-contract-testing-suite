import json
from importlib.resources import files
from pathlib import Path

import catalog_api
import contracts
import practice_runner
from jsonschema import Draft202012Validator
from practice_runner.m2 import manifest


def main() -> None:
    for module in (catalog_api, contracts, practice_runner):
        if module.__file__ is None:
            raise RuntimeError(f"Package location unavailable: {module.__name__}")
        location = Path(module.__file__).resolve()
        if "site-packages" not in location.parts:
            raise RuntimeError(f"Checkout shadows installed package: {location}")
        print(f"Installed package: {location}")
    for version, names in (
        ("v1", ("product", "products", "error")), ("v2", ("product",)),
    ):
        for name in names:
            text = files("contracts").joinpath(version, f"{name}.json").read_text(encoding="utf-8")
            Draft202012Validator.check_schema(json.loads(text))
    for example in ("baseline", "additive", "removed", "renamed", "type_changed", "v2"):
        json.loads(files("contracts").joinpath("examples", f"{example}.json").read_text(encoding="utf-8"))
    manifest()
    for name in (
        "starter", "solution",
        *(f"lab{lab}-{kind}" for lab in (2, 3, 4, 5) for kind in ("starter", "solution")),
    ):
        text = files("practice_runner").joinpath("assets", f"{name}.py.txt").read_text(encoding="utf-8")
        compile(text, f"{name}.py.txt", "exec")
    print("Packaged schemas, fixtures, M1B/M2 exercises and M2 manifest verified.")


if __name__ == "__main__":
    main()
