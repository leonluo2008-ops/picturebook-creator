# -*- coding: utf-8 -*-
"""V6 · 版本资料：frontmatter 升 13.0.0 + CHANGELOG 追加条目。

用法: python apply_moduleV6.py <SKILL.md> <CHANGELOG.md> [--check]
"""
import io
import sys

FM_OLD = """version: 11.1.8-codex.10
required_environment_variables:
  - NOTION_API_KEY"""

FM_NEW = """version: 13.0.0
# 仅「脚本兜底路径」需要该变量；用 Notion MCP（OAuth，工具 mcp__notion__*）时不需要。
# 若 skill 就绪检查因缺此变量报警，MCP 用户可按「Notion 访问：MCP 优先，脚本兜底」一节忽略。
required_environment_variables:
  - NOTION_API_KEY"""

CL_ANCHOR = "## v11.1.8-codex.10 — 2026-11-10 · 简介收尾与口语验收"

CL_NEW = """## v13.0.0 — 2026-11-21 · 大版本重构（以 29 本语料为证据）

> 基线 `11.1.8-codex.10`（git `9288959`），重构分支 `refactor/v13-20261121`。
> 证据：Notion 近 10 天、状态∈{待生图,已制作} 的 **29 本**（领读 27 本 / 故事 2 本；领读共 243 页），
> 见 `docs/盘点-29本-规则族-20261121.md`。**不使用 128 本全量**（含旧混乱内容）。

**规则冲突收敛**

- 词数上限：8 / 1–10 / 15 三套并存 → 统一为「**领读每页硬上限 10 词、单句建议 ≤8**」（243 页实测最长 10 词、超 10 为 0 页；旧「15 词」系误用故事模式 2 本数据，作废）。
- 块序：原「按顺序」→ **块存在性硬、排列顺序软**（243 页实测：完整块序 133/243、含角色一致性 135/243、含场景一致性 144/243）。
- 页面类型术语：`语境重复页` → **`语境页`**；禁止 `旁白:` / `页面类型:` 行写 `Pn` 前缀（实测 13 本 / 8 页漂移）。
- 故事模式块序编号 `1,2,3,4,6,7,6` → 1–7，并明确「七类」。
- 资产类型 schema 更正为 `角色 / 风格参考`（旧文档写的「场景 / 物件」实际不存在）。

**参考图体系**

- 定妆图：六视角 / 2 行 3 列 → **多视角参考图（默认三视角，可扩姿态表）**；纯浅色背景、不出现文字/标注/边框；模板正文与三处引导语同步。
- L4 一致性：有定妆图 → `角色一致性: 严格以图像1为准（关键特征：…2–4 项）`，不重复长外观；无图 → 每页必写外观。
- 领读模式补【参考图约定】模板，与故事模式同口径。

**台账与改写**

- 状态机：8 个状态的语义与流转表；**仅两处允许 agent 自动推进**（归档→`待生图`、交付回读→`已生图`）。
- 新增「改写模式（审核退回）」：意见归层表 + 三道门 + 改完仍留 `修改中`。
- `已制作` ≠ 已交付（台账全库 128 本中 120 本无交付文件）。

**Notion 访问**

- MCP 优先（OAuth，`mcp__notion__*`）、`scripts/notion_*.py` 兜底；query 必须走 data_source URL；禁止靠视图取数（Default view 自带筛选）。
- 写入边界：读可直接，写需所有者明确同意。

**门禁与死链**

- 新增 `scripts/l4_presence_check.py`：补 `l4_case_check` 只校形态、不校存在的缺口（核心词传错也 EXIT=0）；词族拓展页豁免；实测 27 领读本 27/27 过、错词 EXIT=1。
- 清除死链 `scripts/audit_ledger.py`；复核真实死链 0 条。

**回滚点**

- 规则回滚：`git checkout 9288959 -- SKILL.md`。
- 回滚规则时须同步回滚 `docs/项目适配包.md` 与 `docs/开发计划书.md` 的口径与状态（本次改动跨文件，不是单文件动作）。

**审计**

- 双路异源审计（`deepseek-v4.1-flash:1017` + `gpt-6.1-sol`）：4 条 BLOCKING + 12 条 IMPL-FIXABLE 已闭合，记录见 `docs/nodes/V5-audit/审计-双路-20261121.md`。

"""


def main():
    skill, changelog = sys.argv[1], sys.argv[2]
    check_only = "--check" in sys.argv
    st = io.open(skill, encoding="utf-8").read()
    ct = io.open(changelog, encoding="utf-8").read()
    nf, nc = st.count(FM_OLD), ct.count(CL_ANCHOR)
    print("frontmatter 命中 %d（预期 1）%s" % (nf, "" if nf == 1 else "  <<< 不匹配"))
    print("CHANGELOG 锚点命中 %d（预期 1）%s" % (nc, "" if nc == 1 else "  <<< 不匹配"))
    if nf != 1 or nc != 1:
        print("[中止] 未按预期命中，未写盘。")
        return 2
    if check_only:
        print("[check] 全部命中（未写盘）")
        return 0
    io.open(skill, "w", encoding="utf-8", newline="").write(st.replace(FM_OLD, FM_NEW))
    io.open(changelog, "w", encoding="utf-8", newline="").write(ct.replace(CL_ANCHOR, CL_NEW + CL_ANCHOR))
    print("[完成] SKILL.md 版本 -> 13.0.0；CHANGELOG 已追加 v13.0.0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
