# -*- coding: utf-8 -*-
"""V8b · 跨文件口径订正（复审指出：RELEASE_NOTES 把 133 解释反、README 版本未同档、
asset_ref.py 仍写「场景/物件」、适配包/计划书/盘点文档与新口径不一致）。

用法: python apply_moduleV8b.py <workspace_root> [--check]
"""
import io
import os
import sys

JOBS = [
    # 文件, 标识, 旧串, 新串
    ("picturebook-creator/SKILL.md", "J1-残余术语",
     "请上传角色的原始参考图,我将为你生成可在即梦使用的多视图定妆提示词。",
     "请上传角色的原始参考图,我将为你生成可在即梦使用的**多视角参考图（默认三视角）**提示词。"),

    ("picturebook-creator/scripts/asset_ref.py", "J2-asset_ref-doc",
     "角色/场景/物件参考图统一存",
     "角色 / 风格参考图统一存"),
    ("picturebook-creator/scripts/asset_ref.py", "J3-asset_ref-help",
     'help="按「资产类型」筛选（角色/场景/物件…）"',
     'help="按「资产类型」筛选（角色 / 风格参考）"'),

    ("picturebook-creator/README.md", "J4-README版本",
     "## ⚠️ 当前版本：v11.1.8-codex.10（2026-11-10，Codex 独立分支）",
     "## ⚠️ 当前版本：v13.0.0（2026-11-21，重构分支 `refactor/v13-20261121`）"),

    ("picturebook-creator/RELEASE_NOTES_v13.0.0.md", "J5-133解释反了",
     "（243 页里 133 页实际顺序与模板不同，照样验收通过）",
     "（243 页里 133 页就是模板块序、110 页顺序不同，两种都被验收通过）"),

    ("docs/项目适配包.md", "J6-适配包HEAD",
     "| 分支 / HEAD | **`refactor/v13-20261121`** / `698304e`（2026-11-21 建分支；基线 `9288959`） |",
     "| 分支 / HEAD | **`refactor/v13-20261121`** / 以 `git log -1` 为准（基线 `9288959`） |"),
    ("docs/项目适配包.md", "J7-适配包词数档",
     "| V2 | 族4 L4：块序（存在性硬/顺序软）、≤10 词降软、安全区三要素定档 | 已完成（`3b38e2a`） |",
     "| V2 | 族4 L4：块序（存在性硬/顺序软）、**≤10 词定档为领读硬上限**、安全区三要素定档 | 已完成（`3b38e2a`） |"),

    ("docs/开发计划书.md", "J8-计划书V2",
     "B1 块序（存在性硬/顺序软）、B3 ≤10 词降软、B5 背景铺边定档",
     "B1 块序（存在性硬/顺序软）、B3 ≤10 词定档（领读硬上限）、B5 背景铺边定档"),
    ("docs/开发计划书.md", "J9-计划书B1证据",
     "存档 9/9 页为 角色→场景→风格→构图要求",
     "243 页实测：完整块序 133/243、只构图 97、其它 13"),

    ("docs/盘点-29本-规则族-20261121.md", "J10-盘点软约束1",
     "任有一页 >10 ⇒「≤10 词」是软约束",
     "该统计**含故事模式 2 本**；领读 243 页实测 0 页超 10 ⇒ 领读定硬上限 10，故事模式另计"),
    ("docs/盘点-29本-规则族-20261121.md", "J11-盘点软约束2",
     "| B3 | 「单页英文 ≤10 词」 | 2/29 超 | 降为软约束（建议值） |",
     "| B3 | 「单页英文 ≤10 词」 | 2/29 超（均在故事模式） | 领读定硬上限 10；原「15」作废 |"),
]


def main():
    root = sys.argv[1]
    check_only = "--check" in sys.argv
    rows, bad = [], []
    for rel, rid, old, new in JOBS:
        p = os.path.join(root, rel.replace("/", os.sep))
        text = io.open(p, encoding="utf-8").read()
        n = text.count(old)
        rows.append((rid, rel, n))
        if n == 1:
            io.open(p, "w", encoding="utf-8", newline="").write(text.replace(old, new))
        else:
            bad.append((rid, rel, n))
    for rid, rel, n in rows:
        print("%-18s %-46s 命中 %d %s" % (rid, rel, n, "" if n == 1 else "  <<< 不匹配"))
    if bad:
        print("\n[注意] %d 处未命中（其余已写盘；检查后补跑）。" % len(bad))
        return 2 if check_only else 1
    print("\n[完成] %d 处全部命中并写盘" % len(JOBS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
