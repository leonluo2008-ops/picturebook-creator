# -*- coding: utf-8 -*-
"""按规则族对 29 本语料做统计（族1 简介 / 族2 标题 / 族3 旁白）。
输入: corpus.json（build_corpus.py 产出）
输出: family_stats.md + intros_raw.md（供人工做落点分类）
每条统计都带「样本数 / 满足数 / 口径」。
"""
import json
import os
import re
import sys

CORP = sys.argv[1]
CORP_JSON = os.path.join(CORP, "corpus.json")
OUT = sys.argv[2]
os.makedirs(OUT, exist_ok=True)

corpus = json.load(open(CORP_JSON, encoding="utf-8"))

SCENE_WORDS = ("桌上", "碗里", "架子上", "地上", "床上", "手里", "旁边", "门口", "窗前")
BAN_WORDS = ("启蒙", "进阶", "体系", "入门", "音标", "Phonics", "自然拼读", "CVC", "认了就能读", "念几遍就会")
REDUP = re.compile(r"([\u4e00-\u9fff])\1")
SPLIT = re.compile(r"[A-Za-z](?:-[A-Za-z])+")   # S-O-A-P / S-oa-p 型拆读


def get_title(c):
    for ln in c.get("title_lines") or []:
        if "英文标题" in ln:
            en = ln.split("英文标题", 1)[1].lstrip("：: ").strip()
            return en
    return ""


def get_intro(c):
    for ln in c.get("intro_lines") or []:
        if "选定简介" in ln:
            return ln.split("选定简介", 1)[1].lstrip("：: ").strip()
    return ""


def main():
    L, R = [], []
    rows = []
    for c in corpus:
        word = (c.get("核心词") or "").strip()
        title = get_title(c)
        intro = get_intro(c)
        pages = c.get("pages") or []
        n_pages = len(pages)
        en_words = [len(re.findall(r"[A-Za-z][A-Za-z'\-]*", (p.get("narration") or "").split("/")[0]))
                    for p in pages]
        split_hits = sum(1 for p in pages if SPLIT.search((p.get("narration") or "").split("/")[0]))
        rows.append({
            "code": c.get("code"), "word": word, "title": title, "intro": intro,
            "pages": n_pages, "en_min": min(en_words) if en_words else 0,
            "en_max": max(en_words) if en_words else 0,
            "en_avg": round(sum(en_words) / len(en_words), 1) if en_words else 0,
            "split_pages": split_hits,
        })

    R.append("# 29 本原始 标题 / 简介（供人工落点分类）\n")
    for r in rows:
        R.append("## %s · %s\n" % (r["code"], r["word"]))
        R.append("- 标题: `%s`" % (r["title"] or "(空)"))
        R.append("- 简介: %s\n" % (r["intro"] or "(空)"))

    L.append("# 29 本 · 规则族机器统计\n")
    L.append("语料：Notion 近 10 天、状态∈{待生图,已制作}，共 **%d 本**（所有者指定，排除 128 本全量的旧混乱内容）。\n" % len(rows))

    # 族2 标题
    has_word = sum(1 for r in rows if r["word"] and r["word"].lower() in (r["title"] or "").lower())
    has_paren = sum(1 for r in rows if re.search(r"[（(]", r["title"] or ""))
    has_ban = sum(1 for r in rows if any(b.lower() in (r["title"] or "").lower() for b in BAN_WORDS))
    title_lens = [len(r["title"]) for r in rows if r["title"]]
    L.append("## 族2 · 标题\n")
    L.append("| 判据 | 满足 / 样本 | 口径 |")
    L.append("|---|---|---|")
    L.append("| 英文标题含核心词 | %d/%d | 大小写不敏感子串 |" % (has_word, len(rows)))
    L.append("| 标题含括注 | %d/%d | 正则 `[（(]` |" % (has_paren, len(rows)))
    L.append("| 标题含方法论/发音类禁词 | %d/%d | 禁词表 %d 个 |" % (has_ban, len(rows), len(BAN_WORDS)))
    if title_lens:
        L.append("| 英文标题长度 | 最短 %d / 最长 %d / 均值 %.1f 字符 | 字符数 |" % (min(title_lens), max(title_lens), sum(title_lens)/len(title_lens)))
    L.append("")

    # 族1 简介
    scene_start = 0
    has_q = 0
    word_end = 0
    redup_over = 0
    ban_hits = 0
    lens = []
    word_cnt = []
    for r in rows:
        t = r["intro"] or ""
        if not t:
            continue
        first = re.split(r"[。！？!?]", t)[0]
        if any(first.startswith(w) or w in first[:6] for w in SCENE_WORDS):
            scene_start += 1
        if re.search(r"[？?]", t):
            has_q += 1
        if r["word"] and t.rstrip().lower().endswith(r["word"].lower()) or (r["word"] and ("，" + r["word"] + "！") in t):
            word_end += 1
        if len(REDUP.findall(t)) > 1:
            redup_over += 1
        if any(b.lower() in t.lower() for b in BAN_WORDS):
            ban_hits += 1
        lens.append(len(t))
        word_cnt.append(len(re.findall(r"[A-Za-z]+", t)))
    n_intro = len([r for r in rows if r["intro"]])
    L.append("## 族1 · 简介\n")
    L.append("| 判据 | 满足 / 样本 | 口径 |")
    L.append("|---|---|---|")
    L.append("| 首句写场景布置（禁） | %d/%d | 首句前 6 字命中场景词表 |" % (scene_start, n_intro))
    L.append("| 含问句 | %d/%d | 正则 `？|?` |" % (has_q, n_intro))
    L.append("| 目标词落在结尾 | %d/%d | 结尾是目标词，或 `，词！` 形态 |" % (word_end, n_intro))
    L.append("| 叠词 >1 处（禁） | %d/%d | 重复汉字 AA 计数 |" % (redup_over, n_intro))
    L.append("| 含方法论/效果承诺类禁词 | %d/%d | 同上禁词表 |" % (ban_hits, n_intro))
    if lens:
        L.append("| 简介长度 | 最短 %d / 最长 %d / 均值 %.1f 字 | 字符数 |" % (min(lens), max(lens), sum(lens)/len(lens)))
        L.append("| 目标词出现次数 | 均值 %.2f 次 | 英文词计数 |" % (sum(word_cnt)/len(word_cnt)))
    L.append("")

    # 族3 旁白
    L.append("## 族3 · 旁白\n")
    L.append("| 判据 | 结果 | 口径 |")
    L.append("|---|---|---|")
    allmin = min(r["en_min"] for r in rows)
    allmax = max(r["en_max"] for r in rows)
    L.append("| 单页英文词数 | %d–%d 词（全样本极值） | 英文段正则计数 |" % (allmin, allmax))
    L.append("| 单页英文 >10 词的本数 | %d/%d | 任有一页 >10 |" % (sum(1 for r in rows if r["en_max"] > 10), len(rows)))
    L.append("| 存在拆读页（`S-O-A-P` 型）的本数 | %d/%d | 正则 `[A-Za-z](-[A-Za-z])+` |" % (sum(1 for r in rows if r["split_pages"] > 0), len(rows)))
    L.append("| 页数 | 9 页 %d 本；其它 %d 本 | L4 页记录数 |" % (sum(1 for r in rows if r["pages"] == 9), sum(1 for r in rows if r["pages"] != 9)))
    L.append("")

    open(os.path.join(OUT, "family_stats.md"), "w", encoding="utf-8").write("\n".join(L))
    open(os.path.join(OUT, "intros_raw.md"), "w", encoding="utf-8").write("\n".join(R))
    print("\n".join(L))
    print("写出:", OUT)


if __name__ == "__main__":
    main()
