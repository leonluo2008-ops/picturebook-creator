#!/usr/bin/env python3
"""L4 生图提示词 · 画面文字形态门禁 v1.0 (2026-10-24)

总纲: 画面上出现的每一个英文单词, 大小写形态必须与当页旁白文稿完全一致。
不禁止全大写——全大写只出现在文稿本身就是全大写的页(P1 字母拆解);
文稿是小写的词, 画面就不许变成全大写。

检查逻辑:
1. 解析 L4 的页面记录(旁白: / 比例: / 页面类型: / 生图提示词:)
2. 每页从旁白行提取目标词的文稿形态集合(如 water → {water}; W-A-T-E-R, water! → {WATER, water})
3. 扫描同页生图提示词里目标词的全部大小写变体, 逐一比对:
   - 与文稿形态一致(连字符归一后) → 通过
   - 全小写 → 通过(词典词头形态, 独立展示标签的标准形态)
   - 全大写/Title Case/混合形态, 且不在文稿形态里 → 违规
   - 封面页从宽到严: 只认文稿形态(封面英文标题列即文稿), 不给全小写豁免
4. 引导语+全局约定区(第一个「旁白:」之前)出现全大写目标词 → 违规
5. 词长不足全词的碎片(逐字母标色描述里的 loor / Rab 等)自动豁免

用法:
  python3 l4_case_check.py <L4文件> --word water
  python3 l4_case_check.py <L4文件> --word floor --word door   # 词族伙伴词可多次

退出码: 0=全过  1=有违规(按输出逐页修复后重跑)
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



def parse_pages(text):
    """把 L4 文本切成 (header, [page_dict])。页面记录以「旁白: 」行开始。"""
    lines = text.splitlines()
    pages = []
    header_lines = []
    cur = None
    for line in lines:
        m_nar = re.match(r'^旁白[:：]\s*(.*)$', line.strip())
        m_ratio = re.match(r'^比例[:：]\s*(.*)$', line.strip())
        m_type = re.match(r'^页面类型[:：]\s*(.*)$', line.strip())
        m_prompt = re.match(r'^生图提示词[:：]\s*(.*)$', line.strip())
        if m_nar:
            cur = {'narration': m_nar.group(1).strip(), 'ratio': '', 'ptype': '', 'prompt_lines': []}
            pages.append(cur)
        elif cur is None:
            header_lines.append(line)
        else:
            if m_ratio:
                cur['ratio'] = m_ratio.group(1).strip()
            elif m_type:
                cur['ptype'] = m_type.group(1).strip()
            elif m_prompt:
                cur['prompt_lines'].append(m_prompt.group(1).strip())
            else:
                cur['prompt_lines'].append(line.strip())
    header = '\n'.join(header_lines)
    for p in pages:
        p['prompt'] = '\n'.join(x for x in p['prompt_lines'] if x)
    return header, pages


def norm(token):
    """连字符归一: W-A-T-E-R → WATER"""
    return token.replace('-', '').replace('–', '')


def _word_forms(word):
    """核心词的可接受词形——统一走 tools/wordforms.py（原形/s/es/ies/ves/不规则/同形）。"""
    return word_forms(word)


def expected_forms(word, narration, page_no, is_cover):
    """从当页旁白行提取目标词的文稿形态集合(原文形态 + 连字符归一形态)。

    v1.1(2026-11-21): 旁白行已是「英文 / 中文」双语, 先按 / 切出英文段再取形态;
    封面行是「封面（中文 / 英文）」, 英文在后段。不切会让中文列里的大写"洗白"画面错误。
    """
    seg = narration
    if '/' in narration:
        seg = narration.split('/')[-1] if is_cover else narration.split('/')[0]
    forms = set()
    for m in re.finditer(r'[A-Za-z][A-Za-z\-]*', seg):
        tok = m.group(0)
        if norm(tok).lower() in _word_forms(word):
            forms.add(norm(tok))
    return forms


def scan_prompt_variants(word, prompt):
    """扫描提示词里目标词的全部变体, 返回 [(原文变体, 计数)]。碎片(长度<全词)已豁免。"""
    variants = {}
    wl = len(word)
    for m in re.finditer(r'[A-Za-z][A-Za-z\-]*', prompt):
        tok = m.group(0)
        if norm(tok).lower() not in _word_forms(word):
            continue  # 碎片/更长复合词/其它词豁免（含单复数）
        if True:
            variants[tok] = variants.get(tok, 0) + 1
    return variants


def check_page(page, page_no, words):
    """返回该页的违规列表。words: [(word, expected_forms)]"""
    issues = []
    is_cover = (page_no == '封面') or ('封面' in page['narration'][:10])
    for word, exp in words:
        variants = scan_prompt_variants(word, page['prompt'])
        for tok, cnt in sorted(variants.items()):
            n = norm(tok)
            if n in exp:
                continue  # 与文稿形态一致
            if n == n.lower() and n.lower() in _word_forms(word) and not is_cover:
                continue  # **全小写**才放行（缺 n==n.lower() 会让内页检查恒真，2026-11-21 修）
            kind = '全大写' if n == word.upper() else ('Title Case' if n == word.capitalize() else '混合形态')
            issues.append(
                f"[{page_no}] 画面'{tok}'×{cnt}({kind})与文稿不一致——当页旁白形态为 {sorted(exp) or '未出现'}, "
                f"{'封面页必须与文稿完全一致' if is_cover else '改为文稿形态或全小写'}"
            )
    return issues


def check_bilingual(page, page_no, is_cover):
    """G8(2026-11-21 所有者裁定): L4 旁白行必须双语。

    内页: `英文 / 中文`(英文在前, 后段须含汉字);
    封面: `封面（中文 / 英文）`(中文在前, 后段须含拉丁字母)。
    """
    nar = (page.get('narration') or '').strip()
    cjk = re.compile(r'[\u4e00-\u9fff]')
    lat = re.compile(r'[A-Za-z]')
    out = []
    if is_cover:
        if not nar.startswith('封面'):
            return [f"[{page_no}] 封面旁白行应以「封面（中文标题 / 英文标题）」开头, 实际: {nar[:30]}"]
        if nar.count('/') != 1:
            return [f"[{page_no}] 封面旁白行应有且仅有一个 '/' 分隔中英: {nar[:40]}"]
        left, right = nar.split('/', 1)
        if not cjk.search(left):
            out.append(f"[{page_no}] 封面旁白 '/' 前(中文标题)未出现汉字: {nar[:40]}")
        if not lat.search(right):
            out.append(f"[{page_no}] 封面旁白 '/' 后(英文标题)未出现拉丁字母: {nar[:40]}")
        if cjk.search(right):
            out.append(f"[{page_no}] 封面旁白 '/' 后应为英文书名，却含汉字: {right.strip()[:30]}")
        return out
    if nar.count('/') != 1:
        return [f"[{page_no}] 旁白行必须是「英文 / 中文」双语(G8 裁定, 纯英文不合规), 实际: {nar[:50]}"]
    left, right = nar.split('/', 1)
    if cjk.search(left):
        out.append(f"[{page_no}] 旁白 '/' 前应为英文(G8: 英文在前), 却含汉字: {left.strip()[:30]}")
    if not lat.search(left):
        out.append(f"[{page_no}] 旁白 '/' 前未出现英文: {nar[:40]}")
    if not cjk.search(right):
        out.append(f"[{page_no}] 旁白 '/' 后应为中文, 却未出现汉字: {right.strip()[:30]}")
    return out


def check_header(header, words):
    issues = []
    for word, _ in words:
        for m in re.finditer(r'[A-Za-z][A-Za-z\-]*', header):
            tok = m.group(0)
            if norm(tok) in upper_forms(word):
                ctx = header[max(0, m.start() - 15):m.end() + 10].replace('\n', ' ')
                issues.append(f"[引导语/约定区] 全大写'{tok}'——目标词在引导语里也须按约定形态(小写)书写: …{ctx}…")
    return issues


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('l4file', help='L4 生图提示词纯文本文件')
    ap.add_argument('--word', action='append', required=True,
                    help='目标核心词(可重复传入词族伙伴词)')
    args = ap.parse_args()

    try:
        text = open(args.l4file, encoding='utf-8-sig').read()
    except OSError as e:
        print(f"读不到文件: {e}")
        sys.exit(1)

    header, pages = parse_pages(text)
    if not pages:
        print("没解析到任何页面记录(应以「旁白: 」行开始)")
        sys.exit(1)

    issues = []
    checked = 0
    for i, page in enumerate(pages):
        page_no = '封面' if i == 0 else f"P{i}"
        words = [(w, expected_forms(w, page['narration'], page_no, i == 0)) for w in args.word]
        # 全部页面都从旁白行取形态; 旁白没出现该词的页, 该词任何全大写/Title Case变体都会被拦
        issues += check_bilingual(page, page_no, i == 0)
        issues += check_page(page, page_no, words)
        checked += 1
    issues += check_header(header, [(w, None) for w in args.word])

    print(f"解析 {len(pages)} 页 + 引导语区, 核对目标词 {args.word}")
    if issues:
        print(f"\n[必须修复] {len(issues)} 处")
        for x in issues:
            print(f"  ✗ {x}")
        sys.exit(1)
    print("画面文字形态全过——每页字母大小写与当页旁白文稿一致")
    sys.exit(0)


if __name__ == '__main__':
    main()

