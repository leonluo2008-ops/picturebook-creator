#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L4 结构门禁 v1.0 —— 补「块存在性 / 每页词数 / 构图三要素」的机器断言。

背景：2026-11-21 v13 双路审计指出，`l4_case_check.py` 只校形态、`l4_presence_check.py` 只校存在，
两者都不校「块是否写齐」「每页词数是否超限」「构图要求三要素是否齐」——这三条一直是人工检查。

本脚本把这些做成可失败断言（判据来自 SKILL.md v13.0.0）：
1. 页数与比例：封面 3:4，内页 16:9
2. 页面类型 ∈ {认知页, 语境页, 词族拓展页, 互动练习页}，且不带 `Pn` 前缀
3. 每页块存在性：角色一致性 / 场景一致性 / 构图要求（领读模式另要「目标词图形化」；词族拓展页豁免核心词块不豁免块存在性）
4. 构图要求三要素：约80%安全区、四边约10%净空、背景自然延伸填充到边缘
5. 每页英文词数 ≤ --max-words（默认 10）
6. `旁白:` 行不带 `Pn` 前缀

用法:
  python l4_structure_check.py <L4文件> --word coin [--max-words 10]
退出码: 0=全过  1=有违规
注：本脚本只做文本断言，不代替成图验收。
"""
import argparse
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
except Exception:
    pass

PAGE_TYPES = {"认知页", "语境页", "词族拓展页", "互动练习页"}
SAFETY = ("80%", "10%", "边缘")


def parse_pages(text):
    pages, cur = [], None
    for line in text.splitlines():
        s = line.strip()
        m = re.match(r"^旁白[:：]\s*(.*)$", s)
        if m:
            cur = {"narration": m.group(1), "ratio": "", "ptype": "", "prompt": ""}
            pages.append(cur)
            continue
        if cur is None:
            continue
        for key, field in (("比例", "ratio"), ("页面类型", "ptype"), ("生图提示词", "prompt")):
            mm = re.match(r"^" + key + r"[:：]\s*(.*)$", s)
            if mm:
                cur[field] = mm.group(1)
                break
        else:
            if cur["prompt"]:
                cur["prompt"] += "\n" + s
    return pages


def eng_words(narration):
    return len(re.findall(r"[A-Za-z][A-Za-z'\-]*", (narration or "").split("/")[0]))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("l4file")
    ap.add_argument("--word", required=True)
    ap.add_argument("--max-words", type=int, default=10)
    ap.add_argument("--family-words", default="",
                    help="词族拓展页应出现的词族词（逗号分隔，如 hot,dot,cot）；给了就断言本页都出现")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()
    args.family_words = [w.strip() for w in args.family_words.split(",") if w.strip()]

    try:
        text = open(args.l4file, encoding="utf-8-sig").read()
    except OSError as e:
        print("读不到文件: %s" % e)
        return 1
    pages = parse_pages(text)
    if not pages:
        print("没解析到页面记录（应以「旁白: 」行开始）")
        return 1

    issues = []
    rows = []
    for i, p in enumerate(pages):
        no = "封面" if i == 0 else "P%d" % i
        pr = p.get("prompt") or ""
        ptype = (p.get("ptype") or "").strip()
        ratio = (p.get("ratio") or "").strip()
        words = eng_words(p.get("narration") or "")
        has_role = "角色一致性" in pr
        has_scene = "场景一致性" in pr
        has_comp = "构图要求" in pr
        seg = pr.split("构图要求", 1)[1] if has_comp else ""
        safety_miss = [b for b in SAFETY if b not in seg]
        is_family = "词族拓展页" in ptype
        # 词族拓展页豁免的是「核心词字面入画」，不豁免「目标词图形化」块本身；
        # 若给了 --family-words，则本页必须出现这些词族词。
        fam_ok = True
        if is_family and args.family_words:
            fam_ok = all(w.lower() in pr.lower() for w in args.family_words)
        has_word_block = (("目标词图形化" in pr) or (args.word.lower() in pr.lower())) and fam_ok

        rows.append((no, ratio, ptype, words, has_role, has_scene, has_comp, not safety_miss))

        want = "3:4" if i == 0 else "16:9"
        if ratio != want:
            issues.append("[%s] 比例 %r，应为 %s" % (no, ratio, want))
        if re.match(r"^P\d+\s", ptype):
            issues.append("[%s] 页面类型带 Pn 前缀：%r" % (no, ptype))
        if ptype not in PAGE_TYPES and not re.match(r"^P\d+\s", ptype):
            issues.append("[%s] 页面类型 %r 不在词表" % (no, ptype))
        if not has_role:
            issues.append("[%s] 缺「角色一致性」块" % no)
        if not has_scene:
            issues.append("[%s] 缺「场景一致性」块" % no)
        if not has_comp:
            issues.append("[%s] 缺「构图要求」" % no)
        if safety_miss:
            issues.append("[%s] 构图要求缺：%s" % (no, "、".join(safety_miss)))
        if words > args.max_words:
            issues.append("[%s] 每页英文 %d 词 > 硬上限 %d" % (no, words, args.max_words))
        if not has_word_block:
            issues.append("[%s] 缺目标词入画依据（既无「目标词图形化」块、页内也未出现 %r）" % (no, args.word))
        if re.match(r"^P\d+\s", (p.get("narration") or "").strip()):
            issues.append("[%s] 旁白行带 Pn 前缀" % no)

    if not args.quiet:
        print("解析 %d 页；核对：块存在性 / 词数≤%d / 构图三要素 / 比例 / 页面类型 / Pn 前缀" % (len(pages), args.max_words))
        print("| 页 | 比例 | 页面类型 | 词数 | 角色 | 场景 | 构图 | 三要素 |")
        print("|---|---|---|---|---|---|---|---|")
        for no, ratio, ptype, words, r1, r2, r3, safe in rows:
            print("| %s | %s | %s | %d | %s | %s | %s | %s |" % (
                no, ratio, ptype, words, "✓" if r1 else "✗", "✓" if r2 else "✗",
                "✓" if r3 else "✗", "✓" if safe else "✗"))
    if issues:
        print("\n[必须修复] %d 处" % len(issues))
        for x in issues:
            print("  ✗ " + x)
        return 1
    print("\n结构门禁全过——块存在性 / 词数 / 构图三要素 / 比例 / 页面类型 / Pn 前缀 均合规")
    return 0


if __name__ == "__main__":
    sys.exit(main())
