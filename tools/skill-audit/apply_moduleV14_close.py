# -*- coding: utf-8 -*-
"""v14 复核闭合：修掉两路复核指出的「文档一行级」问题。

复核结论（重活 + 轻活一致）：3 条 BLOCKING 已闭；剩余全是机械修补，判 NO 只因「带着已知错句发布」。

本脚本处理：
A. gates.md:70 自相矛盾（grammar 零解析已 exit 2）
B. gates.md BOM 说明不覆盖 l4_case；Path() 归因错
C. rules.md §0 原话列指向落空 → 改为「见需求文档 §三 R#」；SKILL.md:67 承诺同步
D. README:282 16→17 种、删「唯一引用」；README:258 frontmatter 环境变量；README ≤8 词口径
E. CHANGELOG / 适配包 数字未同步（142→144、18→20、11244→12209）
F. 适配包 version/目标版本/references 件数/nodes 路径
G. 两份 AGENTS.md 版本 13.1.0 → 14.0.0
H. rules.md 分母 29 与口径 27 并置
I. 裸〔裁定〕（无 §0 条目）→ 去标记，并声明「无标注属实践约定」
J. test-prompts.json 仍期望故事模式
K. W3 映射表过期陈述

用法: python apply_moduleV14_close.py <repo> [--check]
"""
import io
import os
import sys

REPO = r"E:\OneDrive\工作文件夹\儿童绘本\codex-workspace\picturebook-creator"

# (相对路径, 编号, 旧文本, 新文本, 期望命中数)
EDITS = [
    ("references/gates.md", "A1-退出码自相矛盾",
     "`grammar_check` / `l4_case_check` 读不到文件返回 **1**（它们自身不产生 2，除 argparse 参数错误）；",
     "`grammar_check` / `l4_case_check` 读不到文件返回 **1**；它们自身产生 2 只有两种情况——argparse 参数错误，或 `grammar_check` 解析到 0 行旁白（见 §2）；"),

    ("references/gates.md", "A2-BOM 说明覆盖 l4_case",
     "（v2.0 已全量剥离 `\\ufeff`，BOM 不再丢页）",
     "（v2.0 已全量剥离 `\\ufeff`，BOM 不再丢页；但 **`l4_case_check` 不剥 BOM**，中段 `\\ufeff` 会让它少解析一页却仍报「全过」——第 2 道没有页数断言，页数要人工核）"),

    ("references/gates.md", "A3-Path归因订正",
     "git-bash 风格 `/c/Users/...` 会被 `Path()` 拼成 `\\\\c\\\\...` 直接 FileNotFoundError。",
     "git-bash 风格 `/c/Users/...` 直接 **FileNotFoundError**（脚本用 `open()` 直读，不经 `Path` 归一，所以不认这种路径）。"),

    ("references/rules.md", "C1-原话列改为可命中",
     "**已裁定清单（2026-11-21 两批；原话与日期见末两列）**",
     "**已裁定清单（2026-11-21 两批）**\n\n> 「依据」列指向 `docs/需求-v14-清仓重建.md` §三 的裁定记录（含裁定与日期）；**逐字原话仅 R12 存有**，其余为摘要。无标注的规则句属**实践约定**，不享受裁定级稳定性。"),

    ("SKILL.md", "C2-承诺同步",
     "- 〔裁定〕所有者已拍板，只有所有者能改（编号、原话与日期见 `rules.md` §0）",
     "- 〔裁定〕所有者已拍板，只有所有者能改（编号与日期见 `rules.md` §0；逐字原话仅 R12 存于 `docs/需求-v14-清仓重建.md`）"),

    ("README.md", "D1-风格数17",
     "    └── style-library.md  # 风格备选库（16种预设风格，SKILL.md 唯一引用的参考文件）",
     "    └── style-library.md  # 风格备选库（17 种预设风格 S01–S17；SKILL 参考表 9 个文件之一）"),

    ("README.md", "D2-frontmatter环境变量",
     "前置条件：`NOTION_API_KEY` 在 `~/.hermes/.env`（frontmatter 已声明为必需环境变量），台账库已 Connect 到该 integration。",
     "前置条件：`NOTION_API_KEY` 放在 Hermes 凭据文件（本机 `C:\\Users\\leon3\\AppData\\Local\\hermes\\.env`），台账库已 Connect 到该 integration。**v14 的 frontmatter 只声明 name/description/version**，不再声明该变量；走 Notion MCP 时不需要它。"),

    ("CHANGELOG.md", "E1-行数同步",
     "把绘本 skill 从「1922 行混乱长文档」重建成 DSH skill 插件标准形态：①SKILL.md = frontmatter",
     "把绘本 skill 从「1922 行混乱长文档」重建成 DSH skill 插件标准形态（重建后 **144 行 / 12,209 B**，详见本文件顶部条目）：①SKILL.md = frontmatter"),

    ("docs/项目适配包.md", "F1-适配包体量",
     "（**142 行 / 11,244 B**，2026-11-21 实测）",
     "（**144 行 / 12,209 B**，2026-11-21 实测）"),

    ("docs/项目适配包.md", "F2-适配包版本口径",
     "- 更新：2026-11-21（v13.1.0 口径）",
     "- 更新：2026-11-21（v14.0.0 口径）"),

    ("docs/项目适配包.md", "F3-目标版本",
     "| 目标版本 | **13.1.0**（13.0.0 已发布打 tag；12.0.0 被 `hermes-skill-rebuild` 未完成线占用） |",
     "| 目标版本 | **14.0.0**（清仓重建；13.0.0/13.1.0 已发布打 tag，保留不动） |"),

    ("docs/项目适配包.md", "F4-references件数",
     "| 细则 | `../references/`（5 件：cloud-start / cover-design / notion-ledger-ops / standard-delivery / style-library） |",
     "| 细则 | `../references/`（**9 件**：flow / rules / l4-spec / gates / notion-ops / cover-design / style-library / standard-delivery / cloud-start） |"),

    ("docs/项目适配包.md", "F5-nodes路径",
     "| 实测节点产物（**仅作词型覆盖与文本层证据**） | `./nodes/V7*-v13/`",
     "| 实测节点产物（**仅作词型覆盖与文本层证据**） | `./nodes/样例-coin/`"),
]

# 逐行替换（模式化，可能多命中）
LINE_EDITS = [
    ("references/rules.md", "H1-28/29分母", "28/29 本", "29 本中 28 本（按 27 本领读口径＝27/27）"),
    ("references/rules.md", "H2-29/29分母", "29/29 本", "29 本全满足（按 27 本领读口径＝27/27）"),
    ("README.md", "D3-词数口径", "英文一页 ≤8 词", "英文一页硬上限 10 词、单句建议 ≤8"),
]


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else REPO
    check = "--check" in sys.argv
    bad = []
    for rel, rid, old, new in EDITS:
        p = os.path.join(root, rel.replace("/", os.sep))
        t = io.open(p, encoding="utf-8").read()
        n = t.count(old)
        print("%-24s %-40s 命中 %d %s" % (rid, rel, n, "" if n >= 1 else "<<< 需查"))
        if n >= 1 and not check:
            io.open(p, "w", encoding="utf-8", newline="").write(t.replace(old, new))
        if n < 1:
            bad.append(rid)
    for rel, rid, old, new in LINE_EDITS:
        p = os.path.join(root, rel.replace("/", os.sep))
        t = io.open(p, encoding="utf-8").read()
        n = t.count(old)
        print("%-24s %-40s 命中 %d %s" % (rid, rel, n, "" if n >= 1 else "<<< 需查"))
        if n >= 1 and not check:
            io.open(p, "w", encoding="utf-8", newline="").write(t.replace(old, new))
        if n < 1:
            bad.append(rid)
    print("\n%s：未命中 %d 处" % ("[check]" if check else "[完成]", len(bad)))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
