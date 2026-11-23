#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""标题 / 简介判据检查（族2 + 族1）—— 补「标题与简介无任何机检」的缺口。

判据来自 29 本语料盘点（`docs/证据-29本盘点.md`）：
- 标题：英文含核心词、中文列含目标词形态、无括注、无方法论禁词、含词后 ≤12 字
- 简介：目标词恰好 1 次、首句不以场景词开头、无禁词、单句 ≤30 字

R13（2026-11-22 所有者裁定）新增三条，只在传了 `--gloss` / `--pos` 时执行：
- G1 中文列必须含台账「中文释义」逐字（释义丢了 = 义项教不上）
- G2 去掉释义与核心词后，中文字符只许落在量词/口语虚词白名单（多出实词 = 语义扩充或第二核心词）
- P1 词型非动作类时，英文不得用核心词的动词屈折形或祈使尾（`Fan it!` / `Fanning` = 名词被教成动词）
校准集见 `docs/证据-标题判据校准-2026-11-22.md`：台账 13 条已批准标题 红 9/绿 4、5 条错例 5/5 命中。

两种用法：
  A. 检查新稿：`python3 tools/title_intro_check.py --file <02-title-intro.md> --word coin --gloss 硬币 --pos 名词`
  B. 统计存量：`python3 tools/title_intro_check.py --corpus <corpus.json>`
     （corpus 来自 tools 外部语料管线：29 本，含 title_lines / intro_lines）

退出码：0=全过  1=有违规  2=输入/参数错误（含标题 0 条且简介 0 条，等于没校验）
注意：本脚本是**写稿自检**，不是交付门禁；简介语义（地基是否落在核心义项）无法机检。
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

import io
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
except Exception:
    pass

SCENE_START = ("桌上", "碗里", "架子上", "地上", "床上", "手里", "旁边", "门口", "窗前", "柜上")
BAN_WORDS = ("启蒙", "进阶", "体系", "入门", "音标", "Phonics", "自然拼读", "CVC",
             "认了就能读", "念几遍就会", "学完", "掌握")
MAX_TITLE_CHARS = 12
MAX_SENT_CHARS = 30

# ── R13（2026-11-22）中文标题「释义逐字 + 量词/口语虚词白名单」 ──
# 判定链：去掉「台账释义」与「核心词形态」后，中文字符只许落在白名单里。
# 白名单**只放量词、指代词与口语虚词**，任何形容词性修饰（小/大/好/真…）一律不在内——
# 否则「一枚小硬币」这种「小X」套路会被判绿，而所有者 2026-11-22 明确否掉这类修饰。
# 因此「扇子」释义下的「扇一扇，fan」会因残留「扇一扇」被拦下，「一枚小硬币」也判红。
CN_WHITELIST = set("一二三两几把枚个只口条张片块颗朵根双群对些点儿这那的呀啊啦了呢吧")
# 英文祈使/动作标记：核心词后面紧跟这些词 = 把名词当动词用（今日事故：Fan it!）
EN_IMPERATIVE_TAIL = ("it", "them", "up", "down", "again", "more", "away", "around")
# 词型不属于动作类时，英文标题不得出现核心词的动词屈折形（fanning / fanned / fans…）
NON_VERB_POS = ("名词", "形容词", "颜色/数字", "颜色·数字", "位置介词", "人称代词", "疑问词")


def _strip_punct(s):
    return re.sub(r"[\s，,。.、！!？?：:；;“”\"'’‘（）()\[\]《》/|·\-—_]+", "", s)


def _en_tokens(s):
    return re.findall(r"[A-Za-z][A-Za-z'\-]*", s)


def check_title(text, word, pos=None, gloss=None):
    """返回 (问题列表, 标题条数)。

    支持两种标题写法：
      · 单标题（R13 唯一形态）：行内含「选定标题：硬币，Coin / Coin」——按「中文 / 英文」拆列，只许一条；
      · 表格行（旧 3 备选兼容）：`| 1 | 中文 | 英文 | …`。

    除原有五条（英文含词 / 中文含词形态 / 无括注 / 含词后 ≤12 字 / 无禁词）外，
    R13（2026-11-22）新增三条，只在给了 --gloss / --pos 时生效：
      G1 中文列必须含台账释义逐字        （释义丢了 = 教不上义项）
      G2 去掉释义与核心词后只许留白名单  （多出实词 = 语义扩充/第二核心词/小字病）
      P1 词型非动作类时，英文不得用动词屈折形或祈使尾（Fan it! / Fanning）
    """
    issues, n = [], 0

    def _audit(cn, en, tag):
        nonlocal n
        n += 1
        if not re.search(forms_pattern(word), en, re.I):
            issues.append("%s 英文列不含目标词：%r" % (tag, en))
        if not re.search(forms_pattern(word), cn, re.I):
            issues.append("%s 中文列不含目标词形态：%r" % (tag, cn))
        if re.search(r"[（(]", cn):
            issues.append("%s 中文列含括注：%r" % (tag, cn))
        if len(re.sub(r"[，,。.、！! ]", "", re.sub(forms_pattern(word), "", cn, flags=re.I))) > MAX_TITLE_CHARS:
            issues.append("%s 中文主体超过 %d 字：%r" % (tag, MAX_TITLE_CHARS, cn))
        for b in BAN_WORDS:
            if b.lower() in (cn + en).lower():
                issues.append("%s 含方法论禁词 %r" % (tag, b))
        # ── R13 新增：释义在场 + 零干扰 + 词型一致性 ──
        if gloss:
            # 词组核心词（如 coloring book）必须保留空格才能被词界正则命中；
            # _strip_punct 会吃掉空格导致 G2 结构性误报——这里用保留空格的变体。
            def _strip_keep_space(s):
                return re.sub(r"[\s，,。.、！!？?：:；;“”\"'’‘（）()\[\]《》/|·\-—_]+", " ", s).strip()
            g = _strip_keep_space(gloss)
            cn_clean = _strip_keep_space(cn)
            if g and g not in cn_clean:
                issues.append("%s [G1] 中文列不含台账释义「%s」：%r" % (tag, gloss, cn))
            else:
                residue = cn_clean.replace(g, "") if g else cn_clean
                residue = re.sub(forms_pattern(word), "", residue, flags=re.I).strip()
                bad = sorted({ch for ch in residue if ch not in CN_WHITELIST and not ch.isspace()})
                if bad:
                    issues.append("%s [G2] 中文列在释义与核心词之外多出 %s（释义「%s」）：%r"
                                  % (tag, "".join(bad), gloss, cn))
        if pos and pos.strip() in NON_VERB_POS:
            toks = _en_tokens(en)
            lower = [t.lower() for t in toks]
            verbish = [f for f in word_forms(word) if f.lower().endswith(("ing", "ed"))]
            for t in lower:
                if t in [v.lower() for v in verbish]:
                    issues.append("%s [P1] 词型「%s」却用了动词形态 %r：%r" % (tag, pos, t, en))
            for i, t in enumerate(lower):
                if not re.fullmatch(forms_pattern(word), t, re.I):
                    continue
                tail = lower[i + 1] if i + 1 < len(lower) else ""
                if tail in EN_IMPERATIVE_TAIL:
                    issues.append("%s [P1] 词型「%s」却写成祈使句（%s %s）：%r"
                                  % (tag, pos, t, tail, en))

    # 写法一：单标题「选定标题：中文 / English」（R13 唯一形态，只许一条）
    chosen = re.findall(r"(?m)^\s*[*-]?\s*[*]*选定标题[*]*[:：]\s*(.+)$", text)
    if len(chosen) > 1:
        issues.append("「选定标题」出现 %d 次（唯一形态只许 1 条）" % len(chosen))
        for k, x in enumerate(chosen):
            m2 = re.match(r"(.+?)\s*/\s*(\S.*)$", x.strip())
            _audit(m2.group(1).strip(), m2.group(2).strip(), "标题#选定%d" % (k + 1))
        return issues, n
    if len(chosen) == 1:
        m2 = re.match(r"(.+?)\s*/\s*(\S.*)$", chosen[0].strip())
        if m2:
            _audit(m2.group(1).strip(), m2.group(2).strip(), "标题#选定")
            return issues, n
        issues.append("「选定标题」格式不对（应为「中文 / English」）：%r" % chosen[0].strip())
        return issues, n

    # 写法二：表格行（旧 3 备选兼容；R13 后新稿不该再出现）
    for ln in text.splitlines():
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if len(cells) < 3 or not re.match(r"^\d+$", cells[0]):
            continue
        cn, en = cells[1], cells[2]
        if not en or "英文" in en:
            continue
        _audit(cn, en, "标题#%s" % cells[0])
    return issues, n


def check_intro(text, word):
    """只取「## 二、简介」之后、下一个 ##/### 之前的引用行。返回 (问题列表, 简介条数)。"""
    issues = []
    m = re.search(r"(?s)##\s*二、简介(.*?)(?=\n##\s|\n###\s|\Z)", text)
    seg = m.group(1) if m else text
    intros = []
    for x in re.findall(r"(?m)^>\s*(.+)$", seg):
        x = x.strip()
        # 2026-11-21：原先「不含目标词就 continue」会把 0 次的简介整条丢掉，
        # 导致 gates.md 声明的「目标词恰 1 次」对 0 次永不生效（假绿）。改为全部纳入判据。
        if re.search(r"[！!？?]\s*$", x) or x.endswith("。"):
            intros.append(x)
    for k, x in enumerate(intros):
        tag = "简介%s" % "ABC"[k] if k < 3 else "简介#%d" % (k + 1)
        hits = len(re.findall(forms_pattern(word), x, re.I))
        if hits != 1:
            issues.append("%s 目标词出现 %d 次（应恰好 1 次）：%r" % (tag, hits, x[:40]))
        first = re.split(r"[。！？!?]", x)[0]
        bad = [s for s in SCENE_START if first.startswith(s)]
        if bad:
            issues.append("%s 首句以场景词开头（%s）：%r" % (tag, bad[0], first[:24]))
        for b in BAN_WORDS:
            if b.lower() in x.lower():
                issues.append("%s 含方法论禁词 %r" % (tag, b))
        for s in re.split(r"[。！？!?]", x):
            s = s.strip()
            if s and len(s) > MAX_SENT_CHARS:
                issues.append("%s 有 %d 字长句（上限 %d）" % (tag, len(s), MAX_SENT_CHARS))
    return issues, len(intros)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--file", help="02-title-intro.md 路径（模式 A）")
    ap.add_argument("--word", help="核心词（模式 A 必填）")
    ap.add_argument("--gloss", help="台账『中文释义』（R13：给了才跑 G1/G2 两条判据；新书必须给）")
    ap.add_argument("--pos", help="台账『词型』（R13：给了且非动作类，才跑 P1 判据）")
    ap.add_argument("--corpus", help="corpus.json 路径（模式 B）")
    args = ap.parse_args()

    if args.file:
        if not args.word:
            print("模式 A 需要 --word")
            return 2
        try:
            t = io.open(args.file, encoding="utf-8-sig").read()
        except (OSError, UnicodeDecodeError) as e:
            print("读不到文件：%s" % e)
            return 2
        ti, nt = check_title(t, args.word, args.pos, args.gloss)
        ii, ni = check_intro(t, args.word)
        print("检查 %s（核心词 %s%s%s）" % (
            os.path.basename(args.file), args.word,
            "，词型 %s" % args.pos if args.pos else "",
            "，释义 %s" % args.gloss if args.gloss else ""))
        print("  标题 %d 条、简介 %d 条" % (nt, ni))
        if not args.gloss:
            print("  ⚠ 未给 --gloss：R13 的 G1/G2 两条判据未执行（不能据此说标题合规）")
        if nt == 0:
            print("  ⚠ 没解析到标题（应为 `| 1 | 中文 | 英文 | …` 表格行）")
        if ni == 0:
            print("  ⚠ 没解析到简介（应为「## 二、简介」下的 `>` 引用行）")
        if nt == 0 or ni == 0:  # 单边为 0 也属格式问题：此时那一半没有任何校验
            print("\n没解析到标题/简介，检查格式：标题应为 `| 1 | 中文 | 英文 | …` 表格行，"
                  "简介应为「## 二、简介」下的 `>` 引用行——此时没有任何校验，不能报通过")
            return 2
        allx = ti + ii
        if allx:
            print("\n[必须修复] %d 处" % len(allx))
            for x in allx:
                print("  ✗ " + x)
            return 1
        print("\n标题/简介判据全过（写稿自检口径；语义地基无法机检）")
        return 0

    if args.corpus:
        try:
            corp = json.load(open(args.corpus, encoding="utf-8"))
        except (OSError, ValueError) as e:
            print("读不到 corpus：%s" % e)
            return 2
        tot_t = ok_t = tot_i = ok_i = 0
        bad = []
        for c in corp:
            w = c.get("核心词") or c.get("word") or ""
            if not w:
                continue
            # 存量文本带「选定简介：」「选定标题：」前缀，且标题是「英文标题：X中文」粘连形态，先清洗
            raw_titles = " \n".join(c.get("title_lines") or [])
            raw_titles = raw_titles.replace("选定标题：", "")
            en_t = re.search(r"英文标题[:：]\s*([^\n]+)", raw_titles)
            cn_t = re.search(r"中文标题[:：]\s*([^\n]+)", raw_titles)
            title_issues, nt = [], 0
            if en_t or cn_t:
                nt = 1
                en = (en_t.group(1) if en_t else "").strip()
                cn = (cn_t.group(1) if cn_t else "").strip()
                # 「Robot机器人」是英文+中文粘连：按首个汉字切开
                m = re.match(r"^([A-Za-z][A-Za-z' \-]*?)([\u4e00-\u9fff].*)$", en)
                if m:
                    en, cn_extra = m.group(1).strip(), m.group(2)
                    if not cn:
                        cn = cn_extra
                if not re.search(r"(?<![A-Za-z])" + re.escape(w) + r"(?![A-Za-z])", en, re.I):
                    title_issues.append("英文标题不含目标词：%r" % en)
                if cn and not re.search(r"(?<![A-Za-z])" + re.escape(w) + r"(?![A-Za-z])", cn, re.I):
                    title_issues.append("中文标题不含目标词形态：%r" % cn)
                for b in BAN_WORDS:
                    if b.lower() in (en + cn).lower():
                        title_issues.append("标题含方法论禁词 %r" % b)
            raw_intro = "\n".join("> " + x.replace("选定简介：", "") for x in (c.get("intro_lines") or []))
            if raw_intro:
                ii, ni = check_intro("## 二、简介\n" + raw_intro, w)
                tot_i += ni
                ok_i += ni - len({x.split(" ")[0] for x in ii})
                for x in ii:
                    bad.append((c.get("code", "?"), "简介 " + x))
            if nt:
                tot_t += nt
                ok_t += nt - (1 if title_issues else 0)
                for x in title_issues:
                    bad.append((c.get("code", "?"), "标题 " + x))
        print("存量语料：标题 %d 本（合规 %d）、简介 %d 条（合规 %d）" % (tot_t, ok_t, tot_i, ok_i))
        if bad:
            print("\n不合规明细（共 %d 条，列前 20）：" % len(bad))
            for code, x in bad[:20]:
                print("  %-6s %s" % (code, x))
        return 0 if not bad else 1

    print("需要 --file 或 --corpus 之一")
    return 2


if __name__ == "__main__":
    sys.exit(main())
