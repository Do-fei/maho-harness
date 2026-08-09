# Uninstall

Chinese: [`../zh-CN/UNINSTALL.md`](../zh-CN/UNINSTALL.md)

## Remove the CLI

Use the installer that installed MAHO:

```bash
pipx uninstall maho-harness
# or
uv tool uninstall maho-harness
# or
python3 -m pip uninstall maho-harness
```

## Remove project files

MAHO intentionally does not provide a command that recursively deletes project files. Review Git status and remove only paths you have verified belong to MAHO.

Typical generated paths are:

```text
.harness/
.agents/skills/<maho-skill>/
.factory/skills/<maho-skill>/
.claude/skills/<maho-skill>/
.roo/skills/<maho-skill>/
```

Do not delete a shared Skill directory wholesale. It may contain user-owned files that MAHO preserved. If MAHO created `AGENTS.md`, review it before removal; MAHO never claims ownership of a pre-existing `AGENTS.md`.

When project changes are committed, prefer a normal version-control revert of the installation commit. This is reviewable and recoverable.
