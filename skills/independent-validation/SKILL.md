---
name: independent-validation
description: Validate a material implementation from fresh context with a separate acceptance contract, read-only authority, adversarial boundary checks, and an independent PASS, FAIL, or INCONCLUSIVE verdict.
---

# Independent Validation

Use only when a fresh validator may change a material acceptance decision.

1. Receive specification, acceptance criteria, final artifacts, and existing evidence.
2. Do not receive or repeat the implementer's private rationale or conclusion.
3. Default to read-only authority.
4. Attack hidden cases, trust boundaries, test gaming, and user-visible behavior.
5. Derive negative cases from the invariant, including adjacent, prefix/confusable, encoding, missing-state, and alias/symlink boundaries when relevant. Do not test only the newly added branch.
6. Treat “preserve current behavior” as a compatibility constraint, not permission to preserve behavior that violates the stated safety invariant.
7. Preserve exact commands/observations and expected-versus-observed results.
8. Return `PASS`, `FAIL`, or `INCONCLUSIVE` using `templates/INDEPENDENT_VALIDATION.md`.
9. Record shared-model, shared-test, and unavailable-evidence limitations.

A self-review is useful but must never be labeled independent validation.
