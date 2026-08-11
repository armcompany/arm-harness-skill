#!/usr/bin/env python3
"""Dependency-free checks for React Native detection, violations, and validation."""

from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path


def load(name: str):
    script = Path(__file__).with_name(name)
    spec = importlib.util.spec_from_file_location(name.removesuffix(".py"), script)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


AUDIT = load("audit_rn_project.py")
VALIDATE = load("validate_rn_architecture.py")


def write(path: Path, content: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def package_json(**overrides) -> str:
    payload = {
        "scripts": {"typecheck": "tsc --noEmit", "lint": "eslint .", "test": "jest"},
        "dependencies": {
            "expo": "54.0.0",
            "react-native": "0.81.0",
            "expo-router": "6.0.0",
            "@tanstack/react-query": "5.0.0",
            "zustand": "5.0.0",
            "zod": "3.23.0",
        },
        "devDependencies": {"jest-expo": "54.0.0", "@testing-library/react-native": "13.0.0"},
    }
    payload.update(overrides)
    return json.dumps(payload)


def test_expo_cng_detection() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        write(root / "package.json", package_json())
        write(root / "pnpm-lock.yaml")
        write(root / "app.config.ts", "export default {};")
        write(root / "src" / "features" / "orders" / "ui" / "OrderScreen.tsx", "export const A = 1;\n")

        result = AUDIT.detect(root)
        assert result["workflow"] == "expo_cng"
        assert result["topology"] == "monolith_feature_first"
        assert result["package_manager"] == "pnpm"
        assert result["app_config"] == "app.config.ts"
        assert result["libraries"]["server_state"] == ["TanStack Query"]
        assert result["libraries"]["client_state"] == ["Zustand"]
        assert result["libraries"]["navigation"] == ["expo-router"]


def test_bare_and_prebuild_workflows() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        write(root / "package.json", json.dumps({"dependencies": {"react-native": "0.81.0"}}))
        write(root / "ios" / "Podfile")
        assert AUDIT.detect(root)["workflow"] == "bare"

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        write(root / "package.json", package_json())
        write(root / "android" / "build.gradle")
        assert AUDIT.detect(root)["workflow"] == "expo_prebuild_committed"


def test_violation_scanning() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        write(root / "package.json", package_json())
        write(
            root / "src" / "features" / "orders" / "ui" / "OrderScreen.tsx",
            "import axios from 'axios';\n"
            "import { helper } from '../../../features/catalog/model/helper';\n"
            "const q = useQuery({ queryKey: ['orders'] });\n",
        )
        write(
            root / "src" / "features" / "orders" / "api" / "getOrder.ts",
            "export async function getOrder(id: string): Promise<any> { return null; }\n",
        )
        write(
            root / "src" / "features" / "orders" / "__tests__" / "ignored.test.tsx",
            "import axios from 'axios';\nconst q = useQuery({ queryKey: ['x'] });\n",
        )

        rules = {item["rule"] for item in AUDIT.detect(root)["violations"]}
        assert "ui_imports_transport" in rules
        assert "ui_calls_query_directly" in rules
        assert "inline_query_key" in rules
        assert "cross_feature_deep_import" in rules
        assert "deep_relative_import" in rules
        assert "any_at_boundary" in rules

        locations = [item["location"] for item in AUDIT.detect(root)["violations"]]
        assert not any("__tests__" in location for location in locations), "tests must be exempt"


def test_validation_fails_on_required_rules() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        write(root / "package.json", package_json())
        write(root / "tsconfig.json", json.dumps({"compilerOptions": {"strict": True}}))
        write(root / "src" / "features" / "orders" / "ui" / "Bad.tsx", "import axios from 'axios';\n")

        checks = VALIDATE.evaluate(AUDIT.detect(root))
        by_name = {item["check"]: item for item in checks}
        assert by_name["typescript_strict"]["status"] == "pass"
        assert by_name["ui_imports_transport"]["status"] == "fail"
        assert any(item["status"] == "fail" for item in checks)


def test_validation_passes_on_clean_project() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        write(
            root / "package.json",
            package_json(
                scripts={
                    "typecheck": "tsc --noEmit",
                    "lint": "eslint .",
                    "test": "jest",
                    "e2e:ios": "maestro test e2e/flows",
                    "verify": "pnpm typecheck && pnpm lint && pnpm test",
                },
                devDependencies={
                    "jest-expo": "54.0.0",
                    "@testing-library/react-native": "13.0.0",
                    "detox": "20.0.0",
                    "@sentry/react-native": "6.0.0",
                },
            ),
        )
        write(
            root / "tsconfig.json",
            json.dumps({"compilerOptions": {"strict": True, "noUncheckedIndexedAccess": True}}),
        )
        write(
            root / "src" / "features" / "orders" / "ui" / "OrderScreen.tsx",
            "export function OrderScreen() { return null; }\n",
        )
        write(
            root / "src" / "features" / "orders" / "api" / "useOrderQuery.ts",
            "export function useOrderQuery(id: string) { return id; }\n",
        )

        result = AUDIT.detect(root)
        checks = VALIDATE.evaluate(result)
        assert not [item for item in checks if item["status"] == "fail"], checks


def test_markdown_render_is_stable() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        write(root / "package.json", package_json())
        result = AUDIT.detect(root)
        markdown = AUDIT.render_markdown(result)
        assert "# React Native Architecture Audit" in markdown
        assert "## Violations" in markdown
        assert "## Missing sensors" in markdown
        assert "# React Native Architecture Validation" in VALIDATE.render_markdown(
            result, VALIDATE.evaluate(result)
        )


if __name__ == "__main__":
    test_expo_cng_detection()
    test_bare_and_prebuild_workflows()
    test_violation_scanning()
    test_validation_fails_on_required_rules()
    test_validation_passes_on_clean_project()
    test_markdown_render_is_stable()
    print("audit_rn_project checks passed.")
