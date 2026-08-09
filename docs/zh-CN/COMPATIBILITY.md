# 兼容矩阵

English: [`../en/COMPATIBILITY.md`](../en/COMPATIBILITY.md)

## 状态含义

- **文档确认**：当前一手文档描述了兼容的 Skill 路径。
- **适配器测试**：MAHO 的 disposable 文件系统测试能够创建预期路径并保留已有内容。
- **真实客户端冒烟**：实际安装的客户端在 disposable repo 中发现并加载了 Skill。
- **独立验收**：全新独立验收者接受了该客户端的证据。
- **已验证发布层级**：本版本已经具备有边界真实客户端证据和单独验收。
- **实验性发布层级**：文件系统适配器已经测试，但该客户端不属于本版本支持合同。

这些状态逐层累积。没有获得真实客户端和独立验收证据前，不会宣传为正式支持。

提交 `96f1489` 获得的是 MAHO 仓库侧私测验收，不能代替逐客户端验收。客户端只有在单独的有边界证据获得验收后才能进入“已验证”层级；仅适配器级客户端继续保持“实验性”。

| 目标 | 发布层级 | MAHO 使用的项目 Skill 路径 | 文档 | 适配器 | 真实客户端 | 独立验收 |
|---|---|---|---:|---:|---:|---:|
| Codex | 已验证 | `.agents/skills/` | 本机与当前约定确认 | 已测试 | 0.147.0-alpha.6.5 已通过 | Phase 17 有边界只读范围已通过 |
| Cursor | 已验证 | `.agents/skills/` | 已确认 | 已测试 | CLI 2026.08.04-aaa8809、Free 账号、`composer-2.5` 已通过 | Phase 18 有边界已提交证据范围已通过 |
| Factory/Droid | 已验证 | `.factory/skills/` | 已确认 | 已测试 | 独立安装 0.189.0、Kimi K3（Droid Core）已通过；保留此前 0.190.0 冒烟 | Phase 17 有边界只读范围已通过 |
| Claude Code | 已验证 | `.claude/skills/` | 已确认 | 已测试 | 2.1.197 客户端 + Kimi `k3-256k` 后端已通过 | Phase 14 有边界只读范围已通过 |
| Kilo Code | 已验证 | `.agents/skills/` | 兼容路径已确认 | 已测试 | 独立安装 7.4.20、`kilo/kilo-auto/free` 已通过 | Phase 16 有边界只读范围已通过 |
| Kimi Code | 已验证 | `.agents/skills/` | 兼容路径已确认 | 已测试 | 0.34.0、`kimi-code/k3` 已通过 | Phase 13 有边界只读范围已通过 |
| Gemini CLI | 实验性（仅适配器） | `.agents/skills/` | 兼容路径已确认 | 已测试 | 未运行；不属于 `0.1.0-beta.1` 已验证范围 | 不属于本版本范围 |
| OpenCode | 已验证 | `.agents/skills/` | 兼容路径已确认 | 已测试 | 1.18.13、内置 Kimi For Coding `k3-256k` 已通过 | Phase 15 有边界只读范围已通过 |
| Roo Code | 实验性（仅适配器） | `.roo/skills/` | 只有归档一手来源 | 已测试 | 未运行；不属于 `0.1.0-beta.1` 已验证范围 | 不属于本版本范围 |
| GitHub Copilot | 实验性（仅适配器） | `.agents/skills/` | 兼容路径已确认 | 已测试 | 未运行；不属于 `0.1.0-beta.1` 已验证范围 | 不属于本版本范围 |

当前证据集覆盖 `codex-cli 0.147.0-alpha.6.5`、独立 Factory Droid 0.189.0 与此前保留的 Desktop 0.190.0 冒烟、Kimi Code CLI 0.34.0、Claude Code 2.1.197、OpenCode 1.18.13、独立安装的 Kilo Code CLI 7.4.20，以及 Cursor Agent CLI 2026.08.04-aaa8809。七者都在只读 disposable repo 中发现或加载了 `completion-evidence`，并读取生成的项目宪法。Codex 保留原生串行读取事件，Droid 保留原生并发 `Skill` 与 `Read` 事件；二者在披露模型、计费、私有原生文件和夹具不可重算限制后，通过了 Phase 17 有边界独立验收。Kimi 保留了原生工具 transcript，并通过单独的 Phase 13 客户端验收。Claude Code 通过本地配置的 Kimi `k3-256k` 后端直接调用 `/completion-evidence`，保留原生 stream 证据，并通过 Phase 14 有边界独立验收。OpenCode 通过内置 Kimi For Coding `k3-256k` 提供商保留原生 `skill` 与 `read` 事件，并通过 Phase 15 有边界独立验收。Kilo 通过显式 `kilo/kilo-auto/free` 路由保留原生并发 `skill` 与 `read` 证据，并在原样保存一次 INCONCLUSIVE 和一次 FAIL 后通过 Phase 16 有边界独立验收。Cursor 使用 Free 账号和非 Fast `composer-2.5`，把 Skill 名称解析到项目文件，执行两次互相重叠的原生读取，返回正确 INCONCLUSIVE 完成语义，并通过 Phase 18 已提交证据一致性验收；私有原生工件没有交给验收者。Gemini CLI、Roo Code 和 GitHub Copilot 在本版本中只作为需要显式选择的实验性适配器提供。

## 已核对的一手文档

- [Factory Skills](https://docs.factory.ai/cli/configuration/skills)
- [Cursor Agent Skills](https://cursor.com/docs/skills)
- [Claude Code Skills](https://code.claude.com/docs/en/skills)
- [Kilo Code Skills](https://kilo.ai/docs/customize/skills)
- [Kimi Code Agent Skills](https://www.kimi.com/code/docs/en/kimi-code-cli/customization/skills.html)
- [Gemini CLI Agent Skills](https://geminicli.com/docs/cli/using-agent-skills/)
- [OpenCode Agent Skills](https://opencode.ai/docs/skills)
- [GitHub Copilot Agent Skills](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills)
- [已归档的 Roo Code 源码](https://github.com/RooCodeInc/Roo-Code)

可复制原始地址：

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
