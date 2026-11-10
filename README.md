# picturebook-creator

当前版本：**v11.1.9**

用于 Hermes 的双语儿童绘本创作 Skill。支持故事绘本、整词领读绘本、Notion 排产台账和成图交付。

## 安装与触发

在用于验证的 Hermes 环境中，把本仓验证分支的检出放入该环境的 Skills 目录，例如 $HERMES_HOME/skills/creative/picturebook-creator。该目录包含 SKILL.md 及配套文件。
在终端用 hermes skills list --source local 核对名称，或在新对话中用 /picturebook-creator 显式调用。
自然语言触发包括「画一个小兔子冒险的绘本」「做一本教孩子认读某个单词的领读绘本」「检查绘本台账」。

## 工作流程

- **故事绘本**：确认主题与角色 → 标题及简介 → 双语旁白 → 角色参考与整本生图提示词。
- **领读绘本**：确认词义、年龄和画风 → 页面结构 → 双语文案 → 整本生图提示词 → Notion 归档。封面后进入具体语境，完整词随场景自然出现，旁白随画面变化。单色或多彩装饰以可读性为准。
- **台账**：在当前 Hermes 环境配置 NOTION_API_KEY，确保 Notion 集成可访问台账。python3 scripts/notion_archive.py --word WORD --locate 只读定位，scripts/notion_verify.py 独立回读。先在 Skill 根目录运行脚本的 --help 查看参数。
- **成图交付**：验收完成后按 [标准交付](references/standard-delivery.md) 打包、回传并回读。外部图像与交付工具从当前环境选择。

完整规则见 [SKILL.md](SKILL.md)。辅助资料包括 [封面设计](references/cover-design.md)、[风格库](references/style-library.md) 和 [台账操作](references/notion-ledger-ops.md)。
