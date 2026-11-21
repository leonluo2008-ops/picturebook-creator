# 云端启动与接续

## 环境配置

- GitHub 仓库：leonluo2008-ops/picturebook-creator。仓只一个，资料与工具全部在仓内维护〔裁定 R11〕。
- 分支：**`dev`**（当前开发；`main` 为稳定线，当前版本 `14.0.0`）。旧分支 `codex/picturebook-adaptation` 已冻结；现有云环境若仍为 `PC1024-3` 或旧 codex 分支，**需切换并重新发布**。
- 运行时：Python 3.10+。创作检查与 Notion 脚本仅需标准库。
- 凭据：在云环境的密钥管理中配置 `NOTION_API_KEY`；不写入仓库、聊天或安装脚本。允许访问 api.notion.com；下载资产时按真实来源追加必要域名。**用 `mcp__notion__*` 时不需要该变量**——它只服务于脚本兜底路径。
- 启动检查：`python tools/cloud_check.py`；只读联通检查：`python tools/cloud_check.py --notion-word soap`。
- 启动指令：读取 `AGENTS.md`、`SKILL.md` 对应章节与 `SOUL.md`，读取 `projects/` 对应进度，再继续用户已确认的阶段。不要自动跳过确认。

## 跨设备资料

GitHub 保存规则、脚本、文字稿与用户确认进度；Notion 保存题材、归档稿和交付附件。每次用户确认后同步 `progress.md`，注明下一步和未确认事项，不把建议冒充定稿。
新作品使用相对路径 `绘本创作/作品/<排产号>/`，不依赖本机 E 盘。需要跨设备保存的文字须明确提交；大图、ZIP 和凭据不提交到 Git。

## 能力边界与验收

先验只读 Notion 精确定位、语法检查，再测试用户授权的归档。标准交付当前仍引用本机 series-image-agent，实现未随本仓迁入，因此云端压缩上传尚未验收，不宣称全流程上线。
浏览器生图仍在本地运行。云端提供已确认提示词及资产指引，本地验图后按 `standard-delivery.md` 完成交付，再把结果写回进度。

## 仓与版本维护（改 SKILL.md / references 之前读）

- **只在 live 检出上改**，不写 `.backup-*`、`.curator_backups` 等旁路副本——旁路副本 live 加载不到、git 历史也没有它，事后排查还会被它误导成「已装填」。改前 `pwd` 确认目录，改后 `git status` 确认变更落在 tracked 文件上。
- **动手前三条一起跑**：`git fetch origin <分支>`、`git status --porcelain`（有不是自己写的未提交改动就停，那是另一个会话正在写）、`git log --oneline -3`。语义级覆盖不产生冲突标记，git 全程不报警，只能靠这三条自己发现。
- **同级目录不要留同名副本**：`picturebook-creator.backup-*` / `.rollback-broken` 与 live 同名同级时，加载会报歧义拒载（只剩空 `.git` 的残壳同样删掉）。
- **版本号三处同档**：frontmatter `version`、`README.md`「当前版本」、`CHANGELOG.md` 顶部条目一起更新——只改 frontmatter 不动 README/CHANGELOG，下一轮体检就得补账。
- **版本对齐后再打 tag，tag 必须指向 release 提交**：三处同档 → 提交 → `git tag -a vX.Y.Z -m '…'` → `git push origin <分支> && git push origin vX.Y.Z` → `git ls-remote --tags origin vX.Y.Z` 回读确认。tag 先于版本对齐建了就用 `git tag -f -a` 重指，并断言 `git rev-parse vX.Y.Z^{}` 与 `HEAD` 相等。
- **回滚到某个好版本**：先 `git tag <备份名> HEAD` 保命，把不属于自己的未提交改动存成 patch，再 `git revert --no-commit <好版本>..HEAD` 一次撤销整段——比 `reset --hard` 安全，不改写历史。回滚后 `git diff <好版本>` 为空才算真回到那个版本。
- **怀疑某条规则「到底装没装进 live」时**：`git log -S '<规则关键词>' --all` 查提交历史；空输出＝从未进过 live 仓。备份/旁路副本里长得一样的文字不构成「已装填」证据。
- **SKILL.md 正文与 README 不写变更历史条目**——skill 内只保留唯一当前有效的规则，变更历史由 git 历史承载。
- **规则写「规则 + 判据」，不写事故叙事与具体绘本案例**；同一坑第二次出现时合并进既有条目，不新增第二条。
- **修正偏差先分层**：先查文件里是否已有对应规则（执行层错误＝规则在但没照做，此时改规则是堆砌）；确认规则缺失才补，且用「正面原则 + 一两个示例」的形状写——skill 靠示例引导模型，不靠禁令清单堆约束。修正落库后全文搜索一遍，确认新条目没有和既有条目重复。
- **想到了但没验证过的改动，先写备忘、不直接提交**：写清目标文件与函数、现状、症状、提案、为何先不提交、验证方式；验证有效后才改仓、升 patch 版本。
- **内容修正 ≠ 本文件维护**：用户指着台账某一行动笔时，只改那一行与其对应页的 L4，不顺手改规则、示例、版本号或 README/CHANGELOG——规则修补是独立任务，要用户明确要求才做。
- 出网拉取/推送需挂代理（127.0.0.1:7897）。
