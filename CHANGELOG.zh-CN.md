# 变更日志

English: [`CHANGELOG.md`](CHANGELOG.md)

所有重要变更记录在这里，日期使用 UTC。

## 0.1.0-beta.1 — 2026-08-14

### 新增

- MAHO 产品身份和 `maho` 命令。
- 安全的 `maho init` 预览与应用流程，以及明确的零覆盖回执。
- 英文和简体中文终端输出与 Skill 目录。
- 面向首批十个编程智能体目标的薄适配器，其中包括 Cursor。
- 包含七个已验证客户端和三个需显式选择的实验性适配器的发布分层合同；`--agent all` 只安装已验证客户端。
- Apache License 2.0 发布文件和经过净化的公开导出清单。
- 将运行时 Skills、Stack Packs、Schema 和模板装入 wheel。

### 保留

- 原有发现、就绪度、bootstrap、验证、上下文审计、受保护快照和证据语义。
- 内部研发仓库中原样保存的失败、中止、红队和独立验收证据。

### 限制

- Codex CLI 0.147.0-alpha.6.5 与独立 Factory Droid 0.189.0 已通过原生 transcript 支持的 Skill 加载、宪法读取和 Phase 17 有边界独立验收；此前 Droid 0.190.0 冒烟仍原样保留。
- Kimi Code 和使用 Kimi 后端的 Claude Code 已分别通过有边界的逐客户端验收。
- OpenCode 1.18.13 通过内置 Kimi For Coding 提供商完成了原生 Skill 加载与宪法读取，并通过 Phase 15 有边界范围的独立验收。
- 独立安装的 Kilo Code CLI 7.4.20 通过 `kilo/kilo-auto/free` 完成了原生 Skill 加载与宪法读取，并在原样保存一次 INCONCLUSIVE 和一次 FAIL 后通过该 Phase 16 有边界范围的独立验收。
- Cursor Agent CLI 2026.08.04-aaa8809 使用 Free 账号和非 Fast `composer-2.5`，通过 Skill 发现/加载、宪法读取、正确 INCONCLUSIVE 完成语义及 Phase 18 有边界已提交证据验收；私有原生工件没有发送给验收者。
- Gemini CLI、Roo Code 和 GitHub Copilot 是仅适配器级的实验目标，不属于 `0.1.0-beta.1` 已验证支持合同。
- 发布身份署名为 MAHO contributors，项目标识由 Future Apparatus Laboratory 维护，源码地址指向 `Do-fei/maho-harness`。
