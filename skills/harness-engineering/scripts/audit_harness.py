#!/usr/bin/env python3
"""Inventory coding-agent harness artifacts in a repository.

This script is intentionally conservative: it does not judge quality, install
dependencies, or execute project code. It only scans filenames and common config
keys to produce a starting point for a harness audit.

Security notes:
- Symbolic links are never followed during the directory walk.
- File reads are size-limited to avoid memory exhaustion.
- The scan is bounded by a maximum depth and maximum file count.
- Errors are logged instead of silently swallowed.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
from pathlib import Path
from typing import Any


# --- Default safety limits (can be overridden via CLI) ---
DEFAULT_MAX_FILE_SIZE = 1_000_000  # 1 MB
DEFAULT_MAX_FILES = 100_000
DEFAULT_MAX_DEPTH = 20

# --- Logging setup ---
logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
logger = logging.getLogger("audit_harness")


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
    "site-packages",
    # Additional generated/cache directories that can be huge or sensitive.
    ".cache",
    ".tox",
    ".nox",
    ".direnv",
    ".eggs",
    ".gradle",
    "vendor",
    "Pods",
    ".yarn",
    ".pnpm-store",
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

STACK_MARKERS = {
    "JavaScript/TypeScript": {"package.json", "tsconfig.json", "jsconfig.json"},
    "Python": {"pyproject.toml", "requirements.txt", "setup.py", "setup.cfg", "Pipfile", "poetry.lock", "uv.lock"},
    "Go": {"go.mod", "go.work"},
    "Rust": {"Cargo.toml"},
    "Java/Kotlin": {"pom.xml", "build.gradle", "build.gradle.kts", "settings.gradle", "settings.gradle.kts"},
    ".NET": {"global.json", "Directory.Build.props"},
    "Ruby": {"Gemfile"},
    "PHP": {"composer.json"},
    "Swift": {"Package.swift"},
}

PACKAGE_MANAGER_MARKERS = {
    "Yarn": {"yarn.lock"},
    "pnpm": {"pnpm-lock.yaml", "pnpm-workspace.yaml"},
    "npm": {"package-lock.json"},
    "Bun": {"bun.lock", "bun.lockb"},
    "Poetry": {"poetry.lock"},
    "uv": {"uv.lock"},
    "Pipenv": {"Pipfile.lock"},
    "Gradle": {"gradlew", "gradlew.bat"},
    "Maven": {"mvnw", "mvnw.cmd", "pom.xml"},
    "Bundler": {"Gemfile.lock"},
    "Composer": {"composer.lock", "composer.json"},
    "Swift Package Manager": {"Package.swift"},
}


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def is_excluded_dir(name: str) -> bool:
    """Return True if a directory name should be skipped."""
    return name in EXCLUDE_DIRS or name.startswith(".tmp")


def iter_paths(root: Path, *, max_files: int, max_depth: int):
    """Yield files under *root* with safety bounds.

    Symbolic links are never followed, recursion is depth-limited, and the walk
    stops once max_files have been seen.
    """
    seen = 0
    for current_root, dirs, files in os.walk(root, followlinks=False):
        current = Path(current_root)

        # Depth guard: current_root is at least as long as root; compute depth.
        try:
            depth = len(current.relative_to(root).parts)
        except ValueError:
            depth = 0

        if depth >= max_depth:
            logger.warning("Reached maximum scan depth (%d) at %s", max_depth, current)
            dirs[:] = []
            continue

        dirs[:] = [d for d in dirs if not is_excluded_dir(d)]

        for filename in files:
            if seen >= max_files:
                logger.warning("Reached maximum file scan limit (%d); stopping walk.", max_files)
                return
            seen += 1
            yield current / filename


def _read_limited(path: Path, *, max_file_size: int) -> str | None:
    """Read *path* as text if it exists, is a regular file, and is within size limits.

    Symbolic links are never followed, even for files.
    """
    try:
        if path.is_symlink() or not path.is_file():
            return None
        size = path.stat().st_size
        if size > max_file_size:
            logger.warning("Skipping %s (%d bytes exceeds limit %d)", path, size, max_file_size)
            return None
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        logger.warning("Could not read %s: %s", path, exc)
        return None


def load_package_scripts(path: Path, *, max_file_size: int) -> dict[str, str]:
    text = _read_limited(path, max_file_size=max_file_size)
    if text is None:
        return {}
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        logger.warning("Could not parse JSON in %s: %s", path, exc)
        return {}
    scripts = data.get("scripts")
    if not isinstance(scripts, dict):
        return {}
    return {str(k): str(v) for k, v in scripts.items()}


def load_package_dependencies(path: Path, *, max_file_size: int) -> set[str]:
    text = _read_limited(path, max_file_size=max_file_size)
    if text is None:
        return set()
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        logger.warning("Could not parse JSON in %s: %s", path, exc)
        return set()
    dependencies: set[str] = set()
    for key in ("dependencies", "devDependencies", "peerDependencies"):
        value = data.get(key)
        if isinstance(value, dict):
            dependencies.update(str(name) for name in value)
    return dependencies


def detect(
    root: Path,
    *,
    max_file_size: int = DEFAULT_MAX_FILE_SIZE,
    max_files: int = DEFAULT_MAX_FILES,
    max_depth: int = DEFAULT_MAX_DEPTH,
) -> dict[str, Any]:
    root = root.resolve()
    if not root.is_dir():
        raise ValueError(f"scan root is not a directory: {root}")

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
        "stacks": {},
        "package_managers": {},
        "frameworks": {},
        "planning_and_memory": [],
        "persistent_harness": [],
        "agent_configs": [],
        "notes": [],
    }

    for path in iter_paths(root, max_files=max_files, max_depth=max_depth):
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
            scripts = load_package_scripts(path, max_file_size=max_file_size)
            if scripts:
                result["package_scripts"][rel_path] = scripts
            dependencies = load_package_dependencies(path, max_file_size=max_file_size)
            framework_dependencies = {
                "Expo": "expo",
                "React Native": "react-native",
                "React": "react",
                "Next.js": "next",
                "Vue": "vue",
                "Nuxt": "nuxt",
                "Svelte": "svelte",
                "Angular": "@angular/core",
                "NestJS": "@nestjs/core",
            }
            for framework, dependency in framework_dependencies.items():
                if dependency in dependencies:
                    result["frameworks"].setdefault(framework, []).append(rel_path)
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
        if rel_path.startswith(".harness/") or rel_path.startswith(".agents/harness/"):
            result["persistent_harness"].append(rel_path)
        for stack, markers in STACK_MARKERS.items():
            if name in markers or (stack == ".NET" and path.suffix in {".sln", ".csproj", ".fsproj"}):
                result["stacks"].setdefault(stack, []).append(rel_path)
        for manager, markers in PACKAGE_MANAGER_MARKERS.items():
            if name in markers:
                result["package_managers"].setdefault(manager, []).append(rel_path)

    if not result["stacks"]:
        extensions = {path.suffix for path in iter_paths(root, max_files=max_files, max_depth=max_depth)}
        if extensions & {".py"}:
            result["stacks"]["Python"] = ["Detected from .py source files"]

    for key in [
        "guides",
        "skills",
        "mcp_configs",
        "hooks",
        "ci",
        "lint_and_static_analysis",
        "tests",
        "planning_and_memory",
        "persistent_harness",
        "agent_configs",
    ]:
        result[key] = sorted(set(result[key]))

    for key in ["stacks", "package_managers", "frameworks"]:
        result[key] = {name: sorted(set(paths)) for name, paths in sorted(result[key].items())}

    if not result["guides"]:
        result["notes"].append("No root-level agent guide detected (AGENTS.md, CLAUDE.md, etc.).")
    if not result["hooks"]:
        result["notes"].append("No local hook directory or pre-commit config detected.")
    if not result["ci"]:
        result["notes"].append("No common CI workflow files detected.")
    if not result["tests"]:
        result["notes"].append("No test files detected by common directory names.")

    return result


def _md_escape(text: str) -> str:
    """Escape backticks so user-controlled text cannot break out of inline code."""
    return text.replace("`", "\\`")


def render_markdown(data: dict[str, Any]) -> str:
    lines = ["# Harness Inventory", "", f"Root: `{data['root']}`", ""]

    for title, key in [("Detected stacks", "stacks"), ("Package managers", "package_managers"), ("Frameworks", "frameworks")]:
        lines.extend([f"## {title}", ""])
        values = data.get(key, {})
        if values:
            for name, evidence in values.items():
                lines.append(f"- **{name}**: {', '.join(f'`{_md_escape(item)}`' for item in evidence)}")
        else:
            lines.append("- None detected")
        lines.append("")

    sections = [
        ("Guides", "guides"),
        ("Skills", "skills"),
        ("MCP configs", "mcp_configs"),
        ("Hooks", "hooks"),
        ("CI", "ci"),
        ("Lint and static analysis", "lint_and_static_analysis"),
        ("Tests", "tests"),
        ("Planning and memory", "planning_and_memory"),
        ("Persistent harness", "persistent_harness"),
        ("Agent configs", "agent_configs"),
    ]

    for title, key in sections:
        lines.extend([f"## {title}", ""])
        values = data.get(key, [])
        if values:
            lines.extend(f"- `{_md_escape(value)}`" for value in values[:200])
            if len(values) > 200:
                lines.append(f"- ... {len(values) - 200} more")
        else:
            lines.append("- None detected")
        lines.append("")

    lines.extend(["## Package scripts", ""])
    package_scripts = data.get("package_scripts", {})
    if package_scripts:
        for package_file, scripts in package_scripts.items():
            lines.append(f"### `{_md_escape(package_file)}`")
            for name, command in sorted(scripts.items()):
                lines.append(f"- `{_md_escape(name)}`: `{_md_escape(command)}`")
            lines.append("")
    else:
        lines.append("- None detected")
        lines.append("")

    lines.extend(["## Notes", ""])
    notes = data.get("notes", [])
    if notes:
        lines.extend(f"- {_md_escape(note)}" for note in notes)
    else:
        lines.append("- No immediate inventory gaps detected.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Inventory coding-agent harness artifacts in a repository.")
    parser.add_argument("root", nargs="?", default=".", help="Repository root to scan.")
    parser.add_argument("--format", choices=["json", "markdown"], default="json", help="Output format.")
    parser.add_argument("--max-file-size", type=int, default=DEFAULT_MAX_FILE_SIZE, help="Max file size to read in bytes.")
    parser.add_argument("--max-files", type=int, default=DEFAULT_MAX_FILES, help="Max files to scan.")
    parser.add_argument("--max-depth", type=int, default=DEFAULT_MAX_DEPTH, help="Max directory depth.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Log warnings about skipped files and limits.")
    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    try:
        data = detect(
            Path(args.root),
            max_file_size=args.max_file_size,
            max_files=args.max_files,
            max_depth=args.max_depth,
        )
    except ValueError as exc:
        logger.error("%s", exc)
        return 1

    if args.format == "markdown":
        print(render_markdown(data))
    else:
        print(json.dumps(data, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
