# Contributing to MAHO

Chinese: [`CONTRIBUTING.zh-CN.md`](CONTRIBUTING.zh-CN.md)

Thank you for improving evidence-first agentic engineering.

## Before changing code

1. State the user-visible outcome and non-goals.
2. Keep the change narrow and reversible.
3. Add or update a test that proves the outcome.
4. Preserve failed and aborted evidence; do not rewrite history to make a result look clean.
5. Update English and Simplified Chinese human-facing documentation together.

Run the local gate:

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q harness scripts tests
```

Agent compatibility tests must use disposable repositories. Never put credentials, production data, private absolute paths, or paid-account assumptions in fixtures.

## Developer Certificate of Origin

Contributions use the Developer Certificate of Origin 1.1. Sign off commits with:

```bash
git commit -s
```

The sign-off certifies that you have the right to submit the contribution under Apache License 2.0. MAHO does not require a CLA for the first public release.
