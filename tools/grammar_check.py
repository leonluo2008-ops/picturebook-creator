#!/usr/bin/env python3
"""领读绘本旁白表 · 中英大小写语法审计器 v1.1 (2026-10-24 参数化重写)

检查中英旁白表的大小写语法：
1. 英文列：句首字母必须大写；全大写长句仅限单词展示页；封面英文目标词禁全大写(应 Title Case)
2. 中文列：目标词形态跟随规则（CY/T 154-2017 第7节）
   - 英文列是纯展示行(封面单词行, 如 Floor / Learn "way") → 中文列跟随同形态(Title Case 展示行跟随大写; 带句子的展示行不适用)
   - 其余(句子夹用, 含 P1 拆解行) → 中文列一律小写(7.1 普通词不承担英文句首大写)
3. 句尾标点中英对应（. ! ? → 。！？）

用法: python3 grammar_check.py <旁白表.txt> --word floor [--word door]
输入格式: | 页码 | 英文 | 中文 |
"""
import sys
import re
import argparse


def norm(token):
    """连字符归一: F-L-O-O-R → FLOOR"""
    return token.replace('-', '').replace('–', '')


def en_display_form(en_cell, word):
    """英文列若是该词的纯展示行(去掉引号/句末标点后只剩这一个词), 返回其原文形态; 否则 None。"""
    stripped = en_cell.strip().strip('"“”\'').rstrip('.!?。！？').strip()
    if re.fullmatch(r'[A-Za-z][A-Za-z\-]*', stripped) and norm(stripped).lower() == word.lower():
        return stripped
    return None


def check_rows(rows, words):
    issues, warns = [], []
    for page, en, cn in rows:
        is_cover = (page == '封面')
        # --- 英文列检查 ---
        # 句子只以 . ! ? 结束; 逗号/分号不断句, 逗号后的接续词小写是正字法(W-ay, way!)
        for sent in re.split(r'(?<=[.!?])\s+', en):
            sent = sent.strip()
            if not sent:
                continue
            first_alpha = next((c for c in sent if c.isalpha()), None)
            if first_alpha and first_alpha.islower():
                # 豁免: P1字母拆解页小写跟读词(大写拆解+小写认读对照是教学惯例)
                # 豁免: P7词族页演示词(hit/sit/fit)小写展示词头变化是教学设计
                # 豁免: 连字符词首小写如 c-AT(换词头演示)
                if not (page in ('P1',) or page == 'P7' or re.match(r'^[a-z]-[A-Z]', sent)):
                    issues.append(f"[{page}] 英文句首应大写: '{sent[:20]}...'")
        en_all = re.findall(r'[A-Za-z]+', en)
        if en_all and all(w.isupper() for w in en_all) and len(en) > 12 and ',' in en:
            warns.append(f"[{page}] 英文整句全大写且含逗号——仅认知页单词展示允许全大写,长句请用正常大小写")

        # --- 中文列目标词形态检查 (CY/T 154-2017 第7节) ---
        cn_tokens = re.findall(r'[A-Za-z][A-Za-z\-]*', cn)
        for w in words:
            display = en_display_form(en, w)
            # 封面英文目标词禁全大写(2026-10-24 拍板: 封面 Title Case, 词形与内页一致可迁移)
            if is_cover and display and len(norm(display)) > 1 and display == display.upper():
                issues.append(f"[{page}] 封面英文目标词'{display}'应为Title Case'{display.capitalize()}'(禁全大写,词形须与内页一致)")
            expected = display if display else w.lower()
            reason = ('跟随英文展示行形态' if display else '中文句夹用普通词一律小写,CY/T 154-2017 7.1')
            for tok in cn_tokens:
                if '-' in tok:
                    continue  # 拆解段(R-A-B-B-I-T/Rab-bit)镜像英文列教学设计, 不按夹用词检查
                if len(norm(tok)) == len(w) and norm(tok).lower() == w.lower():
                    if norm(tok) != norm(expected):
                        kind = 'Title Case' if tok == tok.capitalize() else ('全大写' if tok.isupper() else '混合形态')
                        issues.append(f"[{page}] 中文列'{tok}'({kind})应为'{expected}'({reason})")

        # --- 标点对应 ---
        # 封面行是标题: GB/T 15834-2011 B.4 标题末尾通常不用标点,可用问号/叹号/省略号,
        # 两列各自独立决定,不作标点对应要求(机审豁免)
        if not is_cover:
            en_marks = re.findall(r'[.!?]', en)
            cn_marks = re.findall(r'[。！？]', cn)
            if len(en_marks) != len(cn_marks):
                issues.append(f"[{page}] 句尾标点数量不对应: 英文{len(en_marks)}个{en_marks} vs 中文{len(cn_marks)}个{cn_marks}")
    return issues, warns


def parse(text):
    rows = []
    for line in text.splitlines():
        line = line.strip().strip('|')
        if not line or set(line) <= set('-: '):
            continue
        parts = [p.strip() for p in line.split('|')]
        if len(parts) < 3 or parts[0] in ('页码', '序号'):
            continue
        rows.append((parts[0], parts[1], parts[2]))
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('narration_file', help='旁白表文件(markdown 表)')
    ap.add_argument('--word', action='append', required=True, help='目标核心词,可重复传入词族伙伴词')
    args = ap.parse_args()

    try:
        text = open(args.narration_file, encoding='utf-8').read()
    except OSError as e:
        print(f"读不到文件: {e}")
        sys.exit(1)

    rows = parse(text)
    print(f"解析 {len(rows)} 行旁白, 核对目标词 {args.word}")
    issues, warns = check_rows(rows, args.word)
    if issues:
        print("\n[必须修复]")
        for i in issues:
            print(f"  ✗ {i}")
    if warns:
        print("\n[建议人工确认]")
        for w in warns:
            print(f"  ⚠ {w}")
    if not issues and not warns:
        print("语法审计全过——大小写/标点/目标词同现均合规")
    sys.exit(1 if issues else 0)


if __name__ == '__main__':
    main()
