# -*- coding: utf-8 -*-
"""目标词「词形」唯一口径（五个门禁/自检脚本共用）。

为什么要这个文件
----------------
2026-11-21 的审计发现：同一个「目标词」在五个脚本里各有各的识别方式——
`grammar_check` 先只认原形、后只认 +s/+es；`l4_case_check` 只认 +s/+es；
`l4_structure_check` 只认 +s/+es；`l4_presence_check` 完全不容忍复数。
后果：`berries`（-ies）、`feet`/`leaves`/`children`（不规则）、`COINS`（大小写变体）
这些行**整行不被检查**，门禁却照样打印「合规」——即假绿。

从今往后：任何脚本要判「这个词是不是目标词」，一律 `word_forms()` / `forms_pattern()`，
不得再各写一套。

用法
----
    from wordforms import word_forms, forms_pattern
    word_forms("berry")          # {'berry','berrys','berryes','berries'}
    re.search(forms_pattern("berry"), text, re.I)   # 词界安全、含全部屈折形
"""

IRREGULAR = {
    "child": ["children"], "foot": ["feet"], "tooth": ["teeth"], "goose": ["geese"],
    "mouse": ["mice"], "louse": ["lice"], "man": ["men"], "woman": ["women"],
    "person": ["people"], "ox": ["oxen"],
    "leaf": ["leaves"], "loaf": ["loaves"], "knife": ["knives"], "wife": ["wives"],
    "life": ["lives"], "wolf": ["wolves"], "shelf": ["shelves"], "self": ["selves"],
    "half": ["halves"], "thief": ["thieves"], "calf": ["calves"],
    # 同形复数（单复数同形）
    "fish": ["fish"], "sheep": ["sheep"], "deer": ["deer"], "series": ["series"],
    "means": ["means"],
}


def word_forms(word):
    """返回该词的**全部**可接受词形（小写集合）：原形 + 规则复数 + 不规则复数。"""
    w = (word or "").strip().lower()
    if not w:
        return set()
    out = {w, w + "s", w + "es"}
    if len(w) >= 2 and w.endswith("y") and w[-2] not in "aeiou":
        out.add(w[:-1] + "ies")
    if w.endswith("f") and len(w) >= 2:
        out.add(w[:-1] + "ves")
    if w.endswith("fe") and len(w) >= 3:
        out.add(w[:-2] + "ves")
    out.update(IRREGULAR.get(w, []))
    return out


def forms_pattern(word):
    """词形正则：词界安全，匹配任一屈折形（调用方自行加 re.I 控制大小写）。"""
    import re
    alts = sorted((re.escape(f) for f in word_forms(word)), key=len, reverse=True)
    if not alts:
        return r"(?!x)x"
    return r"(?<![A-Za-z])(?:" + "|".join(alts) + r")(?![A-Za-z])"


def upper_forms(word):
    """供「引导语/约定区不得出现全大写目标词」这类检查使用。"""
    return {f.upper() for f in word_forms(word)}
