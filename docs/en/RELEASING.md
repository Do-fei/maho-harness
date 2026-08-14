# Release process

Chinese: [`../zh-CN/RELEASING.md`](../zh-CN/RELEASING.md)

The development repository contains preserved internal evidence and private absolute paths. It must never be published directly.

## Release gates

1. All unit, packaging, disposable-repository, and bilingual-parity checks pass.
2. The compatibility matrix contains no unsupported claim.
3. Copyright and trademark holder placeholders are replaced.
4. Public repository URLs in `pyproject.toml` are replaced.
5. The sanitized export contains no internal reports, experiments, private paths, credentials, caches, or raw logs.
6. Wheel and source archive install successfully in a clean temporary environment.
7. The exact public commit has a GPG- or SSH-signed annotated tag, and the tag verifies locally before publication.
8. A fresh, read-only independent acceptor returns `PASS` for the exact candidate commit and artifact hashes.
9. The owner separately approves external GitHub and PyPI publication.

## Version path

```text
0.1.0-beta.1 -> 0.1.0-rc.1 -> 0.1.0
```

The `0.1.0-beta.1` support contract contains seven verified clients. Gemini CLI, Roo Code, and GitHub Copilot remain adapter-only experimental targets; they must not be called supported until separate real-client and independent acceptance pass.

## Publication order

1. Push the sanitized candidate and signed annotated tag while the repository is still private.
2. Publish and verify the GitHub prerelease while the repository is still private.
3. Enable and verify private vulnerability reporting.
4. Change repository visibility to public, then verify source, tag, release notes, and assets without relying on an authenticated session.
5. Obtain separate owner approval for PyPI, upload once, and verify the live project page and install path.

`SHA256SUMS` and GitHub asset digests provide integrity evidence, but they do not replace the signed tag and do not claim byte-for-byte reproducibility across build environments.

## External boundaries

Authentication, account changes, billing, signing identities, repository creation, pushing, and package publication require explicit user confirmation at the point of action. Subscription-only test authorization does not authorize extra credits or API spending.
