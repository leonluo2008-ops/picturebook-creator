#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L4 生图提示词 · 「在不在」逐页门禁 v3.0（按需模式）

补 SKILL.md「画面文字形态门禁」的缺口：`l4_case_check.py` 只校形态不校存在
（整页没写目标词也 EXIT=0，实测核心词传错同样「全过」）。

v3.0 相对 v2.0 的修改（依据 2026-11-23 所有者改口径）：
- 默认改为**按需模式**：目标词按旁白需要出现，不强制每页；缺页只打印提示行，
  不再判失败。汇总打印「目标词出现 N 页 / 共 M 页」。
- `--require-all`：恢复旧口径（每页必须出现，缺一页 EXIT=1）。
- `--min-pages N`：要求至少 N 页出现，否则 EXIT=1（默认 0＝不设下限）。
- 诚实声明：本脚本只做字面匹配与缺页提示，**不判断载体的叙事恰当性**
  （目标词是否被塞进叙事道具等载体纪律，靠人工核）。

v2.0 保留的行为：
- 页数断言 `--expect-pages`：解析到的页数不等于期望即 fail（v1 会把 `- 旁白:` 这类漏页静默吞掉）
- 全量剥离 `\\ufeff`（v1 只靠 utf-8-sig 处理文件首 BOM，中段 BOM 仍丢页）
- 退出码契约：0=过 / 1=有违规 / 2=输入错误（编码、页数、参数）；docstring 写明
- `UnicodeDecodeError` 归 2，不再抛 traceback
- `--page-words` 空词集 / 越界页码 / 重复页号 → exit 2（v1 会静默改变判定）
- 词匹配默认加词界 `(?<![a-z])word(?![a-z])`（v1 裸子串，`soa` / `photo` 会误命中）
- docstring 与实现对齐：本脚本只做 `--word/--page-words` 字面匹配，**不读封面书名**

用法:
  python3 l4_presence_check.py <L4文件> --word soap [--expect-pages 9]        # 按需模式（默认）
  python3 l4_presence_check.py <L4文件> --word soap --expect-pages 9 --require-all  # 旧严格口径
  python3 l4_presence_check.py <L4文件> --word pot --page-words 7=hot,dot,cot
退出码: 0=过  1=有违规（仅 --require-all 或 --min-pages 触发）  2=输入/参数错误
"""
import argparse

# ── 词形口径：与其它门禁共用 tools/wordforms.py（2026-11-21）──
import os as _os, sys as _sys
_HERE = _os.path.dirname(_os.path.abspath(__file__))
for _p in (_HERE, _os.path.join(_HERE, '..', 'tools')):
    if _os.path.isfile(_os.path.join(_p, 'wordforms.py')):
        _sys.path.insert(0, _os.path.abspath(_p))
        break
from wordforms import word_forms, forms_pattern, upper_forms

import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
except Exception:
    pass

# v3.1（2026-11-25 所有者指令）：--word 支持词组（如 "post office" / "toy store"），
# 作为**一个整体**匹配：词与词之间允许空格/连字符，末词允许复数 s；不匹配单词乱序。
WORD_OK = re.compile(r"^[A-Za-z][A-Za-z'\-]*(?: [A-Za-z][A-Za-z'\-]*)*$")


def parse_pages(text):
    text = text.replace("\ufeff", "")
    pages, cur = [], None
    for line in text.splitlines():
        s = line.strip()
        m = re.match(r"^旁白[:：]\s*(.*)$", s)
        if m:
            cur = {"narration": m.group(1), "ptype": "", "prompt": ""}
            pages.append(cur)
            continue
        if cur is None:
            continue
        m = re.match(r"^生图提示词[:：]\s*(.*)$", s)
        if m:
            cur["prompt"] = m.group(1)
            continue
        mv = re.match(r"^入画英文[:：]\s*(.*)$", s)
        if mv:
            raw = mv.group(1).replace("[", "").replace("]", "").replace('"', "").replace("'", "").strip()
            cur["vocab"] = [w.strip() for w in re.split(r"[、,;；]", raw) if w.strip()]
            continue
        m2 = re.match(r"^页面类型[:：]\s*(.*)$", s)
        if m2:
            cur["ptype"] = m2.group(1).strip()
            continue
        if re.match(r"^比例[:：]", s):
            continue
        if cur["prompt"]:
            cur["prompt"] += "\n" + s
    return pages


def scene_segment(prompt):
    if "构图要求" in prompt:
        return prompt.split("构图要求", 1)[0]
    return prompt


def contains_word(haystack: str, word: str) -> bool:
    """加词界的大小写不敏感匹配；word 含连字符/撇号时按字面。
    词组（含空格）作为一个整体：词间允许空白或连字符，末词允许复数 s；
    单词仍走词形库。"""
    if " " in word.strip():
        toks = [t for t in word.split() if t]
        parts = [re.escape(t) for t in toks]
        pat = r"(?<![A-Za-z])" + r"[\s\-]+".join(parts) + r"s?(?![A-Za-z])"
        return re.search(pat, haystack, flags=re.I) is not None
    return re.search(forms_pattern(word), haystack, flags=re.I) is not None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("l4file")
    ap.add_argument("--word", action="append", default=[],
                    help="目标核心词（重复传伙伴词；会套用到所有未指定 page-words 的页）")
    ap.add_argument("--page-words", action="append", default=[],
                    help="按页指定词集，格式 页码=词1,词2（0=封面，1=第一个内页）")
    ap.add_argument("--expect-pages", type=int, default=0,
                    help="期望页数（含封面）；>0 时解析页数不等即判 fail")
    ap.add_argument("--from-plan", action="store_true",
                    help="按每页 L4 自己的「入画英文:」声明核对：声明了词/词组而画面没有→EXIT=1；入画英文: [] →按需省略不判错（该模式下 --word 仅作汇总参考，可省略）")
    ap.add_argument("--require-all", action="store_true",
                    help="恢复旧口径：每页必须出现目标词，缺一页 EXIT=1（默认按需模式，缺页只提示）")
    ap.add_argument("--min-pages", type=int, default=0,
                    help="要求至少 N 页出现目标词，否则 EXIT=1（默认 0＝不设下限）")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    if args.min_pages < 0:
        print("--min-pages 不能为负数：%d" % args.min_pages)
        return 2

    for w in args.word:
        if not WORD_OK.match(w):
            print("--word 参数非法：%r（只接受英文词或空格分隔的词组；伙伴词请重复传 --word，不要用逗号分隔）" % w)
            return 2

    page_words = {}
    for spec in args.page_words:
        if "=" not in spec:
            print("--page-words 格式错误：%r（应为 页码=词1,词2）" % spec)
            return 2
        k, v = spec.split("=", 1)
        try:
            idx = int(k.strip())
        except ValueError:
            print("--page-words 页码非整数：%r" % k)
            return 2
        words = [x.strip() for x in v.split(",") if x.strip()]
        if not words:
            print("--page-words 空词集：%r（空词集会静默关闭该页检查，已拒绝）" % spec)
            return 2
        if idx in page_words:
            print("--page-words 重复页号：%d（重复会静默覆盖前一条，已拒绝）" % idx)
            return 2
        page_words[idx] = words

    try:
        text = open(args.l4file, encoding="utf-8-sig").read()
    except FileNotFoundError:
        print("读不到文件（不存在）：%s" % args.l4file)
        return 2
    except UnicodeDecodeError as e:
        print("文件不是 UTF-8：%s（%s）。请另存为 UTF-8 或 UTF-8 BOM 后再跑。" % (args.l4file, e))
        return 2
    except OSError as e:
        print("读不到文件：%s" % e)
        return 2

    pages = parse_pages(text)
    if not pages:
        print("没解析到任何页面记录（应以「旁白: 」行开始）")
        return 2
    if args.expect_pages and len(pages) != args.expect_pages:
        print("页数不符：解析到 %d 页，期望 %d 页。"
              "常见原因：某一页的「旁白:」被写成列表/加粗/带前导字符，被吞进上一页。" % (len(pages), args.expect_pages))
        return 1
    max_idx = len(pages) - 1
    for idx in page_words:
        if idx < 0 or idx > max_idx:
            print("--page-words 页码越界：%d（本文件页码范围 0–%d）" % (idx, max_idx))
            return 2

    issues, missing_pages, skipped, used_page_words, omitted = [], [], [], [], []
    for i, p in enumerate(pages):
        page_no = "封面" if i == 0 else "P%d" % i
        if "词族拓展页" in (p.get("ptype") or "") and i not in page_words:
            skipped.append(page_no)
            continue
        if args.from_plan:
            words = p.get("vocab") or []
            if not words:
                omitted.append(page_no)
                continue
        elif i in page_words:
            words = page_words[i]
            used_page_words.append((page_no, words))
        else:
            words = args.word
        scene = scene_segment(p["prompt"])
        for w in words:
            if not contains_word(scene, w):
                if args.require_all or args.from_plan:
                    issues.append("[%s] 场景描述段未出现目标词 '%s'——教学载体丢失"
                                  "（画面上不会有这个词，机审的形态检查也发现不了）" % (page_no, w))
                else:
                    missing_pages.append((page_no, w))

    if not args.quiet:
        if args.from_plan:
            mode = "声明模式（--from-plan：按每页「入画英文:」核对）"
        elif args.require_all:
            mode = "严格模式（--require-all）"
        else:
            mode = "按需模式（缺页只提示，不构成错误）"
        words_shown = args.word if args.word else ["（--from-plan：逐页取声明）"]
        print("解析 %d 页；核对目标词 %s 的「在不在」（%s）" % (len(pages), words_shown, mode))
        if skipped:
            print("跳过 %d 页（词族拓展页，教学载体是词族词）: %s"
                  "——这些页请用 --page-words \"<页号>=词1,词2\" 核对" % (len(skipped), ", ".join(skipped)))
        if omitted:
            print("· 按需省略 %d 页（入画英文: []，不判错）：%s" % (len(omitted), ", ".join(omitted)))
        if used_page_words:
            print("按页指定词集：" + "；".join("%s=%s" % (no, ",".join(ws)) for no, ws in used_page_words))
        if missing_pages:
            print("· 本页无目标词（按需模式下不构成错误）：%s" % ", ".join(no for no, _ in missing_pages))
        absent = len({no for no, _ in missing_pages}) | len({x.split("]")[0][1:] for x in issues})
        print("目标词出现 %d 页 / 共 %d 页" % (len(pages) - len(skipped) - absent, len(pages)))
    if issues:
        print("\n[必须修复] %d 处" % len(issues))
        for x in issues:
            print("  ✗ " + x)
        return 1
    if args.min_pages > 0:
        present = len(pages) - len(skipped) - len({no for no, _ in missing_pages})
        if present < args.min_pages:
            print("\n[必须修复] 目标词只出现 %d 页，低于 --min-pages %d 的下限" % (present, args.min_pages))
            return 1
    if not args.quiet:
        if args.from_plan:
            print("声明模式核对完成——声明词组的页全都有词，入画英文:[] 的页按需省略")
        elif args.require_all:
            print("逐页在不在：全过——每页场景段都能看到目标词字面（严格口径）")
        else:
            print("按需模式核对完成")
        print("诚实声明：本脚本只做字面匹配与缺页提示，不判断载体的叙事恰当性（载体纪律靠人工核）。")
        print("注意：本脚本只做字面匹配，不读封面书名；封面那页需人工按书名校对。需要旧严格口径时加 --require-all。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
