# Codex 绘本独立工作区

工作分支：codex/picturebook-adaptation。
创作读取本目录 SKILL.md 对应章节及 SOUL.md，不加载 Hermes 全局 skill、配置或记忆。
本目录是独立 Git 仓库，不使用 Hermes 检出、符号链接或共享 worktree。
上游规则中的 Hermes 路径、代理、live 检出维护和全局记忆不在本副本执行。内容规范与逐步确认规则继续有效；Codex 直接承担绘本角色。
修改只保存在 Codex 分支；不自动推送、合并或更新 Hermes。不修改全局 Git、Python 配置；额外依赖用项目 .venv。
暂不执行 scripts/ 中的 Notion 和资产脚本，它们可能自动读取 Hermes 凭据；须先适配独立配置，dry-run 也不例外。
新作品保存到项目绘本创作/作品/下的新目录，不覆盖旧作品。

来源：https://github.com/leonluo2008-ops/picturebook-creator
来源分支：PC1024-3；来源提交：5f2f49a8c22b2a5aefe216cd1813f1ad4f9dda10；skill 版本：11.1.7。
通过 GitHub 连接器导入文件快照，upstream-snapshot 是本地导入基线，不含上游 Git 历史。后续更新通过差异比较合入 Codex 分支，不将该基线当作上游历史直接合并。
