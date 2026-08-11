#!/usr/bin/env python3
"""Inventory a React Native / Expo project and flag architecture-contract violations.

Conservative by design: it reads files, it never installs dependencies, runs
project code, or edits anything. Output is evidence for an architecture audit,
not permission to execute commands.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any

EXCLUDE_DIRS = {
    ".git",
    "node_modules",
    "ios",
    "android",
    ".expo",
    ".expo-shared",
    "dist",
    "build",
    "coverage",
    ".next",
    "__pycache__",
    ".venv",
    "venv",
    "generated",
}

SOURCE_SUFFIXES = {".ts", ".tsx", ".js", ".jsx"}

TEST_PATH_MARKERS = ("__tests__", ".test.", ".spec.", "/test/", "/e2e/")

LOCKFILES = {
    "pnpm-lock.yaml": "pnpm",
    "yarn.lock": "Yarn",
    "package-lock.json": "npm",
    "bun.lockb": "Bun",
    "bun.lock": "Bun",
}

# dependency -> (category, label)
DEPENDENCY_MAP: dict[str, tuple[str, str]] = {
    "expo": ("platform", "Expo"),
    "react-native": ("platform", "React Native"),
    "expo-router": ("navigation", "expo-router"),
    "@react-navigation/native": ("navigation", "react-navigation"),
    "@tanstack/react-query": ("server_state", "TanStack Query"),
    "@apollo/client": ("server_state", "Apollo Client"),
    "urql": ("server_state", "urql"),
    "swr": ("server_state", "SWR"),
    "zustand": ("client_state", "Zustand"),
    "jotai": ("client_state", "Jotai"),
    "redux": ("client_state", "Redux"),
    "@reduxjs/toolkit": ("client_state", "Redux Toolkit"),
    "mobx": ("client_state", "MobX"),
    "recoil": ("client_state", "Recoil"),
    "graphql": ("transport", "GraphQL"),
    "graphql-request": ("transport", "GraphQL"),
    "axios": ("transport", "REST (axios)"),
    "ky": ("transport", "REST (ky)"),
    "zod": ("validation", "Zod"),
    "valibot": ("validation", "Valibot"),
    "yup": ("validation", "Yup"),
    "nativewind": ("styling", "NativeWind"),
    "tamagui": ("styling", "Tamagui"),
    "react-native-unistyles": ("styling", "Unistyles"),
    "styled-components": ("styling", "styled-components"),
    "react-native-mmkv": ("storage", "MMKV"),
    "expo-secure-store": ("storage", "SecureStore"),
    "@react-native-async-storage/async-storage": ("storage", "AsyncStorage"),
    "expo-sqlite": ("storage", "SQLite"),
    "drizzle-orm": ("storage", "Drizzle"),
    "jest": ("testing", "Jest"),
    "jest-expo": ("testing", "jest-expo"),
    "vitest": ("testing", "Vitest"),
    "@testing-library/react-native": ("testing", "Testing Library"),
    "msw": ("testing", "MSW"),
    "detox": ("e2e", "Detox"),
    "maestro": ("e2e", "Maestro"),
    "@sentry/react-native": ("observability", "Sentry"),
    "expo-updates": ("release", "expo-updates"),
    "@graphql-codegen/cli": ("codegen", "graphql-codegen"),
    "openapi-typescript": ("codegen", "openapi-typescript"),
}

TRANSPORT_IMPORT = re.compile(
    r"""from\s+['"]([^'"]*(?:axios|ky|graphql-request|@apollo/client|urql|"""
    r"""@tanstack/react-query|core/api|/httpClient|/graphqlClient)[^'"]*)['"]"""
)
STORE_CREATE = re.compile(r"\bcreate<|\bcreate\(\s*\(?\s*set\b|from\s+['\"]zustand['\"]")
QUERY_CALL = re.compile(r"\buse(?:Query|InfiniteQuery|Mutation|SuspenseQuery)\s*\(")
INLINE_QUERY_KEY = re.compile(r"queryKey:\s*\[\s*['\"]")
DEEP_RELATIVE = re.compile(r"from\s+['\"](\.\./\.\./\.\.[^'\"]*)['\"]")
FEATURE_IMPORT = re.compile(r"from\s+['\"][^'\"]*features/([A-Za-z0-9_-]+)/([^'\"]+)['\"]")
ANY_TYPE = re.compile(r":\s*any\b|<any>|as\s+any\b")
USE_EFFECT = re.compile(r"\buseEffect\s*\(")
ASYNC_STORAGE_SECRET = re.compile(r"AsyncStorage[\s\S]{0,80}?(token|secret|password|credential)", re.IGNORECASE)
CONSOLE_LOG = re.compile(r"\bconsole\.log\s*\(")

UI_DIR_MARKERS = ("/ui/", "/components/", "/screens/")


def is_excluded(path: Path) -> bool:
    return any(part in EXCLUDE_DIRS for part in path.parts)


def is_test_path(rel: str) -> bool:
    return any(marker in rel for marker in TEST_PATH_MARKERS)


def read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def iter_source_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for current, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS and not d.startswith(".")]
        for name in filenames:
            path = Path(current) / name
            if path.suffix in SOURCE_SUFFIXES:
                files.append(path)
    return files


def detect_workflow(root: Path, dependencies: dict[str, str]) -> str:
    has_expo = "expo" in dependencies
    has_rn = "react-native" in dependencies
    native_dirs = (root / "ios").is_dir() or (root / "android").is_dir()

    if not has_rn and not has_expo:
        return "not_react_native"
    if has_expo and not native_dirs:
        return "expo_cng"
    if has_expo and native_dirs:
        return "expo_prebuild_committed"
    return "bare"


def detect_topology(root: Path) -> str:
    workspace_markers = [
        (root / "pnpm-workspace.yaml").is_file(),
        bool(read_json(root / "package.json").get("workspaces")),
    ]
    packages = root / "packages"
    if any(workspace_markers) and packages.is_dir():
        return "modular_workspaces"
    for candidate in (root / "src" / "features", root / "features", root / "app" / "features"):
        if candidate.is_dir():
            return "monolith_feature_first"
    if (root / "src" / "components").is_dir() or (root / "components").is_dir():
        return "flat_by_kind"
    return "unknown"


def detect_typescript(root: Path) -> dict[str, Any]:
    config = read_json(root / "tsconfig.json")
    options = config.get("compilerOptions", {}) if isinstance(config, dict) else {}
    return {
        "present": bool(config),
        "strict": bool(options.get("strict")),
        "noUncheckedIndexedAccess": bool(options.get("noUncheckedIndexedAccess")),
        "paths": sorted((options.get("paths") or {}).keys()),
    }


def classify_dependencies(dependencies: dict[str, str]) -> dict[str, list[str]]:
    found: dict[str, list[str]] = {}
    for name, version in dependencies.items():
        entry = DEPENDENCY_MAP.get(name)
        if not entry:
            continue
        category, label = entry
        value = f"{label} ({version})" if category == "platform" else label
        found.setdefault(category, [])
        if value not in found[category]:
            found[category].append(value)
    return {key: sorted(value) for key, value in found.items()}


def scan_violations(root: Path, files: list[Path]) -> list[dict[str, Any]]:
    violations: list[dict[str, Any]] = []

    def add(severity: str, rule: str, path: Path, line: int, detail: str) -> None:
        violations.append(
            {
                "severity": severity,
                "rule": rule,
                "location": f"{path.relative_to(root).as_posix()}:{line}",
                "detail": detail,
            }
        )

    for path in files:
        rel = "/" + path.relative_to(root).as_posix()
        if is_test_path(rel):
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue

        in_ui = any(marker in rel for marker in UI_DIR_MARKERS)
        in_api = "/api/" in rel or "/core/" in rel
        owner_feature = None
        feature_match = re.search(r"features/([A-Za-z0-9_-]+)/", rel)
        if feature_match:
            owner_feature = feature_match.group(1)

        for number, line in enumerate(lines, start=1):
            if in_ui:
                transport = TRANSPORT_IMPORT.search(line)
                if transport:
                    add("high", "ui_imports_transport", path, number, transport.group(1))
                if QUERY_CALL.search(line):
                    add("high", "ui_calls_query_directly", path, number, line.strip()[:100])
                if STORE_CREATE.search(line):
                    add("medium", "ui_defines_store", path, number, line.strip()[:100])
                if USE_EFFECT.search(line):
                    add("low", "useeffect_in_ui", path, number, "justify the external subscription or remove")

            if INLINE_QUERY_KEY.search(line):
                add("medium", "inline_query_key", path, number, "use the feature query key factory")

            deep = DEEP_RELATIVE.search(line)
            if deep:
                add("medium", "deep_relative_import", path, number, deep.group(1))

            cross = FEATURE_IMPORT.search(line)
            if cross and owner_feature and cross.group(1) != owner_feature and "/" in cross.group(2):
                add(
                    "high",
                    "cross_feature_deep_import",
                    path,
                    number,
                    f"{owner_feature} -> features/{cross.group(1)}/{cross.group(2)}",
                )

            if in_api and ANY_TYPE.search(line):
                add("high", "any_at_boundary", path, number, line.strip()[:100])

            if ASYNC_STORAGE_SECRET.search(line):
                add("high", "secret_in_async_storage", path, number, "use SecureStore/Keychain")

            if CONSOLE_LOG.search(line):
                add("low", "console_log", path, number, "route through the logger")

    order = {"high": 0, "medium": 1, "low": 2}
    violations.sort(key=lambda item: (order[item["severity"]], item["rule"], item["location"]))
    return violations


def missing_sensors(root: Path, scripts: dict[str, str], classified: dict[str, list[str]]) -> list[str]:
    joined = " ".join(scripts.values())
    gaps: list[str] = []
    if not any("tsc" in value for value in scripts.values()):
        gaps.append("no typecheck script (`tsc --noEmit`)")
    if not any(key in scripts for key in ("lint", "lint:fix")):
        gaps.append("no lint script")
    if "test" not in scripts:
        gaps.append("no test script")
    if not classified.get("testing"):
        gaps.append("no test runner or Testing Library dependency")
    if not classified.get("e2e") and not (root / "e2e").is_dir() and ".maestro" not in joined:
        gaps.append("no E2E setup (Maestro or Detox)")
    if not classified.get("validation"):
        gaps.append("no runtime schema validation library at the network boundary")
    if not classified.get("observability"):
        gaps.append("no crash reporter")
    if classified.get("codegen") and "codegen" not in joined:
        gaps.append("codegen dependency present but no codegen script")
    if not any(marker in joined for marker in ("verify", "&&")):
        gaps.append("no aggregate `verify` script agents and humans can run before done")
    return gaps


def detect(root: Path) -> dict[str, Any]:
    package_json = read_json(root / "package.json")
    dependencies: dict[str, str] = {}
    for field in ("dependencies", "devDependencies"):
        section = package_json.get(field)
        if isinstance(section, dict):
            dependencies.update({key: str(value) for key, value in section.items()})

    scripts = {k: str(v) for k, v in (package_json.get("scripts") or {}).items()}
    classified = classify_dependencies(dependencies)
    files = [path for path in iter_source_files(root) if not is_excluded(path.relative_to(root))]

    app_config = None
    for name in ("app.config.ts", "app.config.js", "app.json"):
        if (root / name).is_file():
            app_config = name
            break

    return {
        "root": str(root),
        "workflow": detect_workflow(root, dependencies),
        "app_config": app_config,
        "topology": detect_topology(root),
        "package_manager": next(
            (label for name, label in LOCKFILES.items() if (root / name).is_file()), "unknown"
        ),
        "versions": {
            "expo": dependencies.get("expo"),
            "react-native": dependencies.get("react-native"),
            "react": dependencies.get("react"),
        },
        "libraries": classified,
        "typescript": detect_typescript(root),
        "scripts": scripts,
        "source_file_count": len(files),
        "violations": scan_violations(root, files),
        "missing_sensors": missing_sensors(root, scripts, classified),
    }


def render_markdown(result: dict[str, Any]) -> str:
    lines = ["# React Native Architecture Audit", "", "## Detected stack", "", "| Item | Value |", "| --- | --- |"]
    versions = result["versions"]
    typescript = result["typescript"]
    rows = [
        ("Workflow", result["workflow"]),
        ("App config", result["app_config"] or "none"),
        ("Topology", result["topology"]),
        ("Package manager", result["package_manager"]),
        ("Expo", versions["expo"] or "-"),
        ("React Native", versions["react-native"] or "-"),
        ("TypeScript strict", "yes" if typescript["strict"] else "no"),
        ("noUncheckedIndexedAccess", "yes" if typescript["noUncheckedIndexedAccess"] else "no"),
        ("Source files scanned", str(result["source_file_count"])),
    ]
    for category in (
        "navigation",
        "server_state",
        "client_state",
        "transport",
        "validation",
        "styling",
        "storage",
        "testing",
        "e2e",
        "observability",
        "codegen",
    ):
        values = result["libraries"].get(category)
        rows.append((category.replace("_", " ").title(), ", ".join(values) if values else "-"))
    lines += [f"| {name} | {value} |" for name, value in rows]

    lines += ["", "## Violations", ""]
    if result["violations"]:
        lines += ["| Severity | Rule | Location | Detail |", "| --- | --- | --- | --- |"]
        lines += [
            f"| {item['severity']} | {item['rule']} | {item['location']} | {item['detail']} |"
            for item in result["violations"]
        ]
    else:
        lines.append("No contract violations detected by static scan.")

    lines += ["", "## Missing sensors", ""]
    lines += [f"- {gap}" for gap in result["missing_sensors"]] or ["- none"]
    lines += ["", "Static evidence only. Confirm findings against the running app before acting."]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".", help="project root")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.is_dir():
        parser.error(f"not a directory: {root}")

    result = detect(root)
    print(json.dumps(result, indent=2) if args.format == "json" else render_markdown(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
