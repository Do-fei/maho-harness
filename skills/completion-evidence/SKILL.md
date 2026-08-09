---
name: completion-evidence
description: Run accepted project checks, inspect the changed boundary and repository state, and produce a criterion-to-evidence completion report without storing raw secret-bearing output.
---

# Completion Evidence

1. Confirm the active Acceptance Contract and project configuration.
2. Run accepted project checks through an available Harness launcher. If the Harness runtime is not installed or reachable, run the accepted direct commands, record the runner as unavailable, and do not treat runner availability as project failure.
3. Inspect the diff, Git state, generated paths, and boundary-specific runtime/security evidence.
4. Map each criterion to a command or observation and artifact.
5. Record skipped/unavailable checks and unresolved work.
6. Use `PASS`, `FAIL`, or `INCONCLUSIVE`; an unrun check is never a pass.
7. If the Acceptance Contract requires independent validation, do not issue overall `PASS` until a separate validator artifact exists. Without an available validator, return `INCONCLUSIVE`.
8. Do not paste secrets or retain raw tool output in durable evidence.

Success: another engineer can reproduce the decision from repository artifacts.
