"""Compare saved aggregate JSON with replay output."""

import argparse
import json
import math
from pathlib import Path


def first_difference(expected: object, actual: object, path: str = "$", *, field: str = "") -> str | None:
    if type(expected) is not type(actual):
        return f"{path}: different JSON types"
    if isinstance(expected, dict):
        if expected.keys() != actual.keys():
            return f"{path}: different object keys"
        for key, value in expected.items():
            problem = first_difference(value, actual[key], f"{path}.{key}", field=key)
            if problem:
                return problem
        return None
    if isinstance(expected, list):
        if len(expected) != len(actual):
            return f"{path}: different array lengths"
        for index, (left, right) in enumerate(zip(expected, actual)):
            problem = first_difference(left, right, f"{path}[{index}]")
            if problem:
                return problem
        return None
    if isinstance(expected, float):
        matches = math.isclose(expected, actual, rel_tol=1e-11, abs_tol=1e-12)
    elif isinstance(expected, str) and field == "source_file":
        matches = expected.replace("\\", "/") == actual.replace("\\", "/")
    else:
        matches = expected == actual
    return None if matches else f"{path}: different values"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("expected", type=Path)
    parser.add_argument("actual", type=Path)
    args = parser.parse_args()
    expected = json.loads(args.expected.read_text(encoding="utf-8"))
    actual = json.loads(args.actual.read_text(encoding="utf-8"))
    if problem := first_difference(expected, actual):
        parser.exit(1, problem + "\n")
    print(f"Matched {args.expected.name}")


if __name__ == "__main__":
    main()
