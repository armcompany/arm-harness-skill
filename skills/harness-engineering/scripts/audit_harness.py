#!/usr/bin/env python3
"""Inventory coding-agent harness artifacts in a repository.

This script is intentionally conservative: it does not judge quality, install
dependencies, or execute project code. It only scans filenames and common config
keys to produce a starting point for a harness audit.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any


EXCLUDE_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    ".next",
    "dist",
    "build",
    "target",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
}

GUIDE_NAMES = {
    "AGENTS.md",
    "CLAUDE.md",
    "GEMINI.md",
    ".cursorrules",
    ".windsurfrules",
    "copilot-instructions.md",
}

MCP_NAMES = {
    ".mcp.json",
    "mcp.json",
    "mcp.config.json",
    "mcp.jsonc",
}

LINT_CONFIG_NAMES = {
    ".eslintrc",
    ".eslintrc.js",
    ".eslintrc.cjs",
    ".eslintrc.json",
    "eslint.config.js",
    "eslint.config.mjs",
    "biome.json",
    "ruff.toml",
    ".ruff.toml",
    ".flake8",
    "pylintrc",
    ".pylintrc",
    "pyrightconfig.json",
    "mypy.ini",
    "tsconfig.json",
    "semgrep.yml",
    ".semgrep.yml",
}

TEST_DIR_NAMES = {"test", "tests", "__tests__", "spec", "specs", "e2e"}


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def iter_paths(root: Path):
    for current_root, dirs, files in os.walk(root):
        current = Path(current_root)
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for filename in files:
            yield current / filename


def load_package_scripts(path: Path) -> dict[str, str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    scripts = data.get("scripts")
    if not isinstance(scripts, dict):
        return {}
    return {str(k): str(v) for k, v in scripts.items()}


def detect(root: Path) -> dict[str, Any]:
    root = root.resolve()
    result: dict[str, Any] = {
        "root": str(root),
        "guides": [],
        "skills": [],
        "mcp_configs": [],
        "hooks": [],
        "ci": [],
        "lint_and_static_analysis": [],
        "tests": [],
        "package_scripts": {},
        "planning_and_memory": [],
        "agent_configs": [],
        "notes": [],
    }

    for path in iter_paths(root):
        name = path.name
        rel_path = rel(path, root)
        parent_parts = set(path.relative_to(root).parts[:-1])

        if name in GUIDE_NAMES:
            result["guides"].append(rel_path)
        if name == "SKILL.md":
            result["skills"].append(rel_path)
        if name in MCP_NAMES:
            result["mcp_configs"].append(rel_path)
        if name in LINT_CONFIG_NAMES:
            result["lint_and_static_analysis"].append(rel_path)
        if name == "package.json":
            scripts = load_package_scripts(path)
            if scripts:
                result["package_scripts"][rel_path] = scripts
        if any(part in TEST_DIR_NAMES for part in parent_parts):
            result["tests"].append(rel_path)
        if (
            rel_path.startswith(".github/workflows/")
            or rel_path == ".gitlab-ci.yml"
            or rel_path.startswith(".circleci/")
            or rel_path.startswith(".buildkite/")
        ):
            result["ci"].append(rel_path)
        if rel_path.startswith(".husky/") or rel_path.startswith(".git/hooks/") or rel_path == ".pre-commit-config.yaml":
            result["hooks"].append(rel_path)
        if any(part in {".codex", ".claude", ".cursor", ".continue", ".github"} for part in parent_parts):
            result["agent_configs"].append(rel_path)
        if name.lower() in {"plan.md", "handoff.md", "memory.md", "progress.md", ".agent_memory.md"}:
            result["planning_and_memory"].append(rel_path)

    for key in [
        "guides",
        "skills",
        "mcp_configs",
        "hooks",
        "ci",
        "lint_and_static_analysis",
        "tests",
        "planning_and_memory",
        "agent_configs",
    ]:
        result[key] = sorted(set(result[key]))

    if not result["guides"]:
        result["notes"].append("No root-level agent guide detected (AGENTS.md, CLAUDE.md, etc.).")
    if not result["hooks"]:
        result["notes"].append("No local hook directory or pre-commit config detected.")
    if not result["ci"]:
        result["notes"].append("No common CI workflow files detected.")
    if not result["tests"]:
        result["notes"].append("No test files detected by common directory names.")

    return result


def render_markdown(data: dict[str, Any]) -> str:
    lines = ["# Harness Inventory", "", f"Root: `{data['root']}`", ""]

    sections = [
        ("Guides", "guides"),
        ("Skills", "skills"),
        ("MCP configs", "mcp_configs"),
        ("Hooks", "hooks"),
        ("CI", "ci"),
        ("Lint and static analysis", "lint_and_static_analysis"),
        ("Tests", "tests"),
        ("Planning and memory", "planning_and_memory"),
        ("Agent configs", "agent_configs"),
    ]

    for title, key in sections:
        lines.extend([f"## {title}", ""])
        values = data.get(key, [])
        if values:
            lines.extend(f"- `{value}`" for value in values[:200])
            if len(values) > 200:
                lines.append(f"- ... {len(values) - 200} more")
        else:
            lines.append("- None detected")
        lines.append("")

    lines.extend(["## Package scripts", ""])
    package_scripts = data.get("package_scripts", {})
    if package_scripts:
        for package_file, scripts in package_scripts.items():
            lines.append(f"### `{package_file}`")
            for name, command in sorted(scripts.items()):
                lines.append(f"- `{name}`: `{command}`")
            lines.append("")
    else:
        lines.append("- None detected")
        lines.append("")

    lines.extend(["## Notes", ""])
    notes = data.get("notes", [])
    if notes:
        lines.extend(f"- {note}" for note in notes)
    else:
        lines.append("- No immediate inventory gaps detected.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Inventory coding-agent harness artifacts in a repository.")
    parser.add_argument("root", nargs="?", default=".", help="Repository root to scan.")
    parser.add_argument("--format", choices=["json", "markdown"], default="json", help="Output format.")
    args = parser.parse_args()

    data = detect(Path(args.root))
    if args.format == "markdown":
        print(render_markdown(data))
    else:
        print(json.dumps(data, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
