#!/usr/bin/env python3
"""领读绘本旁白表 · 中英大小写语法审计器 v1.1 (2026-10-24 参数化重写)

检查中英旁白表的大小写语法：
1. 英文列：句首字母必须大写；全大写长句仅限单词展示页；封面英文目标词禁全大写(应 Title Case)
2. 中文列：目标词形态跟随规则（CY/T 154-2017 第7节）
   - 英文列是纯展示行(如 Floor / Learn "way") → 中文列跟随同形态
   - 封面行(书名)整行按展示性文本处理 → 中文列跟随书名里目标词的形态(书名写 Towel, 中文列就写 Towel)
   - 其余(句子夹用, 含 P1 拆解行) → 中文列一律小写(7.1 普通词不承担英文句首大写)
3. 句尾标点中英对应（. ! ? → 。！？）
4. 中文列核心词落点（2026-11-25 所有者裁定，rules.md §六）：中文内页旁白里的完整核心词/词组
   必须放在所在句的句尾或作独立句末认读语；核心词后同句仍接中文句意即违规。
   直接扫中文列实际用词——英文列没出现核心词的页同样要查。封面行与词族拓展页豁免
   （封面按标题规范；词族页中文列是「拓展词+释义」串，另有自己的规则）。
5. 认读处中文释义（2026-11-26 所有者裁定，rules.md §六）：传入 --gloss 时，中文内页旁白
   凡用英文核心词承担认读，该格中文必须说出本书已确认的中文释义（逐字）——
   纯指代（「快看，keyboard！」）替代释义 = 孩子不念英文字就不知道指的是什么。
   机检只查可确定的部分（同格含释义）；「紧接的中文认读语境算不算听懂」属自然度，
   留给收稿复核（flow.md §4）人工裁决。封面行与词族拓展页豁免。
   未传 --gloss 时跳过本项并打印提示——正式收稿应传入台账「中文释义」。

用法: python3 grammar_check.py <旁白表.txt> --word floor [--word door] [--gloss 地板]
输入格式: | 页码 | 英文 | 中文 |
退出码: 0=全过  1=有违规或读不到文件  2=参数错误 / 解析到 0 行旁白
"""
import sys
import re
import argparse
# ── 词形口径：与其它门禁共用 tools/wordforms.py（2026-11-21）──
import os as _os, sys as _sys
_HERE = _os.path.dirname(_os.path.abspath(__file__))
for _p in (_HERE, _os.path.join(_HERE, '..', 'tools')):
    if _os.path.isfile(_os.path.join(_p, 'wordforms.py')):
        _sys.path.insert(0, _os.path.abspath(_p))
        break
from wordforms import word_forms, forms_pattern, upper_forms


FAMILY_PAGE = 'P7'  # 词族拓展页在旁白表里的页号；内页数变化时用 --family-page 覆盖


def norm(token):
    """连字符归一: F-L-O-O-R → FLOOR"""
    return token.replace('-', '').replace('–', '')


def en_display_form(en_cell, word, is_cover=False):
    """英文列若是该词的纯展示行(去掉引号/句末标点后只剩这一个词), 返回其原文形态; 否则 None。

    封面行例外: 书名整行是展示性文本(读者直接看到的标题), 目标词在书名里的写法
    就是中文列该跟随的形态——书名写 A Soft Towel, 中文列就写 Towel。
    """
    stripped = en_cell.strip().strip('"“”\'').rstrip('.!?。！？').strip()
    if re.fullmatch(r'[A-Za-z][A-Za-z\-]*', stripped) and norm(stripped).lower() in word_forms(word):
        return stripped
    if is_cover:
        for m in re.finditer(r'[A-Za-z][A-Za-z\-]*', en_cell):
            tok = m.group(0)
            if norm(tok).lower() in word_forms(word):
                return tok
    return None


def _is_wordlist(en):
    """词族页英文列形态：逗号分隔的纯单词条目（≥2 个），无句子结构。"""
    tokens = [x.strip() for x in re.sub(r'[.!?。！？]+$', '', en.strip()).split(',')]
    return len(tokens) >= 2 and all(re.fullmatch(r'[A-Za-z][A-Za-z\-]*', x) for x in tokens if x)


def check_rows(rows, words, glosses=None):
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
                if not (page in ('P1',) or page == FAMILY_PAGE or re.match(r'^[a-z]-[A-Z]', sent)):
                    issues.append(f"[{page}] 英文句首应大写: '{sent[:20]}...'")
        en_all = re.findall(r'[A-Za-z]+', en)
        if en_all and all(w.isupper() for w in en_all) and len(en) > 12 and ',' in en:
            warns.append(f"[{page}] 英文整句全大写且含逗号——仅认知页单词展示允许全大写,长句请用正常大小写")

        # --- 中文列目标词形态检查 (CY/T 154-2017 第7节) ---
        cn_tokens = re.findall(r'[A-Za-z][A-Za-z\-]*', cn)
        for w in words:
            display = en_display_form(en, w, is_cover)
            # 封面英文目标词禁全大写(2026-10-24 拍板: 封面 Title Case, 词形与内页一致可迁移)
            if is_cover and display and len(norm(display)) > 1 and display == display.upper():
                issues.append(f"[{page}] 封面英文目标词'{display}'应为Title Case'{display.capitalize()}'(禁全大写,词形须与内页一致)")
            expected = display if display else w.lower()
            reason = ('跟随英文展示行形态' if display else '中文句夹用普通词一律小写,CY/T 154-2017 7.1')
            for tok in cn_tokens:
                if '-' in tok:
                    continue  # 拆解段(R-A-B-B-I-T/Rab-bit)镜像英文列教学设计, 不按夹用词检查
                if norm(tok).lower() in word_forms(w):
                    # 只判「大小写」：有英文展示行就跟随其形态；没有则要求全小写（词形可以是任意屈折形）
                    want = norm(display) if display else norm(tok).lower()
                    if norm(tok) != want:
                        kind = 'Title Case' if tok == tok.capitalize() else ('全大写' if tok.isupper() else '混合形态')
                        issues.append(f"[{page}] 中文列'{tok}'({kind})应为'{want}'({reason})")

        # --- 目标词双语同现检查(硬闸) ---
        # 英文列含目标词的行, 中文列必须同现目标词——词义双关是领读绘本的核心机制,
        # 词在中文里消失等于这页没教(better/fast/P8互动页均踩过此坑)
        en_low = en.lower()
        for w in words:
            # 2026-11-21: CJK 在 Python re 里属 \w，`\bpot\b` 在「小锅pot坐」这种紧贴汉字处失效
            # 2026-11-21 修：英文按语法写复数（coins）时也要触发同现检查，
            # 否则「中文列丢了目标词」的行会整行不被检查却打印『同现均合规』
            _pat = forms_pattern(w)
            if re.search(_pat, en_low) and not is_cover:
                if not re.search(_pat, cn.lower()):
                    issues.append(f"[{page}] 英文列含目标词'{w}'但中文列未出现——目标词双语同现缺失(领读核心机制)")


        # --- 中文列核心词落点检查(硬闸, 2026-11-25 rules.md §六) ---
        # 完整核心词/词组必须放所在句句尾或作独立句末认读语;
        # 核心词后同句仍接中文句意 → 违规。直接扫中文列, 英文列没词也查。
        # 词族页豁免仅当该页英文列确实是词表（默认页号 P7 可用 --family-page 覆盖;
        # 非词表的 P7 是普通语境页, 照查）。
        if not is_cover and not (page == FAMILY_PAGE and _is_wordlist(en)):
            for w in words:
                for m in re.finditer(forms_pattern(w), cn.lower()):
                    tail = cn[m.end():]
                    endm = re.search(r'[。！？!?]', tail)
                    seg = tail[:endm.end()] if endm else tail
                    if re.search(r'[\u4e00-\u9fff]', seg):
                        issues.append(
                            f"[{page}] 中文列核心词'{w}'后同句仍接中文句意——完整核心词"
                            f"必须放句尾或作独立句末认读语(rules.md §六): '…{cn[max(0, m.start()-6):m.end()+8]}…'")

        # --- 认读处中文释义检查(硬闸, 2026-11-26 所有者裁定, rules.md §六) ---
        # 中文内页旁白用英文核心词承担认读时, 该格中文必须说出本书已确认的中文释义——
        # 纯指代(「快看,keyboard!」「就是这个」)替代释义 = 不念英文字就不知道指的是什么。
        # 机检只做可确定的部分: 同一格必须含释义逐字; 邻句/图文语境是否算「听懂」
        # 属自然度判断, 留给收稿复核(flow.md §4)人工裁决。
        # 封面行豁免(按标题规范); 词族页豁免(拓展词逐一配释义, 另有规则)。
        if glosses and not is_cover and not (page == FAMILY_PAGE and _is_wordlist(en)):
            for w in words:
                if re.search(forms_pattern(w), cn.lower()) and not any(g in cn for g in glosses):
                    issues.append(
                        f"[{page}] 中文列核心词'{w}'认读处缺已确认中文释义({'/'.join(glosses)})"
                        f"——纯指代不能替代释义, 这句须说出释义(rules.md §六): '{cn}'")

        # --- 标点对应 ---
        # 封面行是标题: GB/T 15834-2011 B.4 标题末尾通常不用标点(豁免)。
        # 正文行也只做软提醒不当硬闸: 中英文句界不一一对应是常态
        # (英文两句中文一句流水更顺口), 逐句断句节奏由 L3.5 口语门禁(人声朗读)裁决。
        if not is_cover:
            en_marks = re.findall(r'[.!?]', en)
            cn_marks = re.findall(r'[。！？]', cn)
            if len(en_marks) != len(cn_marks):
                warns.append(f"[{page}] 中英句末标点数不对应(英文{len(en_marks)} vs 中文{len(cn_marks)})——仅提示,读着顺口就不改")
    return issues, warns


def parse(text):
    rows = []
    for line in text.splitlines():
        line = line.strip().strip('|')
        if not line or set(line) <= set('-:| '):  # markdown 分隔行 |---| 剥掉两端竖线后仍含 |，必须一起豁免
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
    ap.add_argument('--gloss', action='append',
                    help='本书已确认中文释义(台账「中文释义」列,如 键盘);传入即启用「认读处中文释义」硬闸')
    ap.add_argument('--family-page', default='P7', help='词族拓展页的页号(默认 P7；内页更多时按实际传)')
    args = ap.parse_args()
    global FAMILY_PAGE
    FAMILY_PAGE = args.family_page

    try:
        text = open(args.narration_file, encoding='utf-8-sig').read()
    except OSError as e:
        print(f"读不到文件: {e}")
        sys.exit(1)

    rows = parse(text)
    print(f"解析 {len(rows)} 行旁白, 核对目标词 {args.word}")
    if args.gloss:
        print(f"启用认读处中文释义检查: 释义={args.gloss}")
    else:
        print("未传 --gloss：跳过「认读处中文释义」检查（正式收稿应传入台账中文释义, rules.md §六）")
    if not rows:
        print("没解析到任何旁白行（检查是否为 `| 页码 | 英文 | 中文 |` 的 markdown 表格）——"
              "此时没有任何校验，不能报通过")
        sys.exit(2)
    issues, warns = check_rows(rows, args.word, glosses=args.gloss)
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

