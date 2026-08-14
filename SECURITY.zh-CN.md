# 安全策略

English: [`SECURITY.md`](SECURITY.md)

## 支持版本

只有最新发布的 Beta 或稳定版接收安全修复。`0.1.0-beta.1` 是当前受支持的 Beta 版本线。

## 报告漏洞

未修复漏洞不要提交公开 Issue。请使用 [GitHub 私密漏洞报告](https://github.com/Do-fei/maho-harness/security/advisories/new)。如果该私密通道暂时不可用，绝不能把漏洞细节写入公开 Issue。

报告应包含受影响版本、在 disposable repo 中的最小复现、影响和相关边界条件。不要提交真实凭据或生产隐私数据。

## 安全边界

MAHO 是工程治理工具，不是安全沙箱。它不会绕过或替代宿主智能体的权限、审批、操作系统控制或账户策略。

MAHO：

- 初始化默认使用 dry-run；
- bootstrap 和 Skill 安装拒绝覆盖现有项目文件；
- 拒绝配置为直接执行的 shell 代码和疑似携带秘密的参数；
- 对验证输出做哈希，而不是保存原始标准输出或错误输出；
- 将不可用证据标为 `INCONCLUSIVE`，绝不标为 `PASS`。

项目验证命令仍然属于受信任的项目代码。执行前必须审阅；破坏性兼容测试只能在 disposable repo 中进行。
