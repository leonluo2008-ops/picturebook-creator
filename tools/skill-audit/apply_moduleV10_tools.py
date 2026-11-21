# ⚠️ 历史一次性补丁（2026-11-21 搬迁前布局）：docs/ 与 tools/ 已移入 picturebook-creator 仓内。
#    本脚本内的相对路径按搬迁前（工作区根）写；如需重放，把 JOBS 里的 `docs/` 改为仓内 `docs/` 的对应路径。
# -*- coding: utf-8 -*-
"""V10 批 B3/B5/B6 + G4/G6/G8 机检落地。

两路审计并集里的 6 条 P0 与 4 条门禁缺陷：
- G8 双语零机检  → l4_case_check 新增 check_bilingual()
- G4 词表零机检  → l4_structure_check 新增词表形态断言
- G6 词数零机检  → l4_structure_check 新增 2–4 个断言
- 词族页反向误杀  → l4_presence_check 存 ptype 并真跳过
- `or True` 恒真  → l4_structure_check 修死条件
- 中文列洗白大小写 → l4_case_check 取形态前按 / 切分
- CJK 相邻词界误杀 → grammar_check 改 lookaround
- 词族页豁免硬编码 P7 → grammar_check 加 --family-page
- 扫描器词表漏本批三项 → repo_legacy_scan 扩词表

用法: python apply_moduleV10_tools.py <repo_root> [--check]
"""
import io
import os
import sys

REPO = r"E:\OneDrive\工作文件夹\儿童绘本\codex-workspace\picturebook-creator"

EDITS = [
    # ══════ 1. l4_case_check.py：G8 双语 + 取形态按 / 切分 ══════
    ("tools/l4_case_check.py", "C1-取形态按斜杠切分",
     '''def expected_forms(word, narration, page_no, is_cover):
    """从当页旁白行提取目标词的文稿形态集合(原文形态 + 连字符归一形态)。"""
    forms = set()
    for m in re.finditer(r'[A-Za-z][A-Za-z\\-]*', narration):''',
     '''def expected_forms(word, narration, page_no, is_cover):
    """从当页旁白行提取目标词的文稿形态集合(原文形态 + 连字符归一形态)。

    v1.1(2026-11-21): 旁白行已是「英文 / 中文」双语, 先按 / 切出英文段再取形态;
    封面行是「封面（中文 / 英文）」, 英文在后段。不切会让中文列里的大写"洗白"画面错误。
    """
    seg = narration
    if '/' in narration:
        seg = narration.split('/')[-1] if is_cover else narration.split('/')[0]
    forms = set()
    for m in re.finditer(r'[A-Za-z][A-Za-z\\-]*', seg):'''),

    ("tools/l4_case_check.py", "C2-新增双语检查函数",
     "def check_header(header, words):",
     '''def check_bilingual(page, page_no, is_cover):
    """G8(2026-11-21 所有者裁定): L4 旁白行必须双语。

    内页: `英文 / 中文`(英文在前, 后段须含汉字);
    封面: `封面（中文 / 英文）`(中文在前, 后段须含拉丁字母)。
    """
    nar = (page.get('narration') or '').strip()
    cjk = re.compile(r'[\\u4e00-\\u9fff]')
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


def check_header(header, words):'''),

    ("tools/l4_case_check.py", "C3-接入双语检查",
     "        issues += check_page(page, page_no, words)",
     "        issues += check_bilingual(page, page_no, i == 0)\n        issues += check_page(page, page_no, words)"),

    # ══════ 2. l4_presence_check.py：存 ptype + 真跳过词族页 ══════
    ("scripts/l4_presence_check.py", "C4-解析页面类型",
     '''        m = re.match(r"^生图提示词[:：]\\s*(.*)$", s)
        if m:
            cur["prompt"] = m.group(1)
            continue
        if re.match(r"^(比例|页面类型)[:：]", s):
            continue''',
     '''        m = re.match(r"^生图提示词[:：]\\s*(.*)$", s)
        if m:
            cur["prompt"] = m.group(1)
            continue
        m2 = re.match(r"^页面类型[:：]\\s*(.*)$", s)
        if m2:
            cur["ptype"] = m2.group(1).strip()
            continue
        if re.match(r"^比例[:：]", s):
            continue'''),

    ("scripts/l4_presence_check.py", "C5-补 ptype 字段",
     '''            cur = {"narration": m.group(1), "prompt": ""}''',
     '''            cur = {"narration": m.group(1), "ptype": "", "prompt": ""}'''),

    ("scripts/l4_presence_check.py", "C6-词族页真跳过",
     '''        if "词族拓展页" in (p.get("prompt") or "") and i not in page_words:
            pass  # 词族页的判定依赖页面类型字段，见下''',
     '''        if "词族拓展页" in (p.get("ptype") or "") and i not in page_words:
            skipped.append(page_no)
            continue'''),

    # ══════ 3. l4_structure_check.py：修 or True + 加 G4/G6 ══════
    ("scripts/l4_structure_check.py", "C7-修恒真死条件",
     '''            else:
                has_word = ("目标词图形化" in pr) or True
                fam_note.append("%s 是词族拓展页，未提供 --family-words，该页词族词未机审" % no)''',
     '''            else:
                has_word = ("目标词图形化" in pr)
                fam_note.append("%s 是词族拓展页，未提供 --family-words，词族词本身未机审（仅查图形化块）" % no)'''),

    ("scripts/l4_structure_check.py", "C8-加G4词表与G6词数",
     '''            if family_words:
                miss = [w for w in family_words if not re.search(
                    r"(?<![A-Za-z])" + re.escape(w) + r"(?![A-Za-z])", pr, flags=re.I)]
                has_word = not miss
                if miss:
                    fam_note.append("%s 缺词族词：%s" % (no, "、".join(miss)))''',
     '''            # G4/G6(2026-11-21 所有者裁定)：英文列必须是词表形态，且词数 2–4
            en_seg = (p.get("narration") or "").split("/")[0].strip()
            if en_seg:
                word_list_ok = re.fullmatch(
                    r"[A-Za-z][A-Za-z'\\-]*(?:\\s*[,，]\\s*[A-Za-z][A-Za-z'\\-]*)*\\.?", en_seg)
                if not word_list_ok:
                    issues.append("[%s] 词族页英文列不是词表形态（G4：只许逗号分隔的单词，"
                                  "不许句子/引导句）：%r" % (no, en_seg[:50]))
                else:
                    n_fam = len([x for x in re.split(r"[,，]", en_seg.rstrip(".")) if x.strip()])
                    if n_fam < 2 or n_fam > 4:
                        issues.append("[%s] 词族页词数 %d 个，应为 2–4 个（G6：常规 2–3、最多 4）"
                                      % (no, n_fam))
            if family_words:
                miss = [w for w in family_words if not re.search(
                    r"(?<![A-Za-z])" + re.escape(w) + r"(?![A-Za-z])", pr, flags=re.I)]
                has_word = not miss
                if miss:
                    fam_note.append("%s 缺词族词：%s" % (no, "、".join(miss)))'''),

    # ══════ 4. grammar_check.py：CJK 词界 + 词族页参数化 ══════
    ("tools/grammar_check.py", "C9-CJK词界",
     '''            if re.search(r'\\b' + re.escape(w.lower()) + r'\\b', en_low) and not is_cover:
                if not re.search(r'\\b' + re.escape(w.lower()) + r'\\b', cn.lower()):''',
     '''            # 2026-11-21: CJK 在 Python re 里属 \\w，`\\bpot\\b` 在「小锅pot坐」这种紧贴汉字处失效
            _pat = r'(?<![A-Za-z])' + re.escape(w.lower()) + r'(?![A-Za-z])'
            if re.search(_pat, en_low) and not is_cover:
                if not re.search(_pat, cn.lower()):'''),

    ("tools/grammar_check.py", "C10-词族页参数化",
     "                if not (page in ('P1',) or page == 'P7' or re.match(r'^[a-z]-[A-Z]', sent)):",
     "                if not (page in ('P1',) or page == FAMILY_PAGE or re.match(r'^[a-z]-[A-Z]', sent)):"),

    ("tools/grammar_check.py", "C11b-词族页全局默认",
     "import argparse",
     'import argparse\n\nFAMILY_PAGE = \'P7\'  # 词族拓展页在旁白表里的页号；内页数变化时用 --family-page 覆盖'),

    ("tools/grammar_check.py", "C11c-加family-page参数",
     "    args = ap.parse_args()",
     "    ap.add_argument('--family-page', default='P7', help='词族拓展页的页号(默认 P7；内页更多时按实际传)')\n"
     "    args = ap.parse_args()\n"
     "    global FAMILY_PAGE\n"
     "    FAMILY_PAGE = args.family_page"),

    # ══════ 5. repo_legacy_scan.py：词表补本批三项 ══════
    ("tools/repo_legacy_scan.py", "C11-扫描词表扩容",
     '''    "每页必须标注", "huiben-v2", "硬上限 15 词", "超过10个英文词",''',
     '''    "每页必须标注", "huiben-v2", "硬上限 15 词", "超过10个英文词",
    "短句串联",  # 2026-11-21 G4 翻案：词族页英文列改为词表，此口径已废'''),
]


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else REPO
    check_only = "--check" in sys.argv
    bad = []
    for rel, rid, old, new in EDITS:
        p = os.path.join(root, rel.replace("/", os.sep))
        t = io.open(p, encoding="utf-8").read()
        n = t.count(old)
        print("%-28s %-34s 命中 %d %s" % (rid, rel, n, "" if n == 1 else "<<< 需查"))
        if n == 1 and not check_only:
            io.open(p, "w", encoding="utf-8", newline="").write(t.replace(old, new))
        if n != 1:
            bad.append(rid)
    print("\n%s：成功 %d / 未命中 %d" % ("[check 未写盘]" if check_only else "[完成]", len(EDITS) - len(bad), len(bad)))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
