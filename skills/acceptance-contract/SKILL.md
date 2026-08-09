---
name: acceptance-contract
description: Define scope, non-goals, risk, acceptance criteria, planned evidence, rollback, and stop conditions before a non-trivial software change.
---

# Acceptance Contract

1. Read the Project Constitution and current repository state.
2. Translate the request into observable outcomes, not implementation activity.
3. Record goal, non-goals, assumptions, allowed/protected scope, and risk class.
4. Define functional, regression, security, runtime, and documentation checks only when relevant.
5. Mark unavailable evidence `INCONCLUSIVE`; never predeclare it `PASS`.
6. State rollback and replan triggers.
7. Decide whether independent validation can overturn a material decision.
8. Default independent validation to required for security/trust boundaries, authorization, destructive migration, or other contracts where a plausible false positive could cause material harm. Record an explicit reason when opting out.

Use `templates/ACCEPTANCE_CONTRACT.md`. Keep the contract proportional: trivial L1 work can be a short task plan.
