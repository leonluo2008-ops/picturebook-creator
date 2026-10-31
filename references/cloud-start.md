# 云端启动与接续

## 环境配置

- GitHub 仓库：leonluo2008-ops/picturebook-creator。
- 分支：codex/picturebook-adaptation；现有云环境若仍为 PC1024-3，需切换并重新发布。
- 运行时：Python 3.10+。创作检查与 Notion 脚本仅需标准库。
- 凭据：在云环境的密钥管理中配置 NOTION_API_KEY；不写入仓库、聊天或安装脚本。允许访问 api.notion.com；下载资产时按真实来源追加必要域名。
- 启动检查：`python tools/cloud_check.py`；只读联通检查：`python tools/cloud_check.py --notion-word soap`。
- 启动指令：读取 AGENTS.md、SKILL.md 对应章节与 SOUL.md，读取 projects/ 对应进度，再继续用户已确认的阶段。不要自动跳过确认。

## 跨设备资料

GitHub 保存规则、脚本、文字稿与用户确认进度；Notion 保存题材、归档稿和交付附件。每次用户确认后同步 progress.md，注明下一步和未确认事项，不把建议冒充定稿。
新作品使用相对路径 `绘本创作/作品/<排产号>/`，不依赖本机 E 盘。需要跨设备保存的文字须明确提交；大图、ZIP 和凭据不提交到 Git。

## 能力边界与验收

先验只读 Notion 精确定位、语法检查，再测试用户授权的归档。标准交付当前仍引用本机 series-image-agent，实现未随本仓迁入，因此云端压缩上传尚未验收，不宣称全流程上线。
浏览器生图仍在本地运行。云端提供已确认提示词及资产指引，本地验图后按 standard-delivery.md 完成交付，再把结果写回进度。
