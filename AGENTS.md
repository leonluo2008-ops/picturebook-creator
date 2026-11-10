# Codex 绘本独立工作区

工作分支：codex/picturebook-adaptation。
创作读取本目录 SKILL.md 对应章节及 SOUL.md，不加载 Hermes 全局 skill、配置或记忆。
本目录是独立 Git 仓库，不使用 Hermes 检出、符号链接或共享 worktree。
上游规则中的 Hermes 路径、代理、live 检出维护和全局记忆不在本副本执行。内容规范与逐步确认规则继续有效；Codex 直接承担绘本角色。
修改只保存在 Codex 分支；不自动推送、合并或更新 Hermes。不修改全局 Git、Python 配置；额外依赖用项目 .venv。
用户已授权 Notion 联动及只读复用 Hermes 凭据。凭据来源为 C:\Users\leon3\AppData\Local\hermes\.env；仅在脚本进程内加载，不打印、复制、提交或修改。沙箱 LOCALAPPDATA 被重定向，运行时可仅为子进程指定真实 LOCALAPPDATA。创作确认后按 SKILL.md 执行归档，检查凭据本身不授权修改 Notion 数据。
新作品保存到项目绘本创作/作品/下的新目录，不覆盖旧作品。
成图验收后自动执行 references/standard-delivery.md：JPEG转换压缩、页序命名、ZIP打包、上传Notion「交付文件」、更新「已生图」并独立回读；不另等打包上传指令。用户当次暂停或仅预览要求优先。

来源：https://github.com/leonluo2008-ops/picturebook-creator
来源分支：PC1024-3；来源提交：5f2f49a8c22b2a5aefe216cd1813f1ad4f9dda10；skill 版本：11.1.7。
通过 GitHub 连接器导入文件快照，upstream-snapshot 是本地导入基线，不含上游 Git 历史。后续更新通过差异比较合入 Codex 分支，不将该基线当作上游历史直接合并。


## 云端与跨设备入口

云端先读 `references/cloud-start.md`，执行 `python tools/cloud_check.py`。云端使用环境提供的 NOTION_API_KEY，不读取本机 Hermes 凭据；不依赖 Windows 绝对路径、OneDrive 或本机代理。当前工作分支为 codex/picturebook-adaptation。
接续已有书先读 `projects/<排产号>/progress.md`，区分用户确认与草稿。每次确认后更新进度；创作文稿按排产号保存，敏感凭据与大图不入 Git。用户允许当前工作分支推送；不合并其他分支。
云端承担创作、审稿、提示词和 Notion 归档。浏览器生图与本机专有工具仍交给本地执行；未验证的云端交付能力不能宣称可用。发布云环境后以只读 Notion 查询验证连通，再执行已获确认的写入。
