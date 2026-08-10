# Stack Discovery and Validation

Use repository evidence to adapt one Harness to any stack. Do not create a separate Harness per language and do not add tools merely to fill a validation field.

## Discovery order

1. Read root and workspace manifests, lockfiles, wrapper scripts, CI workflows, container files, and existing agent instructions.
2. Identify every language and framework that owns code in scope; monorepos may need multiple validation lanes.
3. Determine the package manager from lockfiles and declared metadata. Preserve it.
4. Prefer repository scripts and CI commands over conventional defaults.
5. Locate configurations for type checking, linting, tests, builds, migrations, and generated code.
6. Record unavailable checks honestly. Propose a new tool only when it closes a demonstrated risk.

Run `scripts/audit_harness.py <repo> --format markdown` for a conservative first inventory. Its output is evidence, not permission to execute commands.

## Stack matrix

| Evidence | Stack | Candidate checks to confirm |
| --- | --- | --- |
| `package.json`, `tsconfig.json` | JavaScript/TypeScript | declared package scripts, `tsc`, configured linter/test/build |
| `expo` dependency | Expo/React Native | project scripts, TypeScript, tests, Expo Doctor, platform/runtime validation |
| `pyproject.toml`, requirements/setup files | Python | configured Ruff/Flake8, mypy/Pyright, pytest/unittest, package build |
| `go.mod` | Go | `gofmt`, `go vet`, `go test`, project build |
| `Cargo.toml` | Rust | `cargo fmt --check`, Clippy, `cargo test`, `cargo build` |
| Gradle/Maven files | Java/Kotlin | project wrapper checks, static analysis, tests, assemble/package |
| `.sln`, `.csproj`, `.fsproj` | .NET | `dotnet format` when configured, `dotnet build`, `dotnet test` |
| `Gemfile` | Ruby | configured RuboCop, RSpec/Minitest, Bundler tasks |
| `composer.json` | PHP | configured PHPStan/Psalm, PHPUnit/Pest, Composer scripts |
| `Package.swift` | Swift | SwiftFormat/SwiftLint when configured, `swift test`, Xcode build where required |

Candidate checks are not automatically valid commands. Confirm tool presence, versions, workspace scope, required services, and CI precedent before running them.

## Monorepos and mixed stacks

- Map each workspace or service to its manifest, owner commands, and validation lane.
- Run targeted checks for the changed scope first; run aggregate checks before `DONE` when the repository provides them.
- Do not run every ecosystem command from the root blindly.
- Store validation results by meaningful lane, such as `frontend`, `api`, `mobile`, or `contracts`, rather than forcing universal keys.

## Framework and platform rules

Framework-specific constraints belong in the generated project's `AGENTS.md` or a local reference, based on exact detected versions. Examples include Expo SDK compatibility, Django migrations, Android/iOS behavior, browser support, database contracts, and generated API clients.

Verify current official documentation before version-sensitive dependency or platform changes. Never replace an established framework, package manager, or test runner by preference.

## Validation semantics

- `passed`: the exact relevant command or observable check passed on current code.
- `failed`: the check ran and produced an actionable failure.
- `blocked`: the check requires missing access, hardware, service, authority, or decision.
- `unavailable`: the repository has no such configured check.
- `not_applicable`: the check does not apply to this task or stack.

Do not convert `blocked` or `unavailable` into `passed`. Static checks do not replace runtime, integration, device, browser, security, accessibility, or visual evidence when the definition of done requires them.
