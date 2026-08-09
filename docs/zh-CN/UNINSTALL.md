# 卸载

English: [`../en/UNINSTALL.md`](../en/UNINSTALL.md)

## 移除 CLI

使用原安装工具卸载 MAHO：

```bash
pipx uninstall maho-harness
# 或
uv tool uninstall maho-harness
# 或
python3 -m pip uninstall maho-harness
```

## 移除项目文件

MAHO 不提供递归删除项目文件的命令。请先审阅 Git 状态，只删除已经确认属于 MAHO 的路径。

常见生成路径：

```text
.harness/
.agents/skills/<maho-skill>/
.factory/skills/<maho-skill>/
.claude/skills/<maho-skill>/
.roo/skills/<maho-skill>/
```

不要整体删除共享 Skill 目录，其中可能包含被 MAHO 保留的用户文件。如果 `AGENTS.md` 是由 MAHO 创建的，也要审阅后再删除；MAHO 从不声称拥有预先存在的 `AGENTS.md`。

如果安装变更已经提交，优先使用版本控制正常回退该安装提交，这样最容易审阅和恢复。
