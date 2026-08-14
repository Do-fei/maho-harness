<p align="center">
  <img src="https://raw.githubusercontent.com/Do-fei/maho-harness/main/assets/brand/maho-readme-banner.png" alt="MAHO — Model-Agnostic Harness for Outcomes. Proof before done." width="100%">
</p>

<p align="center">
  <strong>Evidence-first engineering governance for coding agents. / 面向编程智能体的证据优先工程治理。</strong><br>
  Give coding agents a project they can understand—and results you can trust.<br>
  让编程智能体真正读懂项目，也让它说“完成”时拿得出证据。
</p>

<p align="center">
  <a href="README.en.md">English</a> · <a href="README.zh-CN.md">简体中文</a>
</p>

> **Release / 发布** — `0.1.0-beta.1` is MAHO's first public Beta. Its source tag is signed and its GitHub Release wheel is checksummed. PyPI is not published yet. / `0.1.0-beta.1` 是 MAHO 的首个公开 Beta：源码标签带签名，GitHub Release 中的 wheel 带校验和；PyPI 尚未发布。

## Fast code is not the same as finished software / 写出代码，不等于完成软件

A coding agent can produce a patch in minutes. The difficult questions live around that patch: Did it read the repository's rules? Did it touch a protected file? Did it run the checks that actually matter? What happens when a check times out? Can the next agent understand the result without rereading a long chat? Should the agent that wrote the code also be allowed to declare it complete?

编程智能体几分钟就能产出修改。真正困难的问题都在修改周围：它是否读过仓库规范？是否碰了受保护文件？是否运行了真正算数的检查？检查超时该怎么判断？换一个智能体后，能否不重读漫长对话就理解结果？写代码的智能体是否应该同时宣布自己的工作合格？

Most agent tools leave these decisions inside the prompt. Each session reconstructs the process from scratch, and “done” sometimes means only that the agent stopped working.

多数智能体工具把这些决定留在提示词里。每次会话都临时重建一遍流程，最后的“完成”有时只代表智能体停止工作了。

**MAHO adds the missing engineering loop.** It puts project rules, accepted checks, client Skills, safety boundaries, and completion evidence in the repository, where humans and different coding agents can share them.

**MAHO 补上的正是这套工程闭环。** 它把项目规范、已确认检查、客户端 Skills、安全边界和完成证据留在仓库里，让人和不同的编程智能体都使用同一套依据。

| Without MAHO / 没有 MAHO | With MAHO / 使用 MAHO |
|---|---|
| Each agent guesses how the project works. / 每个智能体临时猜一套做法。 | Every supported client reads the same Constitution and engineering Skills. / 所有受支持客户端读取同一份项目宪法和工程 Skills。 |
| Setup may merge or replace existing guidance. / 接入过程可能合并或覆盖已有规范。 | Initialization starts with a dry-run and creates only missing paths. / 初始化默认只读预览，只创建缺失路径。 |
| The agent chooses whichever test looks convenient. / 智能体挑一个方便的测试就开始跑。 | Checks are proposed from repository facts, then approved by a maintainer. / 根据仓库事实提出检查，再由维护者确认。 |
| One green command is treated as proof of the whole task. / 一条绿色命令被当成整个任务的证明。 | Required checks, protected paths, timeouts, and evidence states define what was actually proved. / 必需检查、受保护路径、超时和证据状态共同定义究竟证明了什么。 |
| Failed attempts disappear behind the final success. / 失败尝试被最后一次成功盖住。 | `FAIL` and `INCONCLUSIVE` remain visible. / `FAIL` 与 `INCONCLUSIVE` 会继续留在记录里。 |
| The implementer grades its own work. / 实现者自己给自己判分。 | A fresh agent or human can accept the exact candidate independently. / 新的智能体或人类可以独立验收精确候选。 |

## How MAHO turns agent work into software engineering / MAHO 如何实现工程闭环

```text
Inspect the repository  →  Agree on the contract  →  Let the agent work
检查仓库                    确认项目约定                智能体执行任务

          →  Run accepted checks  →  Keep evidence  →  Accept independently
             运行已确认检查            保留证据            独立验收
```

### 1. Inspect before editing / 修改前，先看懂仓库

`maho discover` reads bounded repository signals: existing instructions, manifests, stack markers, test configuration, and likely validation commands. It proposes what may matter; it never silently turns a guess into policy. `maho readiness` then shows what is still missing before reliable agent work can begin.

`maho discover` 从有边界的仓库信号中识别已有规范、清单文件、技术栈标记、测试配置和候选验证命令。它只提出建议，不会把猜测偷偷变成项目政策。随后，`maho readiness` 会指出可靠开展智能体工作之前还缺什么。

### 2. Make the project contract explicit / 把项目约定写清楚

MAHO creates `.harness/PROJECT_CONSTITUTION.md` for goals, constraints, authority, protected areas, and the definition of success. A companion `.harness/project.json` stores accepted checks, proposed checks, protected and generated paths, runtime probes, and Stack Packs in a form the CLI can load.

MAHO 使用 `.harness/PROJECT_CONSTITUTION.md` 记录目标、约束、权限、受保护范围和完成标准；再用 `.harness/project.json` 保存已接受检查、候选检查、受保护与生成路径、运行探针和 Stack Packs，让 CLI 可以直接加载。

Generated content is only a starting point. A maintainer decides which proposed checks become accepted checks. / 自动生成的内容只是起点。哪些候选检查能够成为正式检查，最终由维护者确认。

### 3. Give different clients the same playbook / 让不同客户端使用同一套工程方法

MAHO maintains one canonical catalog of engineering Skills and maps it into each client's discovery path. Codex, Cursor, Claude Code, and Factory/Droid may load Skills differently, but the underlying rules do not fork into seven unrelated copies.

MAHO 维护一份规范的工程 Skills，再把它映射到不同客户端的发现路径。Codex、Cursor、Claude Code 和 Factory/Droid 的读取方式可以不同，但背后的规则不会分裂成七套各自演化的副本。

The included Skills cover harness discovery, acceptance contracts, architecture decisions, completion evidence, independent validation, and retrospectives that preserve failed attempts. / 内置 Skills 覆盖框架发现、验收合同、架构决策、完成证据、独立验收，以及保留失败尝试的复盘。

### 4. Protect an existing repository / 接入时不伤害已有项目

`maho init` is read-only unless `--apply` is present. Its preview names every path it would create or preserve. Apply mode creates missing files only; an existing file or Skill directory is never merged or overwritten.

除非显式提供 `--apply`，否则 `maho init` 只做预览。预览会列出准备创建和保留的每一条路径。应用模式也只创建缺失文件；已有文件或 Skill 目录不会被合并或覆盖。

During validation, MAHO runs accepted commands as direct argument arrays instead of shell strings, enforces time limits, and takes bounded snapshots of protected paths. If a safety or resource boundary prevents a trustworthy result, validation fails closed instead of quietly lowering the bar.

验证时，MAHO 使用直接参数数组运行已接受命令，而不是拼接 shell 字符串；同时限制执行时间，并为受保护路径创建有边界快照。如果安全或资源限制导致结果不再可信，流程会失败关闭，而不是悄悄降低标准。

### 5. Replace “trust me” with a receipt / 用回执替代“相信我”

`maho validate` records check state, exit status, timing, output byte counts, and protected-path hashes within explicit bounds. `PASS` means the accepted evidence supports the claim. `FAIL` means the check or protected state disproves it. `INCONCLUSIVE` means the required proof could not be obtained.

`maho validate` 会在明确边界内记录检查状态、退出状态、耗时、输出字节数和受保护路径哈希。`PASS` 表示已接受证据支持结论；`FAIL` 表示检查结果或受保护状态否定结论；`INCONCLUSIVE` 表示没有取得作出判断所需的证据。

A broken environment is not a passing test, but it is not always proof that the code is broken. MAHO keeps that uncertainty visible. / 环境损坏不等于测试通过，但也不总能证明代码一定有错。MAHO 会把这种不确定性原样保留下来。

### 6. Separate implementation from acceptance / 把实现和验收分开

For consequential work, the final reviewer should be fresh: another agent or a person who receives the exact candidate, acceptance contract, and evidence. The implementer can fix a failure, but it does not get to rename the earlier failure or silently lower the standard.

对重要任务，最终审查者应该是全新的：由另一个智能体或人类拿到精确候选、验收合同和证据后独立判断。实现者可以修复失败，但不能给早先的失败改名，也不能悄悄降低验收标准。

That is the meaning of **Proof before done. / 先证明，再完成。**

<details>
<summary><strong>See the machine-readable contract / 查看机器可读合同</strong></summary>

Checks in `proposed_checks` are suggestions. Only entries deliberately moved into `checks` can decide validation. / `proposed_checks` 中的检查只是建议；只有经确认移入 `checks` 的条目才能参与正式验证。

```json
{
  "schema_version": 1,
  "project_name": "example",
  "checks": [
    {
      "id": "unit",
      "command": ["python3", "-m", "unittest", "discover"],
      "cwd": ".",
      "required": true,
      "timeout_seconds": 900
    }
  ],
  "proposed_checks": [],
  "protected_paths": ["AGENTS.md", ".harness/project.json"],
  "generated_paths": [".harness/runs"],
  "runtime_probes": [],
  "selected_stack_packs": []
}
```

</details>

## A concrete task / 一个具体任务

Suppose you ask a coding agent to change authentication in an existing Node.js application. Without a harness, it might edit the login flow, run one nearby unit test, and say the task is complete. It may never notice the repository's `AGENTS.md`, a required typecheck, an integration test in another package, or a protected lockfile.

假设你让编程智能体修改一个现有 Node.js 应用的登录流程。没有工程框架时，它可能改完登录逻辑，跑一项附近的单元测试，然后宣布完成。它可能根本没有注意仓库里的 `AGENTS.md`、必须执行的类型检查、另一个 package 中的集成测试，或者不能修改的锁文件。

With MAHO / 使用 MAHO 后：

1. Discovery finds the existing guidance and relevant stack signals. / 发现阶段先找到已有规范和相关技术栈信号。
2. The Constitution states the task, constraints, protected paths, and expected result. / 项目宪法写明任务、约束、受保护路径和预期结果。
3. A maintainer approves the checks that count—perhaps unit tests, typecheck, and a bounded runtime probe. / 维护者确认真正算数的检查，例如单元测试、类型检查和有边界运行探针。
4. The coding agent follows the same acceptance-contract and completion-evidence Skills regardless of client. / 无论使用哪个客户端，编程智能体都遵循同一套验收合同与完成证据 Skills。
5. Validation runs the accepted checks and verifies protected paths. / 验证阶段运行已接受检查，并确认受保护路径没有被破坏。
6. A fresh reviewer judges the exact candidate from the contract and evidence. / 新的审查者根据合同和证据，判断这个精确候选是否合格。

MAHO did not write the authentication feature. It made the path from request to accepted change visible and repeatable. / MAHO 没有替你编写登录功能。它让“提出需求”到“接受修改”之间的过程变得可见、可重复。

## Why teams keep MAHO in the repository / 为什么 MAHO 值得留在仓库里

### Change agents without rebuilding the process / 更换智能体，不必重建工程流程

The project contract belongs to the repository, not to a vendor account or one chat history. A team can move between supported clients while keeping the same definition of success. / 项目约定留在仓库里，不属于某个厂商账号，也不困在一段聊天记录中。团队可以在受支持客户端之间切换，同时保留同一份完成标准。

### Add governance without surrendering the repository / 引入治理，但不交出仓库

MAHO is local and dependency-free at runtime. It does not require a hosted MAHO service, service account, or model API key. Its contract, Skills, and evidence are ordinary files that can be inspected, versioned, and removed. / MAHO 本地运行，且没有 Python 运行时依赖。它不要求托管式 MAHO 服务、服务账号或模型 API Key。合同、Skills 和证据都是普通文件，可以查看、纳入版本管理，也可以卸载。

### Adopt it safely in real projects / 可以安全接入真正的已有项目

Preview is the default. Existing paths are preserved. Installation reports exactly what it would create, what it kept, and that it overwrote zero files. / 默认行为是预览，已有路径会被保留。安装结果会明确告诉你准备创建什么、保留了什么，以及覆盖文件数量为零。

### Keep evidence after the chat ends / 对话结束后，证据还在

The next person or agent does not need to trust a conversation summary. It can inspect the same contract, candidate, and receipts—and disagree when the evidence does not support the claim. / 下一位维护者或智能体不必相信一段对话摘要。它可以检查同一份合同、精确候选和验证回执；证据不足时，也可以得出不同结论。

### Make honest failure useful / 让失败真正有用

MAHO does not optimize for a wall of green badges. It preserves `FAIL`, distinguishes missing proof as `INCONCLUSIVE`, and records the scope of a `PASS`. Failure becomes the next action, not an embarrassing artifact to hide. / MAHO 不追求一墙绿色徽章。它保留 `FAIL`，把缺少证据标为 `INCONCLUSIVE`，并写清 `PASS` 的适用范围。失败会成为下一步行动的依据，而不是需要隐藏的尴尬记录。

## Start in five minutes / 五分钟开始

MAHO requires Python 3.10 or later and has no runtime Python dependencies. Download the wheel and `SHA256SUMS` from the [GitHub Release](https://github.com/Do-fei/maho-harness/releases/tag/v0.1.0-beta.1). / MAHO 需要 Python 3.10 或更高版本，没有 Python 运行时依赖。请从 [GitHub Release](https://github.com/Do-fei/maho-harness/releases/tag/v0.1.0-beta.1) 下载 wheel 和 `SHA256SUMS`。

```bash
# Verify and install / 校验并安装
shasum -a 256 -c SHA256SUMS
pipx install ./maho_harness-0.1.0b1-py3-none-any.whl

# 1. Preview only: MAHO writes nothing / 只读预览：不会写入仓库
maho --locale zh-CN init /path/to/project --agent codex

# 2. Apply the reviewed plan; existing paths are preserved
# 应用审阅后的计划；已有路径不会被覆盖
maho --locale zh-CN init /path/to/project --agent codex --apply --yes

# 3. Inspect readiness and proposed checks / 检查准备度与候选检查
maho discover /path/to/project
maho readiness /path/to/project

# 4. Approve checks in .harness/project.json, then validate
# 在 .harness/project.json 中确认检查，然后执行验证
maho validate /path/to/project
```

Use `--agent all` to install adapters for all seven verified clients. Add another client later without replacing the first one. / 使用 `--agent all` 可安装全部七个已验证客户端的适配器；以后也可以继续添加客户端，不会替换已有配置。

## Client support / 支持的智能体

| Release tier / 发布层级 | Clients / 客户端 | What the label means / 标签含义 |
|---|---|---|
| **Verified / 已验证** | Codex, Cursor, Factory/Droid, Claude Code, Kilo Code, Kimi Code, OpenCode | Filesystem adapter, bounded real-client test, and separate acceptance exist for this Beta. / 本 Beta 已完成文件系统适配、有边界真实客户端测试和单独验收。 |
| **Experimental / 实验性** | Gemini CLI, Roo Code, GitHub Copilot | Adapter behavior is tested; real-client behavior and independent acceptance remain outside this release. / 已验证适配器行为；真实客户端行为和独立验收不属于本版本。 |

The [compatibility matrix](docs/en/COMPATIBILITY.md) / [兼容矩阵](docs/zh-CN/COMPATIBILITY.md) records exact versions, discovery paths, evidence boundaries, and acceptance phases.

## Similar projects—and where MAHO fits / 同类方案与 MAHO 的位置

MAHO is not the only project trying to make AI-assisted development more disciplined. The closest projects solve neighboring parts of the problem. This comparison reflects their official documentation as checked on 2026-08-14. / MAHO 不是唯一一个尝试让 AI 辅助开发更规范的项目。下面这些方案解决的是相邻问题；比较基于 2026-08-14 查阅的官方资料。

- **[GitHub Spec Kit](https://github.github.com/spec-kit/)** is stronger at specification-driven feature planning: Constitution, specification, plan, tasks, and implementation. MAHO concentrates more on repository safety, executable checks, evidence states, and independent completion acceptance. / 更擅长从宪法、规格、计划、任务到实现的功能规划；MAHO 更集中于仓库安全、可执行检查、证据状态和独立完成验收。
- **[OpenSpec](https://github.com/Fission-AI/OpenSpec)** is stronger as an iterative specification and change-management system, especially for existing projects. MAHO adds protected-path validation and a cross-client completion-evidence contract. / 更擅长迭代式规格与变更管理，尤其适合已有项目；MAHO 增加关键路径验证和跨客户端完成证据合同。
- **[BMAD Method](https://github.com/bmad-code-org/BMAD-METHOD)** covers a broader Agile lifecycle with specialist agent roles. MAHO is smaller and governs work performed by the coding agent you already use. / 使用专业智能体角色覆盖更完整的敏捷生命周期；MAHO 更小，专注治理你已经在用的编程智能体。
- **Client-native rules and hooks / 客户端原生规则与 Hooks** provide deep control inside one product but are usually vendor-specific. MAHO keeps the contract and canonical Skills in the repository and maps them across clients. / 能在单一产品中提供深入控制，但通常绑定厂商；MAHO 把合同和规范 Skills 留在仓库，再适配多个客户端。

These tools can complement MAHO. A team may use Spec Kit or OpenSpec to decide **what to build**, then use MAHO to define **what counts as done and how that result is independently checked**. / 这些工具可以和 MAHO 配合：团队可以用 Spec Kit 或 OpenSpec 决定**要做什么**，再用 MAHO 定义**怎样才算完成，以及如何独立复核**。

### Honest trade-offs / 需要诚实说明的缺点

- MAHO is an early Beta with a much smaller ecosystem than the established projects above. / MAHO 仍处于早期 Beta，生态规模远小于上述成熟项目。
- Seven clients are verified, not every agent, operating system, model route, or client version. / 当前只验证了七个客户端，并非所有智能体、操作系统、模型路由或客户端版本。
- Human approval of the Constitution and checks adds deliberate work. That friction is useful for consequential changes and unnecessary for some throwaway tasks. / 项目宪法和检查需要人工确认；重要修改值得这样做，但对某些一次性小任务来说会显得过重。
- Evidence receipts keep bounded metadata and hashes rather than complete raw terminal output. Deep debugging may still require CI or client logs. / 证据回执保留有边界元数据和哈希，而不是完整终端原文；深度排错仍可能需要 CI 或客户端日志。
- MAHO does not plan products, orchestrate an agent team, host models, or sandbox untrusted code. / MAHO 不负责产品规划、智能体团队编排、模型托管或不可信代码沙箱。

If your main problem is “help me discover and design the product,” a planning framework may be the better starting point. If the problem is “several agents touch this repository and I need a trustworthy definition of done,” MAHO is designed for that job. / 如果你的主要问题是“帮我发现和设计产品”，规划型框架可能更适合作为起点。如果问题是“多个智能体会修改这个仓库，我需要一个可信的完成标准”，那正是 MAHO 要解决的事情。

## Current Beta / 当前 Beta

Core CLI, zero-overwrite initialization, bilingual surfaces, public-export gates, and package installation are complete for this Beta. Wheel and sdist are installable but are not proven byte-for-byte reproducible across different build environments. MAHO does not claim to be an agent runtime, model router, model-quality upgrade, or security sandbox.

本 Beta 已完成核心 CLI、零覆盖初始化、双语界面、公开导出门禁和包安装。wheel 与 sdist 可以安装，但尚未证明能够跨不同构建环境逐字节复现。MAHO 不宣称自己是智能体运行时、模型路由器、模型质量增强工具或安全沙箱。

Read the full [English guide](README.en.md), [中文指南](README.zh-CN.md), or the documentation index below. / 继续阅读完整[英文指南](README.en.md)、[中文指南](README.zh-CN.md)或下面的文档索引。

## Documentation / 文档

- [Quick start](docs/en/QUICKSTART.md) / [快速开始](docs/zh-CN/QUICKSTART.md)
- [Architecture](docs/en/ARCHITECTURE.md) / [架构](docs/zh-CN/ARCHITECTURE.md)
- [CLI behavior](docs/en/CLI.md) / [CLI 行为](docs/zh-CN/CLI.md)
- [Compatibility matrix](docs/en/COMPATIBILITY.md) / [兼容矩阵](docs/zh-CN/COMPATIBILITY.md)
- [Uninstall](docs/en/UNINSTALL.md) / [卸载](docs/zh-CN/UNINSTALL.md)
- [Security policy](SECURITY.md) / [安全策略](SECURITY.zh-CN.md)
- [Contributing](CONTRIBUTING.md) / [贡献指南](CONTRIBUTING.zh-CN.md)

---

Apache-2.0 licensed code and documentation. MAHO project marks are stewarded by **Future Apparatus Laboratory**. / 代码与文档采用 Apache-2.0；MAHO 项目标识由**未来装置实验室（Future Apparatus Laboratory）**维护。
