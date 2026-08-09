# 快速开始

English: [`../en/QUICKSTART.md`](../en/QUICKSTART.md)

## 1. 预览

安装 MAHO 后，可以在任意目录运行：

```bash
maho --locale zh-CN init /path/to/project --agent codex
```

预览是只读的。请确认目标仓库、所选智能体、将创建的文件、保留路径和“已覆盖 0”。

## 2. 零覆盖应用

```bash
maho --locale zh-CN init /path/to/project --agent codex --apply --yes
```

未提供 `--yes` 时，交互终端会要求确认；非交互终端会拒绝未带 `--yes` 的 `--apply`。

## 3. 审阅建议检查

```bash
maho discover /path/to/project
maho readiness /path/to/project
```

发现命令只提出建议，不会自动将其写成已接受检查。请审阅 `.harness/project.json`，把认可的条目从 `proposed_checks` 移入 `checks`，并完善生成的项目宪法。

## 4. 验证

```bash
maho validate /path/to/project
maho context-audit /path/to/project
```

验证不会执行配置中的 shell 代码，只运行直接参数数组、记录有边界的证据，并在受保护路径发生变化时失败。

## 5. 添加客户端

重复使用 `--agent`，或选择全部七个已验证客户端：

```bash
maho --locale zh-CN init . --agent claude-code --agent cursor --apply --yes
maho --locale zh-CN init . --agent all --apply --yes
```

`all` 不包含 Gemini CLI、Roo Code 和 GitHub Copilot，因为它们在 `0.1.0-beta.1` 中属于实验性适配器。只有接受回执中的提示时，才按名称显式选择实验性适配器：

```bash
maho --locale zh-CN init . --agent gemini-cli
```

现有 Skill 目录会被完整保留，不会合并或覆盖。
