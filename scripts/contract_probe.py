import argparse
import json

from contracts.compatibility import EXAMPLES, probe


def main() -> int:
    parser = argparse.ArgumentParser(description="Check one controlled consumer fixture")
    parser.add_argument("--example", choices=EXAMPLES, required=True)
    parser.add_argument("--consumer", choices=["v1", "v2"], required=True)
    options = parser.parse_args()
    result = probe(options.example, options.consumer)
    print(json.dumps(result, indent=2))
    return 0 if result["compatible"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
