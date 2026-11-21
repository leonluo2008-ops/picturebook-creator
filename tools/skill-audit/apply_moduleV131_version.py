# -*- coding: utf-8 -*-
"""v13.1.0 版本升档：frontmatter / README / CHANGELOG 三处同档。

用法: python apply_moduleV131_version.py <repo_root> [--check]
"""
import io
import os
import sys

CL_OLD = "## （未发布）v13.0.0 之后 · 工具与证据修补 — 2026-11-21"
CL_NEW = """## v13.1.0 — 2026-11-21 · 所有者裁定落地（规则缺口收敛）

> 所有者对「待审查清单」第二节逐条裁定后，本节为落地结果。基线 `13.0.0`（`5d66819`）。

**所有者明确裁定的三条**

- **G4**：词族拓展页英文列**用词表**（如 `Pot, hot, dot, cot.`），**不写成句子、不加引导句**——朗读节奏优先（原倾向短句的做法作废）。
- **G6**：词族词**常规 2–3 个、最多 4 个**（含核心词本身）；超过 4 个会挤爆「每页 10 词」上限。
- **G8**：**L4 的 `旁白:` 行必须是「英文 / 中文」双语形态**（英文在前、中文在后，` / ` 分隔）。纯英文行不合规。两条 L4 模板（领读 / 故事）同步改为 `旁白: [英文文案] / [中文文案]`。

**按推荐执行的八条**

- G1：核心词本身是词族成员时（pot 之于 pot/hot/dot/cot）必须列为成员、放第一位。
- G5：词族页主角可缺席；缺席时「角色一致性」写 `角色一致性: 本页无角色——教学载体是词族词`。
- G7：同页多词可各词一色，每词仍须单色整词、不逐字母分色。
- G9：简介首句只禁「场景布置」（摆/放/挂 + 物体存在）；「结果状态」（碗里的汤是煮出来的）放行。
- G-Fam-1：承认**首音族**（r-: robot/rabbit/rocket/rain），但同一本书不得与同尾族混用。
- G-Adj-1：简介词型分档补 **维度型**（形容词：两个端点的距离 / 一次没完成的量）。
- G-Prep-1：同表补 **关系型**（位置介词：遮障的后果 + 必须写方向词）。
- D1/D3：结构自检闸与标题/简介判据登记为**可选自检工具**，不进「缺一不过」，是否升级为交付门禁由所有者定。

**门禁口径**

- D2：三道门命令统一加 `--expect-pages <页数>`（不带时脚本只校验解析到的页，页数漏解析会静默放过）。
- 新增「可选自检工具」小节，写明两个工具比交付门禁严、旧档不回填。

**证据**

- V7d（long，形容词）与 V7e（behind，位置介词）实测跑通，词型分档后两档属 **L1 证据**（语料里形容词 1 本、介词 1 本）。
- 双语旁白形态经夹具实测：`l4_case_check` / `l4_presence_check` / `l4_structure_check` 三道均 exit 0，解析口径正确（`/` 前英文、`/` 后中文）。

## （未发布）v13.0.0 之后 · 工具与证据修补 — 2026-11-21"""

JOBS = [
    ("SKILL.md", "version: 13.0.0", "version: 13.1.0"),
    ("README.md", "## ⚠️ 当前版本：v13.0.0（2026-11-21，重构分支 `refactor/v13-20261121`）",
     "## ⚠️ 当前版本：v13.1.0（2026-11-21，开发分支 `dev`；`main` 为稳定线）"),
    ("CHANGELOG.md", CL_OLD, CL_NEW),
]


def main():
    root = sys.argv[1]
    check_only = "--check" in sys.argv
    bad = []
    for rel, old, new in JOBS:
        p = os.path.join(root, rel.replace("/", os.sep))
        t = io.open(p, encoding="utf-8").read()
        n = t.count(old)
        print("%-14s 命中 %d %s" % (rel, n, "" if n == 1 else "<<< 不匹配"))
        if n == 1:
            if not check_only:
                io.open(p, "w", encoding="utf-8", newline="").write(t.replace(old, new))
        else:
            bad.append(rel)
    if bad:
        print("\n[中止] 未命中: %s" % ", ".join(bad))
        return 2
    print("\n[完成] 三处已升到 13.1.0" if not check_only else "\n[check] 命中（未写盘）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
