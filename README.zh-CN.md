<p align="center">
  <img src="https://raw.githubusercontent.com/Do-fei/maho-harness/main/assets/brand/maho-readme-banner.png" alt="MAHO — Model-Agnostic Harness for Outcomes。先证明，再完成。" width="100%">
</p>

<p align="center">
  <strong>面向编程智能体的证据优先工程治理。</strong><br>
  让编程智能体真正读懂项目，也让它说“完成”时拿得出证据。<br>
  为 Codex、Cursor、Claude Code、Kimi Code、OpenCode、Kilo Code 与 Factory/Droid 提供同一套工程闭环。
</p>

<p align="center">
  <a href="README.en.md">English</a> · <a href="README.md">双语概览</a>
</p>

> **发布** — `0.1.0-beta.1` 是 MAHO 的首个公开 Beta：源码标签带签名，[GitHub Release](https://github.com/Do-fei/maho-harness/releases/tag/v0.1.0-beta.1) 中的 wheel 带校验和；PyPI 尚未发布。

## 写出代码，不等于完成软件

编程智能体很擅长快速产出修改。真正困难的部分，往往发生在代码周围：

- 这个仓库到底有哪些规范必须遵守？
- 哪些文件不能碰？
- 哪一组测试、类型检查、构建或运行探针，才能证明任务真的完成？
- 检查超时或环境跑不起来时，应该判失败，还是证据不足？
- 换一个智能体之后，能不能不重读漫长对话就理解上一轮发生了什么？
- 写代码的智能体，是否应该同时负责宣布自己的工作合格？

多数智能体工具把这些问题留给提示词。每次会话都临时重建一遍流程，最后的“完成”有时只代表智能体停止工作了。

**MAHO 把松散的对话变成一套工程闭环。** 它把项目规范、已确认检查、客户端 Skills、安全边界和完成证据留在仓库中，让人和不同的编程智能体都能使用同一套依据。

它不替代你的编程智能体，而是给智能体一个更适合认真工作的项目。

## 使用 MAHO 之后，什么会发生变化

| 以前 | 使用 MAHO 之后 |
|---|---|
| 每个智能体都要猜这个项目该怎么做。 | 所有受支持客户端读取同一份项目宪法和工程 Skills。 |
| 接入脚本可能合并或覆盖已有规范。 | 初始化默认只读预览，应用时只创建缺失路径。 |
| 智能体挑一个方便的测试就开始跑。 | MAHO 根据仓库事实提出检查，由维护者决定哪些检查才算数。 |
| 一条绿色命令被当成整个任务的证明。 | 必需检查、受保护路径、超时和证据状态共同定义结果究竟证明了什么。 |
| 失败尝试被最后一次成功盖住。 | `FAIL` 与 `INCONCLUSIVE` 会继续留在记录里。 |
| 实现者写代码，也给自己判分。 | 新的智能体或人类审查者可以独立验收精确候选。 |

## 这套工程闭环是怎样工作的

### 1. 修改前，先看懂仓库

`maho discover` 从有边界的仓库信号中识别已有规范、清单文件、技术栈标记、测试配置和候选验证命令。它只提出建议，不会把一次猜测偷偷变成项目政策。

随后，`maho readiness` 会指出可靠开展智能体工作之前还缺什么，例如项目宪法尚未完善，或候选检查还没有得到确认。

### 2. 把项目约定写清楚

MAHO 会创建两份彼此配合的文件：

- `.harness/PROJECT_CONSTITUTION.md` 用人和智能体都能读懂的文字，说明项目目标、约束、权限、受保护范围和完成标准。
- `.harness/project.json` 用机器可读形式记录已接受检查、候选检查、受保护与生成路径、运行探针和 Stack Packs。

自动生成的内容只是起点，不能代替维护者判断。哪些候选检查应该成为正式检查，最终由人确认。

### 3. 让不同客户端使用同一套工程方法

MAHO 维护一份规范的工程 Skills，再把它映射到不同客户端的发现路径。Codex、Cursor、Claude Code 和 Factory/Droid 的读取方式可以不同，但背后的规则不会分裂成七套各自演化的副本。

内置 Skills 覆盖：

- 发现 MAHO 并读取项目宪法；
- 实现前定义验收合同；
- 记录架构决策；
- 收集完成证据，同时避免夸大结论；
- 把精确候选交给独立审查者；
- 保留失败尝试并形成复盘。

### 4. 接入时不伤害已有项目

除非显式提供 `--apply`，否则 `maho init` 只做预览。预览会列出所有准备创建和保留的路径。应用模式也只创建缺失文件；已经存在的文件或 Skill 目录不会被合并或覆盖。

验证时，MAHO 使用直接参数数组运行已接受命令，而不是拼接 shell 字符串；同时限制执行时间，并为受保护路径创建有边界快照。如果安全或资源限制导致结果不再可信，流程会失败关闭，而不是悄悄降低检查标准。

### 5. 用回执替代“相信我”

`maho validate` 会在明确的资源边界内记录检查状态、退出状态、耗时、输出字节数和受保护路径哈希。它使用三种结果：

- `PASS`——已接受证据足以支持结论；
- `FAIL`——检查结果或受保护状态否定了结论；
- `INCONCLUSIVE`——没有取得作出判断所需的证据。

这个区别很重要。环境损坏不等于测试通过，但它也不总能证明代码一定有错。MAHO 会把这种不确定性原样保留下来。

### 6. 把实现和验收分开

对重要任务，最终审查者应该是全新的：由另一个智能体或人类拿到精确候选、验收合同和证据后独立判断。实现者可以修复失败，但不能给早先的失败改名，也不能悄悄降低验收标准。

这就是 **“先证明，再完成”**。

## 一个具体例子

假设你让编程智能体修改一个现有 Node.js 应用的登录流程。

没有工程框架时，智能体可能找到一个 package 文件，改完登录逻辑，跑一项附近的单元测试，然后宣布完成。它可能根本没有注意仓库里的 `AGENTS.md`、必须执行的类型检查、另一个 package 中的集成测试，或者不能修改的锁文件。

使用 MAHO 后：

1. 发现阶段先找到已有规范和相关技术栈信号；
2. 项目宪法写明任务、约束、受保护路径和预期结果；
3. 维护者确认真正算数的检查，例如单元测试、类型检查和有边界运行探针；
4. 无论使用哪个客户端，编程智能体都遵循同一套验收合同与完成证据 Skills；
5. 验证阶段运行已接受检查，并确认受保护路径没有被破坏；
6. 新的审查者根据合同和证据，判断这个精确候选是否合格。

MAHO 没有替你编写登录功能。它让“提出需求”到“接受修改”之间的过程变得可见、可重复。

## 为什么选择 MAHO

### 更换智能体，不必重建工程流程

项目约定留在仓库里，不属于某个厂商账号，也不困在一段聊天记录中。团队可以在受支持客户端之间切换，同时保留同一份完成标准。

### 引入治理，但不交出仓库

MAHO 本地运行，且没有 Python 运行时依赖。它不要求托管式 MAHO 服务、服务账号或模型 API Key。生成的合同、Skills 和证据都是普通文件，可以查看、纳入版本管理，也可以卸载。

### 可以安全接入真正的已有项目

默认行为是预览，已有路径会被保留。安装结果会明确告诉你准备创建什么、保留了什么，以及覆盖文件数量为零。

### 对话结束后，证据还在

下一位维护者或智能体不必相信一段对话摘要。它可以检查同一份项目合同、精确候选和验证回执；证据不足时，也可以得出不同结论。

### 让失败真正有用

MAHO 不追求一墙绿色徽章。它保留 `FAIL`，把缺少证据标为 `INCONCLUSIVE`，并写清 `PASS` 的适用范围。这样，失败会成为下一步行动的依据，而不是需要隐藏的尴尬记录。

## 同类方案，以及 MAHO 处在什么位置

MAHO 不是第一个尝试给 AI 辅助开发建立秩序的项目。与它最接近的方案，解决的是相邻但并不完全相同的问题。下面的比较基于 2026-08-14 查阅的官方资料。

**[GitHub Spec Kit](https://github.github.com/spec-kit/)** 更深入地解决规格驱动的功能规划。它的默认路径从项目宪法出发，经过功能规格、计划和任务，再进入实现，而且客户端覆盖更广。MAHO 更关注实现周围的事情：怎样安全接入仓库、哪些可执行检查真正算数、关键路径是否完好、证据处于什么状态，以及谁来独立验收。

**[OpenSpec](https://github.com/Fission-AI/OpenSpec)** 是面向新项目和已有项目的迭代式、产物驱动规格与变更系统。它更擅长管理一项变更的规格生命周期。MAHO 关注的是工作周围的工程合同：允许改什么、哪些命令算数、证据究竟证明了什么、谁有权验收。

**[BMAD Method](https://github.com/bmad-code-org/BMAD-METHOD)** 提供更庞大的敏捷开发生命周期，使用专业智能体角色和结构化工作流覆盖分析、规划、架构和实现。MAHO 刻意保持小型。它治理你已经在用的编程智能体，而不是提供一个虚拟组织。

**客户端原生 Rules、Instructions 与 Hooks** 能够在某一个产品内部提供很深的控制能力。它们很有价值，但通常绑定厂商。MAHO 把规范合同和 Skills 留在仓库，再映射到受支持客户端的发现路径。

这些工具不一定是 MAHO 的替代品，也可以和 MAHO 配合。例如，团队可以用 Spec Kit 或 OpenSpec 决定**要做什么**，再用 MAHO 定义**怎样才算完成、哪些检查能够证明、以及如何由新的审查者验收**。

### MAHO 当前的不足

- **项目还很早期。** `0.1.0-beta.1` 的社区规模很小，集成数量也少于已经成熟的规格框架。
- **覆盖范围有限。** 七个客户端只代表记录版本和场景下的验证，并不等于所有编程智能体、操作系统、客户端版本和模型路由；第三方发现行为也可能变化。
- **治理会增加工作量。** 必须有人审阅项目宪法并确认检查。重要修改值得这样做，但对某些一次性小任务来说会显得过重。
- **回执不是完整日志。** MAHO 保存有边界的状态元数据和哈希，不保存完整终端输出。深度排错仍可能需要 CI 日志或客户端原生 transcript。
- **它不是编排器。** MAHO 不负责生成产品战略、管理一组智能体角色、选择模型、运行远程 Worker 或托管仪表盘。
- **它不是安全沙箱。** 直接命令验证和受保护路径快照能够减少含糊，但不能让不可信代码变得可以安全执行。

如果你的主要问题是“帮我发现和设计产品”，规划型框架可能更适合作为起点。如果问题是“多个智能体会修改这个仓库，我需要一个可信的完成标准”，那正是 MAHO 要解决的事情。

## 快速开始

MAHO 需要 Python 3.10 或更高版本，没有 Python 运行时依赖。

### 1. 下载、校验并安装

从 [GitHub Release](https://github.com/Do-fei/maho-harness/releases/tag/v0.1.0-beta.1) 下载 wheel 和 `SHA256SUMS`，然后运行：

```bash
shasum -a 256 -c SHA256SUMS
pipx install ./maho_harness-0.1.0b1-py3-none-any.whl
maho --version
```

也可以使用 `uv tool install` 代替 `pipx install`。当 [PyPI 项目页](https://pypi.org/project/maho-harness/)列出本版本后，才支持直接按包名安装；在此之前以 GitHub Release 为准。

### 2. 只读预览——MAHO 不会写入仓库

```bash
maho --locale zh-CN init /path/to/project --agent codex
```

检查目标路径、所选客户端、准备创建的文件、保留路径和明确的零覆盖结果。

### 3. 应用审阅后的计划

```bash
maho --locale zh-CN init /path/to/project --agent codex --apply --yes
```

### 4. 检查项目并确认验证命令

```bash
maho discover /path/to/project
maho readiness /path/to/project
```

打开 `.harness/PROJECT_CONSTITUTION.md` 和 `.harness/project.json`，补全项目专属决策，只把真正认可的检查从 `proposed_checks` 移入 `checks`。

### 5. 执行验证

```bash
maho validate /path/to/project
maho context-audit /path/to/project
```

### 6. 添加另一个智能体

```bash
maho --locale zh-CN init . --agent cursor --apply --yes
maho --locale zh-CN init . --agent all --apply --yes
```

`--agent all` 只会安装全部七个已验证客户端。实验性适配器必须按名称显式选择，并会显示明确警告。

自动化场景可以添加 `--json`，取得确定性的机器可读输出。

## 当前 Beta 包含什么

| 状态 | 范围 |
|---|---|
| **核心已完成** | 零覆盖初始化；发现；准备度检查；验证；上下文审计；中英双语界面；白名单公开导出；wheel、sdist 与 pipx 安装检查。 |
| **已验证客户端** | Codex、Cursor、Factory/Droid、Claude Code、Kilo Code、Kimi Code 和 OpenCode 已具备文件系统适配器、有边界真实客户端证据和本 Beta 的单独验收。 |
| **实验性适配器** | Gemini CLI、Roo Code 和 GitHub Copilot 已验证适配器行为，但 `0.1.0-beta.1` 不包含真实客户端支持声明或独立验收。 |
| **已知限制** | wheel 与 sdist 可以安装，但尚未证明能够跨不同构建环境逐字节复现。 |
| **不作声明** | 编程智能体运行时、模型路由、提升模型质量、安全沙箱，或所有第三方客户端具备完全一致的语义。 |

[兼容矩阵](docs/zh-CN/COMPATIBILITY.md)记录了这些标签背后的客户端版本、发现路径、证据边界和验收阶段。

## 命令速查

| 命令 | 它回答什么问题 |
|---|---|
| `maho init` | MAHO 准备添加什么，能否在不触碰已有路径的情况下完成？ |
| `maho discover` | 这是怎样的项目，哪些检查可能重要？ |
| `maho readiness` | 要让智能体可靠工作，目前还缺什么？ |
| `maho validate` | 已接受检查是否通过，受保护路径是否保持完好？ |
| `maho context-audit` | 常驻智能体规范是否符合项目的上下文预算？ |
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
