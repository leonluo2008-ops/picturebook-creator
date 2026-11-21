#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L4 结构门禁 v2.0 —— 块存在性 / 每页词数 / 构图三要素 / 比例 / 页面类型 / Pn 前缀

这是**自检工具**，严格于「交稿门禁」：SKILL v13 明确「安全区第 3 要素不作为交付门禁，只做人工核」，
本脚本把它做成硬断言，用于自我把关；是否把它并入强制门禁由所有者决定。

v2.0 相对 v1.0 的修改（依据 2026-11-21 双路行为审计）：
- **构图三要素**改为在整段提示词里查，**不再要求写在「构图要求」之后**（SKILL 规定块序软）；
  第 3 要素改为 `背景…(边缘|填充|铺边)` 同句判定 —— v1 只查裸子串「边缘」，
  既放过「不得触碰或压到画面的边缘」（假阴），又误杀「自然延伸填充到画面四边」（假阳）
- **目标词图形化块不再短路**：v1 用 `("目标词图形化" in pr) or (word in pr)`，
  导致 `--word zzz` 也能全过；v2 只认块名（词族拓展页按词族词判定）
- 词族拓展页与 presence 同口径：未给 `--family-words` 时提示并按词族词规则放行，不再静默判红
- 场景一致性接受「场景一致性」或「场景锚点」（SKILL 二者二选一）
- 词数口径修正：剥 `^P\\d+` 前缀；封面取 `/` 后的英文段（v1 取到中文段，书名从不计数）
- 比例归一化比较（`3:4` / `3：4` / `3:4（竖版）` 都认）
- Pn 前缀正则改 `^[Pp]\\d+`（v1 只认 `P1 `，漏全角冒号与无空格形态）
- 封面页型必须是「认知页」（否则记一条 issue、exit 1），第 0 页必须识别为封面（否则 exit 2；v1 默认第 0 页就是封面）
- 页数断言 `--expect-pages`；全量剥离 `\\ufeff`；`UnicodeDecodeError` 归 2
- 退出码契约：0=过 / 1=有违规 / 2=输入或参数错误
- `--max-words` 只允许 ≤10（SKILL 硬上限），超出则 clamp 并告警

覆盖说明：块存在性只覆盖「六类 + 构图要求」里可机检的 **4 项**（目标词图形化 / 角色一致性 / 场景一致性 / 构图要求）；
镜头类型、场景描述、风格锚点不在此脚本断言范围内。

用法:
  python3 l4_structure_check.py <L4文件> --word coin [--expect-pages 9] [--family-words hot,dot,cot]
退出码: 0=过  1=有违规  2=输入/参数错误
"""
import argparse
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
except Exception:
    pass

PAGE_TYPES = {"认知页", "语境页", "词族拓展页", "互动练习页"}
PN = re.compile(r"^[Pp]\d+")
RATIO = re.compile(r"(\d+)\s*[:：]\s*(\d+)")
BG_EDGE = re.compile(r"背景[^。;；]{0,40}?(边缘|填充|铺边)")


def parse_pages(text):
    text = text.replace("\ufeff", "")
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


def english_for_count(narration, is_cover):
    s = (narration or "").strip()
    s = PN.sub("", s).strip()
    if is_cover:
        # 封面行形如「封面（中文标题 / 英文标题）」：取最后一个 / 之后
        if "/" in s:
            s = s.split("/")[-1]
        s = re.sub(r"^封面[（(]", "", s)
    else:
        if "/" in s:
            s = s.split("/")[0]
    return s


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("l4file")
    ap.add_argument("--word", required=True, help="目标核心词（本脚本只接受单词）")
    ap.add_argument("--max-words", type=int, default=10)
    ap.add_argument("--family-words", default="", help="词族拓展页应出现的词族词（逗号分隔）")
    ap.add_argument("--expect-pages", type=int, default=0)
    ap.add_argument("--no-cover", action="store_true", help="允许第 0 页不是封面（跳过封面专属断言）")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    family_words = [w.strip() for w in args.family_words.split(",") if w.strip()]
    max_words = args.max_words
    if max_words > 10:
        print("提示：--max-words %d 超过 SKILL 硬上限 10，已按 10 判定。" % max_words)
        max_words = 10
    if max_words < 1:
        print("--max-words 必须 ≥1")
        return 2

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
        print("没解析到页面记录（应以「旁白: 」行开始）")
        return 2
    if args.expect_pages and len(pages) != args.expect_pages:
        print("页数不符：解析到 %d 页，期望 %d 页。" % (len(pages), args.expect_pages))
        return 1
    if not args.no_cover and not pages[0]["narration"].strip().startswith("封面"):
        print("第 0 页不是封面（旁白：%r）。若本书 L4 不含封面记录，请加 --no-cover。" % pages[0]["narration"][:30])
        return 2

    issues, rows, fam_note = [], [], []
    for i, p in enumerate(pages):
        no = "封面" if (i == 0 and not args.no_cover) else "P%d" % i
        pr = p.get("prompt") or ""
        ptype = (p.get("ptype") or "").strip()
        words = len(re.findall(r"[A-Za-z][A-Za-z'\-]*", english_for_count(p.get("narration"), i == 0)))
        has_role = "角色一致性" in pr
        has_scene = ("场景一致性" in pr) or ("场景锚点" in pr)
        has_comp = "构图要求" in pr
        safety = {"80%": "80%" in pr, "10%": "10%" in pr, "背景铺边": bool(BG_EDGE.search(pr))}
        is_family = "词族拓展页" in ptype
        if is_family:
            if family_words and len(family_words) < 2:
                issues.append("[%s] 传了 %d 个词族词——词族页至少要 2 个同族词，否则名不副实（存量 B261 cloud 只有 1 个词）" % (no, len(family_words)))
            # G4/G6(2026-11-21 所有者裁定)：英文列必须是词表形态，且词数 2–4
            en_seg = (p.get("narration") or "").split("/")[0].strip()
            if en_seg:
                word_list_ok = re.fullmatch(
                    r"[A-Za-z][A-Za-z'\-]*(?:\s*[,，]\s*[A-Za-z][A-Za-z'\-]*)*\.?", en_seg)
                if not word_list_ok:
                    issues.append("[%s] 词族页英文列不是词表形态（G4：只许逗号分隔的单词，"
                                  "不许句子/引导句）：%r" % (no, en_seg[:50]))
                else:
                    toks = [x.strip().lower() for x in re.split(r"[,，]", en_seg.rstrip(".")) if x.strip()]
                    n_fam = len(toks)
                    if n_fam < 2 or n_fam > 4:
                        issues.append("[%s] 词族页词数 %d 个，应为 2–4 个（G6：常规 2–3、最多 4）"
                                      % (no, n_fam))
                    # R8（2026-11-21 所有者裁定「首音族不要」）：词族词必须共享同一词尾 ≥2 字符
                    if n_fam >= 2:
                        _suf = toks[0]
                        for _t in toks[1:]:
                            _i = 0
                            while _i < min(len(_suf), len(_t)) and _suf[-1 - _i] == _t[-1 - _i]:
                                _i += 1
                            _suf = _suf[len(_suf) - _i:] if _i else ""
                        if len(_suf) < 2:
                            issues.append("[%s] 词族页不是同尾族（共同词尾 %r，需 ≥2 字符）：%s"
                                          "——首音族不采用（2026-11-21 裁定）" % (no, _suf, en_seg[:40]))
            if family_words:
                miss = [w for w in family_words if not re.search(
                    r"(?<![A-Za-z])" + re.escape(w) + r"(?![A-Za-z])", pr, flags=re.I)]
                has_word = not miss
                if miss:
                    fam_note.append("%s 缺词族词：%s" % (no, "、".join(miss)))
            else:
                has_word = ("目标词图形化" in pr)
                fam_note.append("%s 是词族拓展页，未提供 --family-words，词族词本身未机审（仅查图形化块）" % no)
        else:
            # 双条件：既有「目标词图形化」块，页内也真的出现该词字面（v1 有块即短路，--word 传错也过）
            word_present = re.search(r"(?<![A-Za-z])" + re.escape(args.word) + r"(?![A-Za-z])",
                                      pr, flags=re.I) is not None
            has_word = ("目标词图形化" in pr) and word_present

        rows.append((no, p.get("ratio", ""), ptype, words, has_role, has_scene, has_comp, safety, has_word))

        want = (3, 4) if no == "封面" else (16, 9)
        m = RATIO.search(p.get("ratio") or "")
        got = (int(m.group(1)), int(m.group(2))) if m else None
        if got != want:
            issues.append("[%s] 比例 %r，应为 %d:%d" % (no, p.get("ratio"), want[0], want[1]))
        if PN.match(ptype):
            issues.append("[%s] 页面类型带 Pn 前缀：%r" % (no, ptype))
        elif ptype not in PAGE_TYPES:
            issues.append("[%s] 页面类型 %r 不在词表" % (no, ptype))
        if no == "封面" and ptype and ptype != "认知页":
            issues.append("[%s] 封面页面类型应为「认知页」，实际 %r" % (no, ptype))
        if not has_role:
            issues.append("[%s] 缺「角色一致性」块" % no)
        if not has_scene:
            issues.append("[%s] 缺「场景一致性 / 场景锚点」" % no)
        if not has_comp:
            issues.append("[%s] 缺「构图要求」" % no)
        else:
            miss = [k for k, v in safety.items() if not v]
            if miss:
                issues.append("[%s] 构图要求缺：%s" % (no, "、".join(miss)))
        if words > max_words:
            issues.append("[%s] 每页英文 %d 词 > 硬上限 %d" % (no, words, max_words))
        if not has_word:
            issues.append("[%s] 缺「目标词图形化」块" % no)
        if PN.match((p.get("narration") or "").strip()):
            issues.append("[%s] 旁白行带 Pn 前缀" % no)

    if not args.quiet:
        print("解析 %d 页；自检项：块存在性(六类 + 构图要求里 4 项) / 词数≤%d / 构图三要素 / 比例 / 页面类型 / Pn 前缀"
              % (len(pages), max_words))
        print("| 页 | 比例 | 页面类型 | 词数 | 角色 | 场景 | 构图 | 80% | 10% | 背景铺边 | 目标词 |")
        print("|---|---|---|---|---|---|---|---|---|---|---|")
        for no, ratio, ptype, words, r1, r2, r3, safe, hw in rows:
            tick = lambda b: "✓" if b else "✗"
            print("| %s | %s | %s | %d | %s | %s | %s | %s | %s | %s | %s |" % (
                no, ratio, ptype, words, tick(r1), tick(r2), tick(r3),
                tick(safe["80%"]), tick(safe["10%"]), tick(safe["背景铺边"]), tick(hw)))
        for n in fam_note:
            print("  · " + n)

    if issues:
        print("\n[必须修复] %d 处" % len(issues))
        for x in issues:
            print("  ✗ " + x)
        return 1

    # ── 全书级硬约束（v2.1 补：审计列出「SKILL 有、脚本没查」中可机检的三条）──
    inner = len(pages) - (0 if args.no_cover else 1)
    book_issues, book_notes = [], []
    if not 8 <= inner <= 16:
        book_issues.append("内页数 %d 不在 8–16 页区间（SKILL「内页 8-16 页」）" % inner)

    word_total = 0
    wpat = re.compile(r"(?<![A-Za-z])" + re.escape(args.word) + r"(?:s|es)?(?![A-Za-z])", re.I)
    for i, p in enumerate(pages):
        en = english_for_count(p.get("narration"), i == 0)
        word_total += len(wpat.findall(en))
    if word_total < 8:
        book_issues.append("目标词全书只出现 %d 次（按原形+复数计），SKILL 要求 ≥8 次" % word_total)

    cn_lens, cn_missing = [], 0
    for i, p in enumerate(pages):
        if i == 0 and not args.no_cover:
            continue
        nar = (p.get("narration") or "").strip()
        if "/" not in nar:
            cn_missing += 1
            continue
        cn = nar.split("/", 1)[1]
        cn = re.sub(r"[，。！？、；：「」（）\"'…\s]", "", cn)
        n = len(re.findall(r"[\u4e00-\u9fff]", cn))
        cn_lens.append(n)
        if n > 30:
            book_issues.append("[P%d] 中文旁白 %d 字，超过 30 字硬上限" % (i, n))
        elif not 8 <= n <= 14:
            book_notes.append("[P%d] 中文旁白 %d 字，超出建议区间 8–14（软提示）" % (i, n))

    print("\n-- 全书级约束 --")
    print("  内页数 %d（要求 8–16）；目标词全书 %d 次（原形+复数，要求 ≥8）" % (inner, word_total))
    if cn_lens:
        print("  中文内页字数 %d–%d（硬上限 30）" % (min(cn_lens), max(cn_lens)))
    if cn_missing:
        print("  · 有 %d 页 L4 旁白行不含中文列（纯英文形态）——中文句长请到旁白表上核，本脚本不判" % cn_missing)
    for n in book_notes:
        print("  · " + n)
    if book_issues:
        print("\n[必须修复] %d 处（全书级）" % len(book_issues))
        for x in book_issues:
            print("  ✗ " + x)
        return 1

    print("\n结构门禁全过（自检口径，严格于交付门禁）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
