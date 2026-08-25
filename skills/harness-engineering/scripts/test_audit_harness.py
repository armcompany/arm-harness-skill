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


def test_symlinks_not_followed() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        secret = root / "secret.txt"
        secret.write_text("SHOULD_NOT_BE_READ", encoding="utf-8")
        link_dir = root / "link"
        link_dir.mkdir()
        (link_dir / "to_secret").symlink_to(secret)
        # Also create a package.json symlink pointing to the secret file.
        (root / "package.json").symlink_to(secret)
        result = AUDIT.detect(root, max_files=AUDIT.DEFAULT_MAX_FILES)
        assert "SHOULD_NOT_BE_READ" not in json.dumps(result)
        assert result["package_scripts"] == {}


def test_large_package_json_skipped() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        huge = '{"scripts": {"x": "' + "A" * 2_000_000 + '"}}'
        write(root / "package.json", huge)
        result = AUDIT.detect(root, max_file_size=1_000)
        assert result["package_scripts"] == {}


def test_max_depth_respected() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        deep = root / "a" / "b" / "c" / "d" / "e"
        deep.mkdir(parents=True)
        write(deep / "package.json", '{"scripts": {"x": "y"}}')
        # With max_depth=2 the file is below the limit and should be ignored.
        result = AUDIT.detect(root, max_depth=2)
        assert result["package_scripts"] == {}
        # With max_depth=10 it should be found.
        result = AUDIT.detect(root, max_depth=10)
        assert "a/b/c/d/e/package.json" in result["package_scripts"]


def test_invalid_root_raises() -> None:
    with tempfile.TemporaryDirectory() as directory:
        not_a_dir = Path(directory) / "file.txt"
        not_a_dir.write_text("x", encoding="utf-8")
        try:
            AUDIT.detect(not_a_dir)
        except ValueError:
            return
        raise AssertionError("detect() should raise ValueError for a non-directory root")


if __name__ == "__main__":
    test_mixed_web_python()
    test_compiled_stacks()
    test_ignored_generated_environment()
    test_symlinks_not_followed()
    test_large_package_json_skipped()
    test_max_depth_respected()
    test_invalid_root_raises()
    print("audit_harness checks passed.")
