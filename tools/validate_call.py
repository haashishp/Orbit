"""Validate an ORBIT tool call against tool_schemas.json.

Usage:
    python validate_call.py '{"name": "get_robot_status", "arguments": {"robot_id": "ORBIT_001"}}' --role user

Used later to auto-check every generated dataset example.
Requires: pip install jsonschema
"""
import argparse
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

SCHEMA_PATH = Path(__file__).with_name("tool_schemas.json")


def load_registry():
    data = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    return data, {t["name"]: t for t in data["tools"]}


def validate_call(call: dict, role: str = "user") -> list[str]:
    data, tools = load_registry()
    errors = []
    name = call.get("name")
    if name not in tools:
        return [f"unknown tool: {name!r}"]
    tool = tools[name]
    allowed = data["permissions_by_role"].get(role)
    if allowed is None:
        return [f"unknown role: {role!r}"]
    if tool["permission"] not in allowed and name not in data["always_allowed"]:
        errors.append(f"role {role!r} lacks {tool['permission']!r} permission for {name}")
    validator = Draft202012Validator(tool["parameters"])
    for err in validator.iter_errors(call.get("arguments", {})):
        path = ".".join(str(p) for p in err.path) or "(root)"
        errors.append(f"{path}: {err.message}")
    return errors


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("call", help="tool call JSON")
    ap.add_argument("--role", default="user")
    args = ap.parse_args()
    errors = validate_call(json.loads(args.call), args.role)
    if errors:
        print("INVALID")
        for e in errors:
            print(" -", e)
        sys.exit(1)
    print("VALID")


if __name__ == "__main__":
    main()
