# Security policy

Chinese: [`SECURITY.zh-CN.md`](SECURITY.zh-CN.md)

## Supported versions

Only the latest published beta or stable release receives security fixes. No public release exists yet; `0.1.0-beta.1` is under private testing.

## Report a vulnerability

Do not open a public issue for an unpatched vulnerability. Use [GitHub private vulnerability reporting](https://github.com/Do-fei/maho-harness/security/advisories/new). Availability of that private channel must be verified before publication; never place vulnerability details in a public issue if it is unavailable.

Include the affected version, a minimal reproduction in a disposable repository, impact, and any relevant boundary conditions. Do not include real credentials or private production data.

## Security boundary

MAHO is an engineering governance tool, not a security sandbox. It does not bypass or replace the host agent's permissions, approvals, operating-system controls, or account policies.

MAHO:

- defaults initialization to dry-run;
- refuses to overwrite existing project files during bootstrap or Skill installation;
- rejects configured shell-code execution and likely secret-bearing arguments;
- hashes validation output instead of retaining raw stdout or stderr;
- treats unavailable evidence as `INCONCLUSIVE`, never as `PASS`.

Project validation commands are still trusted project code. Review them before execution and use disposable repositories for destructive compatibility tests.
