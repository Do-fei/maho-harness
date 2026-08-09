# Quick start

Chinese: [`../zh-CN/QUICKSTART.md`](../zh-CN/QUICKSTART.md)

## 1. Preview

Run from any directory after installing MAHO:

```bash
maho --locale en init /path/to/project --agent codex
```

The preview is read-only. Confirm the target repository, selected agents, files that would be created, preserved paths, and `Overwritten 0`.

## 2. Apply without overwriting

```bash
maho --locale en init /path/to/project --agent codex --apply --yes
```

Without `--yes`, an interactive terminal asks for confirmation. A non-interactive terminal rejects `--apply` unless `--yes` is present.

## 3. Review proposed checks

```bash
maho discover /path/to/project
maho readiness /path/to/project
```

Discovery proposes commands but does not declare them accepted. Review `.harness/project.json`, move approved entries from `proposed_checks` into `checks`, and resolve the generated Project Constitution.

## 4. Validate

```bash
maho validate /path/to/project
maho context-audit /path/to/project
```

Validation never executes shell code from configuration. It runs direct argument arrays, records bounded evidence, and fails if configured protected paths change.

## 5. Add clients

Repeat `--agent`, or select all seven verified clients:

```bash
maho --locale en init . --agent claude-code --agent cursor --apply --yes
maho --locale en init . --agent all --apply --yes
```

`all` excludes Gemini CLI, Roo Code, and GitHub Copilot because they are experimental in `0.1.0-beta.1`. Name an experimental adapter explicitly only when you accept the displayed warning:

```bash
maho --locale en init . --agent gemini-cli
```

Existing Skill directories are preserved rather than merged or overwritten.
