---
name: harness-discovery
description: Inspect a repository before planning or coding, generate bounded stack and readiness evidence, and propose a minimal Project Constitution without overwriting existing guidance.
---

# Harness Discovery

Use for a new repository, an unfamiliar stack, or when supported commands and boundaries are uncertain.

1. Run `python3 -m harness discover <project>`.
2. Inspect Git state, existing `AGENTS.md`, README, build metadata, and proposed checks.
3. Run `python3 -m harness readiness <project>`.
4. If enabling the Harness, run bootstrap without `--apply` first and review its plan.
5. Apply only within the resolved repository; never overwrite existing guidance.
6. Report detected facts, unknowns, proposed commands, and readiness findings separately.

Success: the repository has reviewable discovery/readiness evidence and no inferred command is represented as executed.
