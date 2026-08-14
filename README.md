<p align="center">
  <img src="https://raw.githubusercontent.com/Do-fei/maho-harness/main/assets/brand/maho-readme-banner.png" alt="MAHO — Model-Agnostic Harness for Outcomes. Proof before done." width="100%">
</p>

<p align="center">
  <strong>Evidence-first engineering governance for coding agents.</strong><br>
  <strong>面向编程智能体的证据优先工程治理。</strong>
</p>

<p align="center">
  <a href="README.en.md">English</a> · <a href="README.zh-CN.md">简体中文</a>
</p>

> **Release / 发布** — `0.1.0-beta.1` is MAHO's first public Beta. GitHub Releases is the authority for signed artifacts; treat PyPI as available only when its project page lists this version. / `0.1.0-beta.1` 是 MAHO 的首个公开 Beta。签名产物以 GitHub Releases 为准；只有 PyPI 项目页列出本版本时，才视为 PyPI 可用。

## What MAHO gives you / MAHO 提供什么

| Shared contract / 共享合同 | Safe setup / 安全接入 | Verifiable outcomes / 可验证结果 |
|---|---|---|
| A Project Constitution and machine-readable checks keep humans and agents aligned. / 项目宪法与机器可读检查让人类和智能体遵循同一约定。 | Preview-first installation adds only missing guidance and Skills; existing paths are preserved. / 先预览、后安装，只补齐缺失规范和 Skills，保留已有路径。 | Accepted checks, bounded evidence, preserved failures, and independent acceptance replace unsupported completion claims. / 用已接受检查、有边界证据、保留失败和独立验收替代无依据的“已完成”。 |

MAHO is a governance layer—not an agent runtime, model router, or security sandbox. / MAHO 是工程治理层，不是智能体运行时、模型路由器或安全沙箱。

## Start safely / 安全开始

Requires Python 3.10 or later. Install from PyPI only after its project page lists `0.1.0b1`; otherwise install the downloaded GitHub Release wheel. / 需要 Python 3.10 或更高版本。只有 PyPI 项目页列出 `0.1.0b1` 后才从 PyPI 安装；否则请安装从 GitHub Release 下载的 wheel。

```bash
pipx install maho-harness
# or / 或
pipx install ./maho_harness-0.1.0b1-py3-none-any.whl

# Read-only preview / 只读预览
maho --locale zh-CN init /path/to/project --agent codex

# Apply the reviewed plan; existing files are never overwritten
# 应用已审阅计划；不会覆盖已有文件
maho --locale zh-CN init /path/to/project --agent codex --apply --yes

# Inspect, then run accepted checks / 检查仓库，再运行已接受检查
maho discover /path/to/project
maho readiness /path/to/project
maho validate /path/to/project
```

Selecting `--agent all` installs adapters for all seven verified clients. / 使用 `--agent all` 会安装全部七个已验证客户端的适配器。

<details>
<summary><strong>Machine-readable project contract / 机器可读项目合同</strong></summary>

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

## Done and not done / 已完成与未完成

| State / 状态 | Scope / 范围 |
|---|---|
| **Verified / 已验证** | Core CLI, zero-overwrite initialization, bilingual surfaces, public-export gates, package installation, and bounded real-client plus independent acceptance for Codex, Cursor, Factory/Droid, Claude Code, Kilo Code, Kimi Code, and OpenCode. / 核心 CLI、零覆盖初始化、双语界面、公开导出门禁、包安装，以及七个客户端的有边界真实测试和独立验收。 |
| **Experimental / 实验性** | Gemini CLI, Roo Code, and GitHub Copilot have tested filesystem adapters only; real-client and independent acceptance are outside this Beta. / 三者仅完成文件系统适配器测试，真实客户端与独立验收不属于本次 Beta。 |
| **Release boundary / 发布边界** | Signed and checksummed GitHub Release artifacts are canonical. PyPI availability, private vulnerability reporting, and anonymous visibility are verified live rather than inferred from this checkout. / 以带签名与校验和的 GitHub Release 产物为准；PyPI 可用性、私密漏洞报告和匿名可见性必须在线验证，不能从本地检出状态推断。 |
| **Not claimed / 不作声明** | Byte-for-byte reproducible artifacts, identical behavior across clients, or protection equivalent to a security sandbox. / 产物逐字节复现、所有客户端行为完全一致，或等同安全沙箱的保护能力。 |

See the detailed [English README](README.en.md), [中文 README](README.zh-CN.md), and compatibility matrices ([EN](docs/en/COMPATIBILITY.md) · [中文](docs/zh-CN/COMPATIBILITY.md)).

---

Apache-2.0 licensed code and documentation. MAHO project marks are stewarded by **Future Apparatus Laboratory**. / 代码与文档采用 Apache-2.0；MAHO 项目标识由**未来装置实验室**维护。
