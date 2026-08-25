# Supply Chain Risk Audit

This document records the supply-chain checks applied before publishing
`arm-harness` to npm, GitHub, and skills.sh.

## Scope

- npm package `arm-harness`
- GitHub repository `armcompany/arm-harness-skill`
- skills.sh skill `harness-engineering`

## Checks performed

| # | Control | Result | Evidence |
|---|---------|--------|----------|
| 1 | No secrets, credentials, or tokens committed | ✅ Pass | Grep for `api_key`, `password`, `secret`, `token`, `private_key` found only conceptual references; no real values. |
| 2 | `.npmignore` excludes build artifacts and OS files | ✅ Pass | `__pycache__/`, `*.pyc`, `.DS_Store`, `*.tgz`, `node_modules/` excluded. |
| 3 | Published tarball inspected before release | ✅ Pass | `npm publish --dry-run` shows 18 intended files, no `__pycache__`, no `.env`, no `.git`. |
| 4 | Runtime dependencies reviewed | ✅ Pass | `package.json` has no `dependencies`; only `python3` is required by `bin/harness`, declared in `engines`. |
| 5 | Scripts in `package.json` reviewed | ✅ Pass | Only `test` and `prepublishOnly` scripts; neither downloads or executes untrusted code. |
| 6 | License declared | ✅ Pass | `LICENSE` file is MIT; `license` field in `package.json` is `MIT`. |
| 7 | Publisher identity | ✅ Pass | npm logged in as `armdevelop`; GitHub remote is `git@github.com:armcompany/arm-harness-skill.git`. |
| 8 | Version bump justified | ✅ Pass | Patch bump `0.1.1 -> 0.1.2` for security hardening and supply-chain audit of `audit_harness.py`. |
| 9 | Tests run before publish | ✅ Pass | `prepublishOnly` runs `npm test`; current tests pass. |
| 10 | Symlinks and path-traversal risks mitigated | ✅ Pass | `audit_harness.py` no longer follows symlinks and bounds scan depth/file count/file size. |

## Tarball contents (v0.1.2)

```
README.md
bin/harness
package.json
skills/harness-engineering/SKILL.md
skills/harness-engineering/agents/openai.yaml
skills/harness-engineering/references/*.md
skills/harness-engineering/scripts/audit_harness.py
skills/harness-engineering/scripts/test_audit_harness.py
skills/harness-engineering/scripts/validate_project_harness.py
```

## Known supply-chain assumptions

- Consumers must have `python3` installed; the npm package does not bundle a Python runtime.
- The skill is distributed as source Markdown and Python scripts; no compiled artifacts are shipped.
- Git tags (`v0.1.2`) are used as immutable release references.

## Signed off

Audited by: Kimi Code CLI agent session
Date: 2026-08-25
