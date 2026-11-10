#!/usr/bin/env python3
"""校验 L4 完整目标词的拼写形态和大小写。

封面按书名，内页完整词可用词典词头形态。
用法：python3 tools/l4_case_check.py <L4 文件> --word <目标词>
"""
import sys
import re
import argparse


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
    """归一分隔符，用于识别目标词的拆写形式。"""
    return re.sub(r'[-–‑·]', '', token)


def expected_forms(word, narration, page_no, is_cover):
    """提取旁白中的完整目标词形态。"""
    forms = set()
    for m in re.finditer(r'[A-Za-z][A-Za-z–‑·-]*', narration):
        tok = m.group(0)
        if tok.lower() == word.lower():
            forms.add(tok)
    return forms


def scan_prompt_variants(word, prompt):
    """扫描提示词里目标词的全部变体, 返回 [(原文变体, 计数)]。碎片(长度<全词)已豁免。"""
    variants = {}
    wl = len(norm(word))
    for m in re.finditer(r'[A-Za-z][A-Za-z–‑·-]*', prompt):
        tok = m.group(0)
        if len(norm(tok)) != wl:
            continue  # 碎片/更长复合词豁免
        if norm(tok).lower() == norm(word).lower():
            variants[tok] = variants.get(tok, 0) + 1
    return variants


def check_page(page, page_no, words):
    """返回该页的违规列表。words: [(word, expected_forms)]"""
    issues = []
    is_cover = (page_no == '封面') or ('封面' in page['narration'][:10])
    for word, exp in words:
        for tok in scan_prompt_variants(word, page['narration']):
            if tok.lower() != word.lower():
                issues.append(f"[{page_no}] 旁白拆写了目标词 {tok!r}，请完整写作 {word}。")
        variants = scan_prompt_variants(word, page['prompt'])
        for tok, cnt in sorted(variants.items()):
            if tok.lower() != word.lower():
                issues.append(f"[{page_no}] 画面拆写了目标词 {tok!r}，请完整写作 {word}。")
                continue
            n = tok
            if n in exp:
                continue  # 与文稿形态一致
            if n == word.lower() and not is_cover:
                continue  # 全小写=词典词头形态, 非封面页放行
            kind = '全大写' if n == word.upper() else ('Title Case' if n == word.capitalize() else '混合形态')
            issues.append(
                f"[{page_no}] 画面'{tok}'×{cnt}({kind})与文稿不一致——当页旁白形态为 {sorted(exp) or '未出现'}, "
                f"{'封面页必须与文稿完全一致' if is_cover else '改为文稿形态或全小写'}"
            )
    return issues


def check_header(header, words):
    issues = []
    for word, _ in words:
        for m in re.finditer(r'[A-Za-z][A-Za-z–‑·-]*', header):
            tok = m.group(0)
            if norm(tok).lower() == norm(word).lower() and tok.lower() != word.lower():
                issues.append(f"[引导语/约定区] 拆写了目标词 {tok!r}，请完整写作 {word}。")
            elif tok == word.upper() and len(word) > 1:
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
        text = open(args.l4file, encoding='utf-8').read()
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
