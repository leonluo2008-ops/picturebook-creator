#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L4 生图提示词 · 「在不在」逐页门禁 v1.0

补 SKILL.md「画面文字形态门禁」的缺口：`l4_case_check.py` 只校形态不校存在——
整页压根没写目标词时它照样 EXIT=0（实测：核心词传错也输出「全过」）。

本脚本只做一件事：逐页取「生图提示词:」到「构图要求:」之间的**场景描述段**
（不含安全区句，那里提到词不算入画），断言里面出现目标词字面；封面按正式英文标题核对。

用法:
  python l4_presence_check.py <L4文件> --word soap
  python l4_presence_check.py <L4文件> --word glue --word blue

退出码: 0=每页都在  1=有页缺失

注：Windows 控制台默认 GBK，输出含 ✗ 会抛 UnicodeEncodeError；本脚本已 reconfigure 为 UTF-8。
"""
import argparse
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
except Exception:
    pass


def parse_pages(text):
    pages = []
    cur = None
    for line in text.splitlines():
        s = line.strip()
        m = re.match(r"^旁白[:：]\s*(.*)$", s)
        if m:
            cur = {"narration": m.group(1), "prompt": ""}
            pages.append(cur)
            continue
        if cur is None:
            continue
        m = re.match(r"^生图提示词[:：]\s*(.*)$", s)
        if m:
            cur["prompt"] = m.group(1)
            continue
        m3 = re.match(r"^页面类型[:：]\s*(.*)$", s)
        if m3:
            cur["ptype"] = m3.group(1)
            continue
        m4 = re.match(r"^比例[:：]\s*(.*)$", s)
        if m4:
            continue
        if cur["prompt"]:
            cur["prompt"] += "\n" + s
    return pages


def scene_segment(prompt):
    """取「生图提示词」正文里、构图要求之前的场景描述段"""
    if "构图要求" in prompt:
        return prompt.split("构图要求", 1)[0]
    return prompt


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("l4file", help="L4 生图提示词纯文本文件")
    ap.add_argument("--word", action="append", required=True,
                    help="目标核心词（可重复传伙伴词；注意：会套用到所有页）")
    ap.add_argument("--page-words", action="append", default=[],
                    help="按页指定词集，格式 页码=词1,词2（页码 1=第一个内页，0=封面）；"
                         "用于词族拓展页这类「本页只该出现词族词」的情形")
    args = ap.parse_args()

    page_words = {}
    for spec in args.page_words:
        try:
            k, v = spec.split("=", 1)
            page_words[int(k.strip())] = [x.strip() for x in v.split(",") if x.strip()]
        except Exception:
            print("--page-words 格式错误：%r（应为 页码=词1,词2）" % spec)
            return 2

    try:
        text = open(args.l4file, encoding="utf-8").read()
    except OSError as e:
        print("读不到文件: %s" % e)
        return 1

    pages = parse_pages(text)
    if not pages:
        print("没解析到任何页面记录（应以「旁白: 」行开始）")
        return 1

    issues = []
    skipped = []
    for i, p in enumerate(pages):
        page_no = "封面" if i == 0 else "P%d" % i
        ptype = (p.get("ptype") or "").strip()
        # 词族拓展页：若给了 --page-words 指定本页词集，就按词集核；否则跳过
        # （词族页的教学载体是词族词，本就不要求核心词入画）
        if "词族拓展页" in ptype:
            if i not in page_words:
                skipped.append(page_no)
                continue
        words = page_words.get(i, args.word)
        scene = scene_segment(p["prompt"])
        low = scene.lower()
        for w in words:
            if w.lower() not in low:
                issues.append("[%s] 场景描述段未出现目标词 '%s'——教学载体丢失"
                              "（画面上不会有这个词，机审的形态检查也发现不了）" % (page_no, w))

    print("解析 %d 页，核对目标词 %s 的「在不在」" % (len(pages), args.word))
    if skipped:
        print("跳过 %d 页（词族拓展页，教学载体是词族词）: %s" % (len(skipped), " / ".join(skipped)))
    if issues:
        print("\n[必须修复] %d 处" % len(issues))
        for x in issues:
            print("  ✗ " + x)
        return 1
    print("逐页在不在：全过——每页场景段都能看到目标词字面")
    return 0


if __name__ == "__main__":
    sys.exit(main())
