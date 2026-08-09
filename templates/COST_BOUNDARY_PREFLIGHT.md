# Cost Boundary Preflight

Use before any external model call that can consume a subscription allowance, credits, or paid usage.

## Attestation

- Timestamp:
- Product and version:
- Exact model:
- Billed/model category:
- Selected allowance tab:
- Explicit current-route text (`You are using ...`):
- 5-hour usage:
- Weekly usage:
- Monthly usage:
- Selected exhaustion/fallback behavior:
- Paid/Extra fallback selected: YES / NO / UNKNOWN
- Paid balance visible: YES / NO / UNKNOWN
- User authorization for verified current route:
- Maximum calls in this batch:
- Stop threshold:
- Disposable target path:
- Push/deploy/production access: PROHIBITED
- Recheck after:

## Go / no-go

Evaluate the allowance state in this order:

1. verify the selected allowance tab;
2. verify explicit current-route text;
3. read usage values from that same tab;
4. verify the selected fallback independently;
5. match the verified current route to the user's authorization.

Proceed only if every decision-relevant field is known, the selected allowance and explicit current route match the user's authorization, paid fallback is not selected unless explicitly authorized, and the target/action scope is bounded. A visible paid balance is not itself evidence that paid fallback is active. Standard exhaustion is not a stop condition when a separately authorized subscription-included route is verified as active.

If state is ambiguous, resolve it through read-only inspection, such as selecting the relevant usage tab. If an approval reviewer rejects the call, record `NOT RUN`, preserve the exact reason, and do not use a workaround. Retry only after correcting the evidence or obtaining new authorization when the actual route or cost boundary changed.
