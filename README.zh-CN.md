<p align="center">
  <img src="https://raw.githubusercontent.com/Do-fei/maho-harness/main/assets/brand/maho-readme-banner.png" alt="MAHO — Model-Agnostic Harness for Outcomes。先证明，再完成。" width="100%">
</p>

<p align="center">
  <strong>面向编程智能体的证据优先工程治理。</strong><br>
  先检查，保留已有规范；用证据验证，由独立角色验收。
</p>

<p align="center">
  <a href="README.en.md">English</a> · <a href="README.md">语言入口</a>
</p>

> **发布** — `0.1.0-beta.1` 是 MAHO 的首个公开 Beta。签名产物以 GitHub Releases 为准；只有 PyPI 项目页列出本版本时，才视为 PyPI 可用。详见[哪些已经完成，哪些尚未完成](#哪些已经完成哪些尚未完成)。

MAHO 是一个无运行时依赖的工程治理层，为编程智能体提供共享工程合同、安全仓库接入、可执行验证、有边界证据和独立验收语义。

它不是智能体运行时、模型路由器或安全沙箱，也不承诺所有客户端的行为完全一致。

## MAHO 的主要功能

| 共享工程合同 | 安全接入多个智能体 | 可验证的结果 |
|---|---|---|
| 根据仓库事实生成项目宪法与机器可读检查合同。 | 在客户端兼容路径中只安装缺失的规范和 Agent Skills，不覆盖已有文件。 | 运行已接受的直接命令，记录有边界证据，保留失败，并把实现与最终验收分开。 |

在实际工程中，MAHO 帮助编程智能体：

1. **修改前先检查**——发现技术栈、已有规范、验证信号和就绪度缺口。
2. **遵循同一份合同**——让人类与不同智能体共享目标、约束、受保护路径和成功标准。
3. **安全初始化**——先预览全部变化，保留已有文件，只在明确确认后应用。
4. **不用 shell 字符串做验证**——只运行已接受的参数数组，限制超时，并检测受保护路径变化。
5. **保留诚实证据**——明确区分事实、推断、厂商声明以及 `PASS`、`FAIL`、`INCONCLUSIVE`。
6. **独立完成验收**——让实现者与最终完成判断彼此分离。

## 快速开始

### 1. 安装

MAHO 需要 Python 3.10 或更高版本，且没有 Python 运行时依赖。当 [PyPI 项目页](https://pypi.org/project/maho-harness/)列出 `0.1.0b1` 后，可使用：

```bash
pipx install maho-harness
# 或
uv tool install maho-harness
maho --version
```

在此之前，请从 [GitHub Releases](https://github.com/Do-fei/maho-harness/releases) 下载已签名 wheel 与 `SHA256SUMS`，完成校验后安装本地 wheel：

```bash
pipx install ./maho_harness-0.1.0b1-py3-none-any.whl
# 或
uv tool install ./maho_harness-0.1.0b1-py3-none-any.whl
```

### 2. 只读预览，不修改仓库

```bash
maho --locale zh-CN init /path/to/project --agent codex
```

请检查目标仓库、所选客户端、将创建的文件、保留路径以及“已覆盖 0”。

### 3. 应用已经审阅的计划

```bash
maho --locale zh-CN init /path/to/project --agent codex --apply --yes
```

初始化只创建缺失路径。已有项目规范和 Skill 目录会被保留，不会合并或覆盖。

### 4. 检查并验证

```bash
maho discover /path/to/project
maho readiness /path/to/project
maho validate /path/to/project
maho context-audit /path/to/project
```

`discover` 只提出检查建议，不会擅自接受。请审阅 `.harness/project.json`，把认可的条目从 `proposed_checks` 移入 `checks`，并完善生成的项目宪法，再把验证结果视为正式依据。

### 5. 添加更多编程智能体

```bash
maho --locale zh-CN init . --agent claude-code --agent cursor --apply --yes
maho --locale zh-CN init . --agent all --apply --yes
```

`--agent all` 只安装全部七个已验证客户端的适配器。实验性适配器必须按名称显式选择，并会给出明确警告。

自动化场景应显式请求 JSON：

```bash
maho --json --locale zh-CN init /path/to/project --agent codex
```

## 工作方式

```mermaid
flowchart LR
    A[检查仓库] --> B[项目宪法]
    B --> C[客户端 Skill 适配器]
    C --> D[编程智能体工作]
    D --> E[运行已接受检查]
    E --> F[有边界证据账本]
    F --> G[独立验收]
```

通用核心保持技术栈中立。可选 Stack Packs 为 Python、FastAPI、Node.js、React、Next.js 和 Electron 增加工程约定，但不会改变完成语义。

## 哪些已经完成，哪些尚未完成

| 状态 | 范围 |
|---|---|
| **公开 Beta 已完成** | 核心 CLI；零覆盖 `init`；发现、就绪度、验证与上下文审计；双语 CLI/文档；七客户端适配器选择；白名单公开导出；wheel、sdist 与 pipx 安装检查。 |
| **已验证客户端** | Codex、Cursor、Factory/Droid、Claude Code、Kilo Code、Kimi Code 和 OpenCode 均有有边界真实客户端证据及单独独立验收。 |
| **实验性适配器** | Gemini CLI、Roo Code 和 GitHub Copilot 已完成文件系统适配器测试，但 `0.1.0-beta.1` 不包含其真实客户端测试与独立验收。 |
| **发布边界** | 以带签名与校验和的 GitHub Release 产物为准；PyPI 可用性、私密漏洞报告和匿名可见性必须在线验证，不能从本地检出状态推断。 |
| **已知限制** | wheel/sdist 可以安装，但尚未证明能够跨不同构建环境逐字节复现。 |
| **明确不作声明** | 智能体运行时、模型路由、安全沙箱，或所有第三方客户端具备完全一致的语义。 |

仓库侧候选已经通过有边界独立验收：完整测试套件通过，公开导出干净，并完成全新包安装检查。这次验收没有重新播放全部私有客户端 transcript，也不构成对外发布授权。公开[兼容矩阵](docs/zh-CN/COMPATIBILITY.md)保留了支持范围与证据边界。

## 客户端支持

| 发布层级 | 客户端 | 含义 |
|---|---|---|
| **已验证** | Codex、Cursor、Factory/Droid、Claude Code、Kilo Code、Kimi Code、OpenCode | 本次 Beta 已具备文档路径、文件系统适配器、有边界真实客户端测试和单独验收。 |
| **实验性** | Gemini CLI、Roo Code、GitHub Copilot | 适配器行为已经测试；真实客户端行为和验收不属于本版本支持合同。 |

详细[兼容矩阵](docs/zh-CN/COMPATIBILITY.md)会分别记录客户端版本、Skill 路径、证据边界和验收阶段。

## 核心命令

| 命令 | 用途 |
|---|---|
| `maho init` | 预览或安装 MAHO 规范与 Skills，不覆盖已有路径。 |
| `maho discover` | 检查仓库技术栈并提出验证建议。 |
| `maho readiness` | 审计仓库是否已经具备可靠的智能体工作条件。 |
| `maho validate` | 运行已接受检查并记录有边界证据。 |
| `maho context-audit` | 检查常驻规范是否超出上下文预算。 |
| `maho bootstrap` | 向后兼容的机器型初始化命令。 |

## 文档

- [快速开始](docs/zh-CN/QUICKSTART.md)
- [架构](docs/zh-CN/ARCHITECTURE.md)
- [CLI 行为](docs/zh-CN/CLI.md)
- [兼容矩阵](docs/zh-CN/COMPATIBILITY.md)
- [项目合同 Schema](schemas/project.schema.json)
- [公开发布流程](docs/zh-CN/RELEASING.md)
- [卸载](docs/zh-CN/UNINSTALL.md)
- [安全策略](SECURITY.zh-CN.md)
- [贡献指南](CONTRIBUTING.zh-CN.md)

## 许可证与项目标识

代码和文档使用 [Apache License 2.0](LICENSE)，中文参考见 [`LICENSE.zh-CN.md`](LICENSE.zh-CN.md)。MAHO 名称与帆船项目标记另由 [`TRADEMARKS.zh-CN.md`](TRADEMARKS.zh-CN.md) 说明。

著作权署名为 MAHO contributors。**未来装置实验室（Future Apparatus Laboratory）**维护项目身份与标识。公开源码仓库为 [`Do-fei/maho-harness`](https://github.com/Do-fei/maho-harness)。
