# picturebook-creator（DSH 侧 skill 仓）

> 本仓只装 **DSH 侧 `picturebook-creator` skill** 及其成书产物。上级目录 `E:\User\DSH-Project\picturebook` 是 DSH 收纳根（非本仓的一部分）：整理/归置类规则见根 `AGENTS.md` 与 `docs/项目适配包.md`；本文件只管本仓自身。任何会话先确认 cwd 是本仓而不是根目录，再按本文件行事。

工作分支：**`dsh/v14-prod`**（本机 DSH 实际工作线，当前版本 `14.0.0`）；**`main`** 为稳定线；`codex/picturebook-adaptation` 为 v11 基线、**已冻结**。V15 属 Codex 工作区分支，本线不跟随、不合并。
本检出位于 `E:\User\DSH-Project\picturebook\picturebook-creator`，经 **junction** 链接为 `~/.dsh/skills/picturebook-creator`（DSH 读取层）。
创作读取本目录 SKILL.md 对应章节及 SOUL.md；内容规范与逐步确认规则继续有效，生图由 DSH 承担。
修改只保存在 `dsh/v14-prod` 分支；**不自动推送、合并**（推送/并回需所有者点头）。不修改全局 Git、Python 配置。
用户已授权 Notion 联动及只读复用 Hermes 凭据。凭据来源为 C:\Users\leon3\AppData\Local\hermes\.env；仅在脚本进程内加载，不打印、复制、提交或修改。检查凭据本身不授权修改 Notion 数据。
新作品保存到**本仓内** `绘本创作/作品/` 下的新目录，不覆盖旧作品。（注意：根目录下另有一个 `绘本创作/作品/`，归属待所有者裁定，勿混用。）

## 生图路径（可选之一，非唯一）

本机产线（series-image-agent）只是生图的**可选路径之一，不写死**：提示词同样可直接交给即梦等外部生图工具，按当次情况与所有者意见选路。
代码仓：`E:\User\GitHub\series-image-agent`。分支以仓库实况为准——当前检出 `feature/scene-platform`（2026-11-24 初建，场景契约化平台）；v14 适配线为 `feature/adapt-picturebook-v14`；动分支前先问所有者哪条是当前产线。
本机链路：`parse_prompts.py`（L4→book yaml，refs.json 绑定）→ `batch.py`（ComfyUI 出图）→ `eagle_export.py`（按页导出）→ Eagle 入库 → 台账推「已生图」。
参考图纪律：**只喂单视角**——横图三视角先用 `scripts/split_single_view.py` 切中份（`refs-single/`），比例尺图不入模型；比例用提示词文字写死。
图像生成任务须逐次取得所有者授权；台账/Eagle 入库等写入动作同样先报后做。

## 交付（2026-11-26 更新）

- **Notion 是创作产物的正式存档、审阅和修订载体**：创作或修改完成后默认按正式流程回写 Notion（归档/`--rewrite` 整本重写+保留原备注追加摘要+独立回读）；用户当次要求仅预览/暂缓时按当次执行。收尾在对话框给 Notion 链接+改动摘要+验证结果。细则：`references/notion-ops.md`（§2/§3/§6/§8），口径记录 `docs/项目适配包.md` §1.5。
- **本地产物生命周期**：`projects/<排产号>/` 是可弃工作副本（Notion 才是存档）；回读一致且后续步骤无需即清理，批量对账后清理已完成项——细则 `references/notion-ops.md` §8。
- 成图验收后：`eagle_export.py` 导出 → Eagle `儿童绘本/<排产号> <word>-成图` 文件夹（命名 0=封面，1..N=内页）→ `notion_archive.py --status 已生图` + `notion_verify.py` 独立回读。
**不走 ZIP 打包、不上传 Notion「交付文件」**（`deliver_book.py` 已废弃，勿用）。用户当次暂停或仅预览要求优先。

## 云端与跨设备入口

云端先读 `references/cloud-start.md`，执行 `python tools/cloud_check.py`。云端使用环境提供的 NOTION_API_KEY，不读取本机凭据；不依赖 Windows 绝对路径、OneDrive 或本机代理。
接续已有书先读 `projects/<排产号>/progress.md`，区分用户确认与草稿。每次确认后更新进度；创作文稿按排产号保存，敏感凭据与大图不入 Git。
浏览器生图与本机专有工具仍交给本地执行；未验证的云端交付能力不能宣称可用。

来源：https://github.com/leonluo2008-ops/picturebook-creator；导入基线版本：11.1.7；**当前版本：14.0.0**。
