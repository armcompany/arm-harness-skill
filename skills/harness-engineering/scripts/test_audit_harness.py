#!/usr/bin/env python3
"""Dependency-free checks for stack and package-manager detection."""

from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path


SCRIPT = Path(__file__).with_name("audit_harness.py")
SPEC = importlib.util.spec_from_file_location("audit_harness", SCRIPT)
assert SPEC and SPEC.loader
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


def write(path: Path, content: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_mixed_web_python() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        write(
            root / "package.json",
            json.dumps({"scripts": {"test": "vitest"}, "dependencies": {"expo": "1", "react": "1", "react-native": "1"}}),
        )
        write(root / "yarn.lock")
        write(root / "pyproject.toml", "[project]\nname = 'api'\n")
        result = AUDIT.detect(root)
        assert set(result["stacks"]) == {"JavaScript/TypeScript", "Python"}
        assert set(result["frameworks"]) == {"Expo", "React", "React Native"}
        assert set(result["package_managers"]) == {"Yarn"}
        assert result["package_scripts"]["package.json"]["test"] == "vitest"


def test_compiled_stacks() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        for marker in ("go.mod", "Cargo.toml", "service.csproj", "Package.swift"):
            write(root / marker)
        result = AUDIT.detect(root)
        assert set(result["stacks"]) == {".NET", "Go", "Rust", "Swift"}
        assert set(result["package_managers"]) == {"Swift Package Manager"}


def test_ignored_generated_environment() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        write(root / "package.json", "{}")
        write(root / ".tmp-build" / "site-packages" / "setup.py")
        result = AUDIT.detect(root)
        assert set(result["stacks"]) == {"JavaScript/TypeScript"}


if __name__ == "__main__":
    test_mixed_web_python()
    test_compiled_stacks()
    test_ignored_generated_environment()
    print("audit_harness checks passed.")
