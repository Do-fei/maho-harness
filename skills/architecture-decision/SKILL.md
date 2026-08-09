---
name: architecture-decision
description: Challenge disproportionate implementation requests, compare viable technical approaches, and record an evidence-backed recommendation or ADR when architecture choice matters.
---

# Architecture Decision

Trigger only when approaches differ materially in compatibility, data, security, operations, or irreversible cost.

1. Restate the underlying goal separately from the proposed technology.
2. Test whether the proposal is over-engineered; include the simplest viable option.
3. Compare two or three options using evidence, reversibility, migration, and wrong-decision cost.
4. Recommend one option with confidence and falsifiers.
5. Escalate with one Decision Packet only when user/product judgment or new authority is required.
6. Otherwise record the decision using `templates/ADR.md` and proceed.

Success: the decision can be revisited from evidence without replaying private reasoning.
