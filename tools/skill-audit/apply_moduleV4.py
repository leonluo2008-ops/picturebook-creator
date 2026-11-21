# -*- coding: utf-8 -*-
"""V4 · 术语与格式代际统一。

死链复核结论：真实死链 0 条（`scripts/notion_` 是扫描器把通配 `scripts/notion_*.py` 截断的误报）。
术语残留：语境重复页 / 六视图 / 定稿参考 / audit_ledger.py 均 = 0。

本脚本只补一条实测的格式漂移：
- 旧档 13 本在 `旁白:` 行带 `P1 …` 前缀；8 页在 `页面类型:` 写「P1 语境重复页」→ v13 统一为不带前缀。

用法: python apply_moduleV4.py <SKILL.md> [--check]
"""
import io
import sys

REPLACEMENTS = [
    ("V4a-门禁补格式规则",
     "- 中文列夹用的目标词跟随英文列同形态：封面 Title Case 行跟随（Floor），普通句夹用一律小写（CY/T 154—2017 7.1）。",
     """- 中文列夹用的目标词跟随英文列同形态：封面 Title Case 行跟随（Floor），普通句夹用一律小写（CY/T 154—2017 7.1）。
- **`旁白:` 行与 `页面类型:` 行都不写页码前缀**：`旁白:` 直接写文案（页码由页序体现），`页面类型:` 只写类型名（`认知页` / `语境页` / `词族拓展页` / `互动练习页`）。实测旧档 **13 本**在 `旁白:` 行带了 `P1 …` 前缀、**8 页**在 `页面类型:` 里写「P1 语境重复页」——属格式漂移；v13 统一为不带前缀，存量重整时一并去掉。""",
     1),

    ("V4b-存量重整缺口清单",
     "- 整本没有「构图要求」句式——每页末尾按当页主体补齐,高危部位点名(耳朵=最高点/脚=最低点/横排字母两端/网格四角)。",
     """- 整本没有「构图要求」句式——每页末尾按当页主体补齐,高危部位点名(耳朵=最高点/脚=最低点/横排字母两端/网格四角)。
- `旁白:` 行带 `P1 …` 页码前缀、或 `页面类型:` 写成「P1 语境重复页」——去掉前缀（实测旧档 13 本/8 页有）。""",
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
        print("%-20s 命中 %d（预期 %d）%s" % (rid, n, expect, "" if n == expect else "  <<< 不匹配"))
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
