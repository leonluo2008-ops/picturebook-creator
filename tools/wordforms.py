# -*- coding: utf-8 -*-
"""目标词「词形」唯一口径（五个门禁/自检脚本共用）。

为什么要这个文件
----------------
审计发现同一个「目标词」在五个脚本里各有各的识别方式，且随版本漂移：
先只认原形，后只认 +s/+es；`l4_presence_check` 一度完全不容忍复数。
后果是 `berries`（-ies）、`feet`/`leaves`（不规则复数）、`jumping`/`longer`
（动词、形容词屈折形）这些行**整行不被检查**，门禁却打印「合规」——假绿。

因此：本 skill 声明支持的核心词型是 **名词 / 动作动词 / 形容词 / 位置介词**
（见 `references/flow.md`「台账词型」）。凡要判「这个词是不是目标词」，
一律走本文件的 `word_forms()` / `forms_pattern()`，不得各写一套。

设计取舍
--------
- 生成的是**候选词形超集**：宁可多认（最多造成「该页本不算目标词也去查」的误红），
  也不许漏认（漏认＝整行不查＝假绿，比误红危险得多）。
- 不做 `f/fe → ves` 通用改写（会让 safe→saves、cafe→caves 误命中），
  需要 ves 的词在 `IRREGULAR_NOUN` 里逐个列出。
- 复合词按后缀处理：`snowman → snowmen`、`grandchild → grandchildren`。

用法
----
    from wordforms import word_forms, forms_pattern, upper_forms
    word_forms("berry")   # {'berry','berrys','berryes','berries'}
    re.search(forms_pattern("jump"), text, re.I)
"""

# ── 名词：不规则复数 / 同形复数 ──
IRREGULAR_NOUN = {
    "child": ["children"], "foot": ["feet"], "tooth": ["teeth"], "goose": ["geese"],
    "mouse": ["mice"], "louse": ["lice"], "ox": ["oxen"], "person": ["people"], "man": ["men"], "penny": ["pence"],
    "leaf": ["leaves"], "loaf": ["loaves"], "knife": ["knives"], "wife": ["wives"],
    "life": ["lives"], "wolf": ["wolves"], "shelf": ["shelves"], "self": ["selves"],
    "half": ["halves"], "thief": ["thieves"], "calf": ["calves"], "elf": ["elves"],
    "scarf": ["scarves"], "dwarf": ["dwarves"], "hoof": ["hooves"], "wharf": ["wharves"],
    "sheaf": ["sheaves"], "deer": ["deer"], "sheep": ["sheep"], "fish": ["fish"],
    "series": ["series"], "means": ["means"],
}

# 复合词后缀处理（-man / -woman / -child 等）
COMPOUND_SUFFIX = [
    ("man", "men"), ("woman", "women"), ("child", "children"), ("foot", "feet"),
    ("tooth", "teeth"), ("mouse", "mice"), ("goose", "geese"),
]

# ── 动词：不规则变化（低幼绘本常见）──
IRREGULAR_VERB = {
    "be": ["am", "is", "are", "was", "were", "been", "being"],
    "go": ["goes", "going", "went", "gone"],
    "do": ["does", "doing", "did", "done"],
    "have": ["has", "having", "had"],
    "say": ["says", "saying", "said"],
    "make": ["makes", "making", "made"],
    "take": ["takes", "taking", "took", "taken"],
    "come": ["comes", "coming", "came"],
    "give": ["gives", "giving", "gave", "given"],
    "get": ["gets", "getting", "got", "gotten"],
    "see": ["sees", "seeing", "saw", "seen"],
    "eat": ["eats", "eating", "ate", "eaten"],
    "run": ["runs", "running", "ran"],
    "sit": ["sits", "sitting", "sat"],
    "stand": ["stands", "standing", "stood"],
    "fall": ["falls", "falling", "fell", "fallen"],
    "find": ["finds", "finding", "found"],
    "think": ["thinks", "thinking", "thought"],
    "bring": ["brings", "bringing", "brought"],
    "buy": ["buys", "buying", "bought"],
    "hold": ["holds", "holding", "held"],
    "keep": ["keeps", "keeping", "kept"],
    "sleep": ["sleeps", "sleeping", "slept"],
    "swim": ["swims", "swimming", "swam", "swum"],
    "fly": ["flies", "flying", "flew", "flown"],
    "draw": ["draws", "drawing", "drew", "drawn"],
    "sing": ["sings", "singing", "sang", "sung"],
    "read": ["reads", "reading"],
    "put": ["puts", "putting"],
    "cut": ["cuts", "cutting"],
    "stop": ["stops", "stopping", "stopped"],
    "jump": ["jumps", "jumping", "jumped"],
    "clap": ["claps", "clapping", "clapped"],
    "hug": ["hugs", "hugging", "hugged"],
    "hop": ["hops", "hopping", "hopped"],
    "wave": ["waves", "waving", "waved"],
    "smile": ["smiles", "smiling", "smiled"],
    "begin": ["begins", "beginning", "began", "begun"],
    "blow": ["blows", "blowing", "blew", "blown"],
    "break": ["breaks", "breaking", "broke", "broken"],
    "build": ["builds", "building", "built"],
    "catch": ["catches", "catching", "caught"],
    "choose": ["chooses", "choosing", "chose", "chosen"],
    "drink": ["drinks", "drinking", "drank", "drunk"],
    "drive": ["drives", "driving", "drove", "driven"],
    "feel": ["feels", "feeling", "felt"],
    "hear": ["hears", "hearing", "heard"],
    "hide": ["hides", "hiding", "hid", "hidden"],
    "leave": ["leaves", "leaving", "left"],
    "lose": ["loses", "losing", "lost"],
    "meet": ["meets", "meeting", "met"],
    "ride": ["rides", "riding", "rode", "ridden"],
    "ring": ["rings", "ringing", "rang", "rung"],
    "rise": ["rises", "rising", "rose", "risen"],
    "sell": ["sells", "selling", "sold"],
    "send": ["sends", "sending", "sent"],
    "shake": ["shakes", "shaking", "shook", "shaken"],
    "shoot": ["shoots", "shooting", "shot"],
    "speak": ["speaks", "speaking", "spoke", "spoken"],
    "spend": ["spends", "spending", "spent"],
    "teach": ["teaches", "teaching", "taught"],
    "tell": ["tells", "telling", "told"],
    "throw": ["throws", "throwing", "threw", "thrown"],
    "wake": ["wakes", "waking", "woke", "woken"],
    "wear": ["wears", "wearing", "wore", "worn"],
    "win": ["wins", "winning", "won"],
    "write": ["writes", "writing", "wrote", "written"],
    "forget": ["forgets", "forgetting", "forgot", "forgotten"],
    "fight": ["fights", "fighting", "fought"],
    "pay": ["pays", "paying", "paid"],
    "sweep": ["sweeps", "sweeping", "swept"],
}

# ── 形容词：比较级 / 最高级 ──
IRREGULAR_ADJ = {
    "good": ["better", "best"], "bad": ["worse", "worst"],
    "many": ["more", "most"], "much": ["more", "most"],
    "little": ["less", "least"], "far": ["farther", "farthest", "further", "furthest"],
    "big": ["bigger", "biggest"], "hot": ["hotter", "hottest"],
    "sad": ["sadder", "saddest"], "thin": ["thinner", "thinnest"],
    "wet": ["wetter", "wettest"], "fat": ["fatter", "fattest"],
}

VOWELS = "aeiou"


def _is_cvc(w):
    """粗略的「辅音-元音-辅音」判定，用于 stop→stopping、big→bigger 这类双写。"""
    if len(w) < 3:
        return False
    a, b, c = w[-3], w[-2], w[-1]
    return (a not in VOWELS) and (b in VOWELS) and (c not in VOWELS) and c not in "wxy"


def word_forms(word):
    """返回该词的**全部**候选词形（小写集合）：名词复数 + 动词变化 + 形容词级。"""
    w = (word or "").strip().lower()
    if not w:
        return set()
    out = {w, w + "s", w + "es"}

    # 名词：-y → -ies；不规则；复合词
    if len(w) >= 2 and w.endswith("y") and w[-2] not in VOWELS:
        out.add(w[:-1] + "ies")
    out.update(IRREGULAR_NOUN.get(w, []))
    for suf, rep in COMPOUND_SUFFIX:
        if w.endswith(suf) and len(w) > len(suf):
            out.add(w[: -len(suf)] + rep)

    # 动词：-ing / -ed / 第三人称；e 结尾去 e；CVC 双写
    if w.endswith("e") and len(w) >= 2:
        out.add(w[:-1] + "ing")
        out.add(w + "d")
    else:
        out.add(w + "ing")
        out.add(w + "ed")
        if _is_cvc(w):
            out.add(w + w[-1] + "ing")
            out.add(w + w[-1] + "ed")
    if len(w) >= 2 and w.endswith("y") and w[-2] not in VOWELS:
        out.add(w[:-1] + "ied")
    out.update(IRREGULAR_VERB.get(w, []))

    # 形容词：-er / -est
    out.add(w + "er")
    out.add(w + "est")
    if w.endswith("e"):
        out.add(w + "r")
        out.add(w + "st")
    if len(w) >= 2 and w.endswith("y") and w[-2] not in VOWELS:
        out.add(w[:-1] + "ier")
        out.add(w[:-1] + "iest")
    if _is_cvc(w):
        out.add(w + w[-1] + "er")
        out.add(w + w[-1] + "est")
    out.update(IRREGULAR_ADJ.get(w, []))

    return out


def forms_pattern(word):
    """词形正则：词界安全，匹配任一候选词形（调用方自行加 re.I 控制大小写）。"""
    import re
    alts = sorted((re.escape(f) for f in word_forms(word)), key=len, reverse=True)
    if not alts:
        return r"(?!x)x"
    return r"(?<![A-Za-z])(?:" + "|".join(alts) + r")(?![A-Za-z])"


def upper_forms(word):
    """供「引导语/约定区不得出现全大写目标词」这类检查使用。"""
    return {f.upper() for f in word_forms(word)}
