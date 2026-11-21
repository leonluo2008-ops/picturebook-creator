# -*- coding: utf-8 -*-
"""V3 · 规则族2（标题）+ 族3（旁白）—— 只补证据脚注，不改规则。

29 本实测结论（docs/盘点-29本-规则族-20261121.md）：
- 英文标题含核心词 27/27（2 本为故事模式空标题）→ 规则已正确（L539），补证据
- 标题含括注 0/29、禁词 0/29 → 规则已正确（L545），补证据
- 拆读残留 2/29 → 规则已正确（L885 存量重整清理拆词旁白），补证据

用法: python apply_moduleV3.py <SKILL.md> [--check]
"""
import io
import sys

REPLACEMENTS = [
    ("B6a-标题含词证据",
     "- **英文列也必须把目标词写进去**：",
     "- **英文列也必须把目标词写进去**（29 本实测：有英文标题的 27 本 **27/27** 都含核心词，规则成立）：",
     1),

    ("B6b-禁括注证据",
     "- ❌ **禁止方法论括注**：不写「（自然拼读绘本）」「（Phonics）」「（CVC）」，中英文都不加。",
     "- ❌ **禁止方法论括注**：不写「（自然拼读绘本）」「（Phonics）」「（CVC）」，中英文都不加。（29 本实测：**0/29** 含括注、**0/29** 含方法论禁词，规则成立）",
     1),

    ("B7-拆读存量证据",
     "存量稿采用新规范重整时，一并清理拆词旁白、分块字卡和旧颜色映射。",
     "存量稿采用新规范重整时，一并清理拆词旁白、分块字卡和旧颜色映射（29 本实测：仍有 **2/29** 的书留着 `S-O-A-P` 型拆读页，属重整必清项，不是可选项）。",
     1),
]


def main():
    path = sys.argv[1]
    check_only = "--check" in sys.argv
    text = io.open(path, encoding="utf-8").read()
    rows = []
    for rid, old, new, expect in REPLACEMENTS:
        n = text.count(old)
        rows.append((rid, n, expect))
        if n == expect:
            text = text.replace(old, new)
    bad = [r for r in rows if r[1] != r[2]]
    for rid, n, expect in rows:
        print("%-18s 命中 %d（预期 %d）%s" % (rid, n, expect, "" if n == expect else "  <<< 不匹配"))
    if bad:
        print("[中止] 未按预期命中，未写盘。")
        return 2
    if check_only:
        print("[check] 全部命中（未写盘）")
        return 0
    io.open(path, "w", encoding="utf-8", newline="").write(text)
    print("[完成] 已改写 %d 处" % len(REPLACEMENTS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
