#!/usr/bin/env python3
"""Validate a React Native project against the architecture contracts of this skill.

Runs the static audit, then turns it into pass/warn/fail checks. Intended as a
repository gate: `python validate_rn_architecture.py . --strict` exits non-zero
when a required contract is broken.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any

AUDIT_PATH = Path(__file__).with_name("audit_rn_project.py")
_spec = importlib.util.spec_from_file_location("audit_rn_project", AUDIT_PATH)
assert _spec and _spec.loader
audit_rn_project = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(audit_rn_project)

REQUIRED_RULES = {"ui_imports_transport", "cross_feature_deep_import", "any_at_boundary", "secret_in_async_storage"}


def check(name: str, status: str, detail: str) -> dict[str, str]:
    return {"check": name, "status": status, "detail": detail}


def evaluate(result: dict[str, Any]) -> list[dict[str, str]]:
    checks: list[dict[str, str]] = []
    libraries = result["libraries"]
    typescript = result["typescript"]

    if result["workflow"] == "not_react_native":
        return [check("project_type", "fail", "no react-native or expo dependency found")]

    checks.append(check("workflow", "pass", result["workflow"]))
    checks.append(
        check(
            "topology",
            "warn" if result["topology"] in {"flat_by_kind", "unknown"} else "pass",
            result["topology"],
        )
    )

    checks.append(
        check("typescript_strict", "pass" if typescript["strict"] else "fail", "strict must be enabled")
    )
    checks.append(
        check(
            "no_unchecked_indexed_access",
            "pass" if typescript["noUncheckedIndexedAccess"] else "warn",
            "recommended for mobile index-access crashes",
        )
    )

    server_state = libraries.get("server_state", [])
    client_state = libraries.get("client_state", [])
    checks.append(
        check(
            "server_state_owner",
            "pass" if server_state else "fail",
            ", ".join(server_state) or "no server-state cache (TanStack Query, Apollo, urql)",
        )
    )
    checks.append(
        check(
            "single_server_cache",
            "warn" if len(server_state) > 1 else "pass",
            ", ".join(server_state) or "-",
        )
    )
    checks.append(
        check(
            "single_client_store",
            "warn" if len(client_state) > 1 else "pass",
            ", ".join(client_state) or "none (local state only)",
        )
    )
    checks.append(
        check(
            "runtime_validation",
            "pass" if libraries.get("validation") else "fail",
            ", ".join(libraries.get("validation", [])) or "no schema validation at boundaries",
        )
    )
    checks.append(
        check(
            "unit_tests",
            "pass" if libraries.get("testing") else "fail",
            ", ".join(libraries.get("testing", [])) or "no test runner",
        )
    )
    checks.append(
        check(
            "e2e_tests",
            "pass" if libraries.get("e2e") else "warn",
            ", ".join(libraries.get("e2e", [])) or "no Maestro or Detox setup",
        )
    )
    checks.append(
        check(
            "observability",
            "pass" if libraries.get("observability") else "warn",
            ", ".join(libraries.get("observability", [])) or "no crash reporter",
        )
    )

    by_rule: dict[str, int] = {}
    for violation in result["violations"]:
        by_rule[violation["rule"]] = by_rule.get(violation["rule"], 0) + 1

    for rule in sorted(REQUIRED_RULES):
        count = by_rule.get(rule, 0)
        checks.append(
            check(rule, "fail" if count else "pass", f"{count} occurrence(s)" if count else "clean")
        )

    for rule, count in sorted(by_rule.items()):
        if rule not in REQUIRED_RULES:
            checks.append(check(rule, "warn", f"{count} occurrence(s)"))

    for gap in result["missing_sensors"]:
        checks.append(check("missing_sensor", "warn", gap))

    return checks


def render_markdown(result: dict[str, Any], checks: list[dict[str, str]]) -> str:
    counts = {status: sum(1 for item in checks if item["status"] == status) for status in ("pass", "warn", "fail")}
    lines = [
        "# React Native Architecture Validation",
        "",
        f"Root: `{result['root']}`",
        f"Result: {counts['pass']} pass, {counts['warn']} warn, {counts['fail']} fail",
        "",
        "| Status | Check | Detail |",
        "| --- | --- | --- |",
    ]
    order = {"fail": 0, "warn": 1, "pass": 2}
    for item in sorted(checks, key=lambda i: (order[i["status"]], i["check"])):
        lines.append(f"| {item['status']} | {item['check']} | {item['detail']} |")

    failing = [item for item in result["violations"] if item["rule"] in REQUIRED_RULES]
    if failing:
        lines += ["", "## Blocking violations", ""]
        lines += [f"- `{item['location']}` {item['rule']}: {item['detail']}" for item in failing[:50]]
        if len(failing) > 50:
            lines.append(f"- ... and {len(failing) - 50} more")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".", help="project root")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--strict", action="store_true", help="exit 1 when any check fails")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.is_dir():
        parser.error(f"not a directory: {root}")

    result = audit_rn_project.detect(root)
    checks = evaluate(result)

    if args.format == "json":
        print(json.dumps({"checks": checks, "audit": result}, indent=2))
    else:
        print(render_markdown(result, checks))

    failed = any(item["status"] == "fail" for item in checks)
    return 1 if (failed and args.strict) else 0


if __name__ == "__main__":
    raise SystemExit(main())
