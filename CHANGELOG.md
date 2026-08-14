# Changelog

Chinese: [`CHANGELOG.zh-CN.md`](CHANGELOG.zh-CN.md)

All notable changes are documented here. Dates use UTC.

## 0.1.0-beta.1 — 2026-08-14

### Added

- MAHO product identity and the `maho` command.
- Safe `maho init` preview/apply flow with an explicit zero-overwrite receipt.
- English and Simplified Chinese terminal output and Skill catalogs.
- Thin adapters for ten initial coding-agent targets, including Cursor.
- A release-tier contract with seven verified clients and three explicitly selected experimental adapters; `--agent all` installs verified clients only.
- Apache License 2.0 release files and a sanitized public-export manifest.
- Wheel packaging for runtime Skills, Stack Packs, schemas, and templates.

### Preserved

- Existing discovery, readiness, bootstrap, validation, context-audit, protected-snapshot, and evidence semantics.
- Historical failed, aborted, red-team, and independent-acceptance evidence in the internal development repository.

### Limitations

- Codex CLI 0.147.0-alpha.6.5 and standalone Factory Droid 0.189.0 passed native transcript-backed Skill loading, Constitution reading, and bounded Phase 17 independent acceptance; the earlier Droid 0.190.0 smoke remains preserved.
- Kimi Code and Claude Code with a Kimi backend passed separate bounded per-client acceptance.
- OpenCode 1.18.13 passed native Skill loading and Constitution reading through its built-in Kimi For Coding provider plus independent acceptance for that bounded Phase 15 scope.
- Standalone Kilo Code CLI 7.4.20 passed native Skill loading and Constitution reading through `kilo/kilo-auto/free` plus independent acceptance for that bounded Phase 16 scope after one preserved INCONCLUSIVE and one preserved FAIL.
- Cursor Agent CLI 2026.08.04-aaa8809 passed Skill discovery/loading, Constitution reading, correct INCONCLUSIVE completion semantics, and bounded Phase 18 committed-evidence acceptance with a Free account and non-Fast `composer-2.5`; private native artifacts were not shared with the validator.
- Gemini CLI, Roo Code, and GitHub Copilot are adapter-only experimental targets outside the `0.1.0-beta.1` verified support contract.
- Release identity is attributed to MAHO contributors, with project marks stewarded by Future Apparatus Laboratory and source URLs targeting `Do-fei/maho-harness`.
