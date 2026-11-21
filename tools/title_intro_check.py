#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""标题 / 简介判据检查（族2 + 族1）—— 补「标题与简介无任何机检」的缺口。

判据来自 29 本语料盘点（`docs/证据-29本盘点.md`）：
- 标题：英文含核心词、中文列含目标词形态、无括注、无方法论禁词、含词后 ≤12 字
- 简介：目标词恰好 1 次、首句不以场景词开头、无禁词、单句 ≤30 字

两种用法：
  A. 检查新稿：`python3 tools/title_intro_check.py --file <02-title-intro.md> --word coin`
  B. 统计存量：`python3 tools/title_intro_check.py --corpus <corpus.json>`
     （corpus 来自 tools 外部语料管线：29 本，含 title_lines / intro_lines）

退出码：0=全过  1=有违规  2=输入/参数错误（含标题 0 条且简介 0 条，等于没校验）
注意：本脚本是**写稿自检**，不是交付门禁；简介语义（地基是否落在核心义项）无法机检。
"""
import argparse
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


def check_title(text, word):
    """返回 (问题列表, 标题条数)。"""
    issues, n = [], 0
    # 表格行：| 1 | 中文 | 英文 | ...
    for ln in text.splitlines():
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if len(cells) < 3 or not re.match(r"^\d+$", cells[0]):
            continue
        cn, en = cells[1], cells[2]
        if not en or "英文" in en:
            continue
        n += 1
        tag = "标题#%s" % cells[0]
        if not re.search(r"(?<![A-Za-z])" + re.escape(word) + r"(?![A-Za-z])", en, re.I):
            issues.append("%s 英文列不含目标词：%r" % (tag, en))
        if not re.search(r"(?<![A-Za-z])" + re.escape(word) + r"(?![A-Za-z])", cn, re.I):
            issues.append("%s 中文列不含目标词形态：%r" % (tag, cn))
        if re.search(r"[（(]", cn):
            issues.append("%s 中文列含括注：%r" % (tag, cn))
        if len(re.sub(r"[，,。.、！! ]", "", re.sub(r"(?i)" + re.escape(word), "", cn))) > MAX_TITLE_CHARS:
            issues.append("%s 中文主体超过 %d 字：%r" % (tag, MAX_TITLE_CHARS, cn))
        for b in BAN_WORDS:
            if b.lower() in (cn + en).lower():
                issues.append("%s 含方法论禁词 %r" % (tag, b))
    return issues, n


def check_intro(text, word):
    """只取「## 二、简介」之后、下一个 ##/### 之前的引用行。返回 (问题列表, 简介条数)。"""
    issues = []
    m = re.search(r"(?s)##\s*二、简介(.*?)(?=\n##\s|\n###\s|\Z)", text)
    seg = m.group(1) if m else text
    intros = []
    for x in re.findall(r"(?m)^>\s*(.+)$", seg):
        x = x.strip()
        if not re.search(r"(?<![A-Za-z])" + re.escape(word) + r"(?![A-Za-z])", x, re.I):
            continue
        if re.search(r"[！!]\s*$", x) or x.endswith("。"):
            intros.append(x)
    for k, x in enumerate(intros):
        tag = "简介%s" % "ABC"[k] if k < 3 else "简介#%d" % (k + 1)
        hits = len(re.findall(r"(?<![A-Za-z])" + re.escape(word) + r"(?![A-Za-z])", x, re.I))
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
        ti, nt = check_title(t, args.word)
        ii, ni = check_intro(t, args.word)
        print("检查 %s（核心词 %s）" % (os.path.basename(args.file), args.word))
        print("  标题 %d 条、简介 %d 条" % (nt, ni))
        if nt == 0:
            print("  ⚠ 没解析到标题（应为 `| 1 | 中文 | 英文 | …` 表格行）")
        if ni == 0:
            print("  ⚠ 没解析到简介（应为「## 二、简介」下的 `>` 引用行）")
        if nt == 0 and ni == 0:
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
