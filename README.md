# picturebook-creator

标准儿童双语绘本 skill。运行入口是 [SKILL.md](SKILL.md)，规则版本在 YAML `metadata.version`。创作流程不依赖 AGENTS.md、SOUL.md、某个工作站或其他 Agent。

## 安装内容

将 `SKILL.md`、`references/`、`scripts/` 一起放入宿主可发现的 `picturebook-creator/` 技能目录。不要只复制入口而遗漏引用。替换时安装当前完整文件集，避免混入旧同名文件。测试报告和仓库管理文档不属于运行规则。

Hermes 可使用其当前 profile 的技能目录。安装位置以宿主配置为准；本仓库不会自动修改生产 profile。启用后直接要求“使用 picturebook-creator 制作绘本”进行首次检查，确认读取的是本目录入口，再按正常自然语言使用。

纯创作无需 Notion 凭据。台账操作使用已连接的 Notion 工具，或为执行脚本的进程提供 `NOTION_API_KEY` 与实际数据源 ID。图片生成由宿主可用工具承担。

## 制作安装包

`python validation/build_package.py --out outputs/picturebook-creator.zip`

ZIP 仅包含运行入口、参考资料和必要脚本，输出同目录 SHA-256 清单。无需把测试稿件或原始聊天导出安装为技能。

## 验证

- 实际结果及稿件：[validation/RESULTS.md](validation/RESULTS.md)
- 原子任务与进度：[validation/WORKPLAN.md](validation/WORKPLAN.md)
- 用户规范及验收点：[validation/requirements.md](validation/requirements.md)
- 离线工具测试：`python validation/test_tools.py`
- 行为场景：[validation/cases.json](validation/cases.json)

实际测试结果以本次结果报告为准。文件能被发现、结构检查通过、Agent 写出合格文本、生成模型画对、生产台账写入成功是不同证据，不互相替代。
