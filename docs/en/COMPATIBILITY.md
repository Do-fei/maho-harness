# Compatibility matrix

Chinese: [`../zh-CN/COMPATIBILITY.md`](../zh-CN/COMPATIBILITY.md)

## Meaning of status

- **Docs confirmed**: current primary documentation describes a compatible Skill location.
- **Adapter tested**: MAHO's disposable filesystem test created and preserved the expected paths.
- **Client smoke tested**: a real installed client discovered and loaded the Skill in a disposable repository.
- **Accepted**: a fresh independent validator accepted the client evidence.
- **Verified release tier**: both bounded real-client evidence and separate acceptance exist for this release.
- **Experimental release tier**: the filesystem adapter is tested, but the client is outside this release's support contract.

These states are cumulative. An adapter is not advertised as officially supported until the required real-client and acceptance evidence exists.

The MAHO repository-side private-beta acceptance at `96f1489` does not replace per-client acceptance. A client enters the Verified tier only after a separate validator accepts its bounded evidence; adapter-only clients remain Experimental.

| Target | Release tier | Project Skill root used by MAHO | Documentation | Adapter | Real client | Independent acceptance |
|---|---|---|---:|---:|---:|---:|
| Codex | Verified | `.agents/skills/` | Confirmed locally/current convention | Tested | Passed: 0.147.0-alpha.6.5 | Passed: Phase 17 bounded read-only scope |
| Cursor | Verified | `.agents/skills/` | Confirmed | Tested | Passed: CLI 2026.08.04-aaa8809, Free account, `composer-2.5` | Passed: Phase 18 bounded committed-evidence scope |
| Factory/Droid | Verified | `.factory/skills/` | Confirmed | Tested | Passed: standalone 0.189.0, Kimi K3 (Droid Core); earlier 0.190.0 smoke retained | Passed: Phase 17 bounded read-only scope |
| Claude Code | Verified | `.claude/skills/` | Confirmed | Tested | Passed: 2.1.197 client + Kimi `k3-256k` backend | Passed: Phase 14 bounded read-only scope |
| Kilo Code | Verified | `.agents/skills/` | Confirmed compatibility path | Tested | Passed: standalone 7.4.20, `kilo/kilo-auto/free` | Passed: Phase 16 bounded read-only scope |
| Kimi Code | Verified | `.agents/skills/` | Confirmed compatibility path | Tested | Passed: 0.34.0, `kimi-code/k3` | Passed: Phase 13 bounded read-only scope |
| Gemini CLI | Experimental (adapter-only) | `.agents/skills/` | Confirmed compatibility path | Tested | Not run; outside the `0.1.0-beta.1` verified scope | Not in release scope |
| OpenCode | Verified | `.agents/skills/` | Confirmed compatibility path | Tested | Passed: 1.18.13, built-in Kimi For Coding `k3-256k` | Passed: Phase 15 bounded read-only scope |
| Roo Code | Experimental (adapter-only) | `.roo/skills/` | Archived primary source only | Tested | Not run; outside the `0.1.0-beta.1` verified scope | Not in release scope |
| GitHub Copilot | Experimental (adapter-only) | `.agents/skills/` | Confirmed compatibility path | Tested | Not run; outside the `0.1.0-beta.1` verified scope | Not in release scope |

The evidence set covers `codex-cli 0.147.0-alpha.6.5`, standalone Factory Droid 0.189.0 plus the preserved earlier 0.190.0 Desktop smoke, Kimi Code CLI 0.34.0, Claude Code 2.1.197, OpenCode 1.18.13, standalone Kilo Code CLI 7.4.20, and Cursor Agent CLI 2026.08.04-aaa8809. All seven discovered or loaded `completion-evidence` and read the generated Constitution in a read-only disposable repository. Codex retained native serial read events, while Droid retained native concurrent `Skill` and `Read` events; both passed bounded Phase 17 independent acceptance, with model, billing, private-native-file, and fixture-reproducibility limits disclosed. Kimi retained a native tool transcript and passed separate Phase 13 client acceptance. Claude Code retained native stream evidence for direct `/completion-evidence` invocation through a locally configured Kimi `k3-256k` backend and passed bounded Phase 14 independent acceptance. OpenCode retained native `skill` and `read` events through its built-in Kimi For Coding `k3-256k` provider and passed bounded Phase 15 independent acceptance. Kilo retained native concurrent `skill` and `read` evidence through the explicit `kilo/kilo-auto/free` route and passed bounded Phase 16 independent acceptance after one preserved INCONCLUSIVE and one preserved FAIL. Cursor used a Free account and non-Fast `composer-2.5`, resolved the Skill name to its project file, performed two overlapping native reads, returned correct INCONCLUSIVE completion semantics, and passed Phase 18 acceptance for committed-evidence consistency; private native artifacts were not shared with the validator. Gemini CLI, Roo Code, and GitHub Copilot remain available only as explicit experimental adapters for this release.

## Primary documentation checked

- [Factory Skills](https://docs.factory.ai/cli/configuration/skills)
- [Cursor Agent Skills](https://cursor.com/docs/skills)
- [Claude Code Skills](https://code.claude.com/docs/en/skills)
- [Kilo Code Skills](https://kilo.ai/docs/customize/skills)
- [Kimi Code Agent Skills](https://www.kimi.com/code/docs/en/kimi-code-cli/customization/skills.html)
- [Gemini CLI Agent Skills](https://geminicli.com/docs/cli/using-agent-skills/)
- [OpenCode Agent Skills](https://opencode.ai/docs/skills)
- [GitHub Copilot Agent Skills](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills)
- [Archived Roo Code source](https://github.com/RooCodeInc/Roo-Code)

Raw URLs:

```text
https://docs.factory.ai/cli/configuration/skills
https://cursor.com/docs/skills
https://code.claude.com/docs/en/skills
https://kilo.ai/docs/customize/skills
https://www.kimi.com/code/docs/en/kimi-code-cli/customization/skills.html
https://geminicli.com/docs/cli/using-agent-skills/
https://opencode.ai/docs/skills
https://docs.github.com/en/copilot/concepts/agents/about-agent-skills
https://github.com/RooCodeInc/Roo-Code
```
