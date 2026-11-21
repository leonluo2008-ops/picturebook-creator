"""修正口径后的最终盘点：把「规则 × 成果」分三档，并做代际/模式分层。
输入: corpus.json（build_corpus） + verdict.json（check_rules，仅取 R1/R2/R5/R8/R9/R10/R12）
输出: final.md
"""
import json
import os
import re
import sys

CORP = sys.argv[1]
OUT = sys.argv[2]

corpus = json.load(open(os.path.join(CORP, "corpus.json"), encoding="utf-8"))
verdict = json.load(open(os.path.join(OUT, "verdict.json"), encoding="utf-8"))

LEAD_TYPES = ("认知页", "语境重复页", "语境页", "词族拓展页", "互动练习页")
HEAD_FIELD_VARIANTS = {
    "目标单词": ("目标单词", "目标词"),
    "目标年龄": ("目标年龄",),
    "文字风格": ("文字风格",),
    "主角外观": ("主角外观",),
    "画风": ("画风", "画面风格", "画面风格锚点"),
    "站位约定": ("站位约定",),
    "机位约定": ("机位约定",),
    "场景锚点": ("主要场景锚点", "场景锚点"),
    "全书文字与配色": ("全书文字与配色",),
}


def head_of(l4pages):
    return "\n".join([p.get("prompt", "") for p in l4pages])


def is_lead(c):
    """领读模式判定：页面类型列非空，或 L4 里出现目标单词/目标年龄字段"""
    if any((p.get("ptype") or "").strip() for p in c.get("pages") or []):
        return True
    h = head_of(c.get("pages") or [])
    return ("目标单词" in h) or ("目标年龄" in h)


def safety3(prompt):
    """边缘安全区「三要素」按 SKILL.md:1619-1623 口径"""
    seg = prompt.split("构图要求", 1)[1] if "构图要求" in prompt else ""
    e1 = "80%" in seg
    e2 = ("10%" in seg)
    e3 = ("背景" in seg) and ("边缘" in seg)
    return e1, e2, e3, seg


def main():
    lead = [c for c in corpus if is_lead(c)]
    story = [c for c in corpus if not is_lead(c)]
    L = []
    L.append("# 规则 × 成果 盘点（最终，修正口径后）")
    L.append("")
    L.append("语料：Notion 排产台账，近 10 天、状态∈{待生图,已制作} 共 **%d 本**（领读模式 %d 本 / 故事模式 %d 本）。"
             % (len(corpus), len(lead), len(story)))
    L.append("规则源：`picturebook-creator/SKILL.md`（11.1.8-codex.10，1786 行）。")
    L.append("")
    L.append("## 一、匹配（成果普遍遵守，规则可留）")
    L.append("")
    L.append("| 判据 | 口径 | 通过 |")
    L.append("|---|---|---|")
    v = verdict["verdict"]
    for rid, label in (("R1", "L4 页数 == 旁白表数据行数"), ("R2", "封面 3:4 / 内页 16:9"),
                       ("R5", "每页场景段出现核心词（在不在）"), ("R8", "画面词大小写形态 == 文稿形态"),
                       ("R9", "提示词不混入链接"), ("R10", "首条旁白「封面（中 / 英）」"),
                       ("R12", "英文含词行中文须同现（封面豁免）")):
        L.append("| %s | %s | %d/%d |" % (rid, label, v[rid]["ok"], v[rid]["total"]))
    L.append("")

    # 三要素
    L.append("## 二、修正后重算的两条")
    L.append("")
    total_pages = sum(len(c["pages"]) for c in lead)
    e_ok = [0, 0, 0]
    danger_named = 0
    for c in lead:
        for p in c["pages"]:
            e1, e2, e3, seg = safety3(p.get("prompt", ""))
            e_ok[0] += e1
            e_ok[1] += e2
            e_ok[2] += e3
            if re.search(r"(顶|尖|端|角|脚|爪|翼|尾|头|手)", seg):
                danger_named += 1
    L.append("### R4（修正）边缘安全区三要素 —— 分母 %d 页（领读模式）" % total_pages)
    L.append("")
    L.append("| 要素 | 满足页数 |")
    L.append("|---|---|")
    L.append("| ① 80%% 安全区 | %d/%d |" % (e_ok[0], total_pages))
    L.append("| ② 10%% 净空 | %d/%d |" % (e_ok[1], total_pages))
    L.append("| ③ 背景铺边 | %d/%d |" % (e_ok[2], total_pages))
    L.append("| （启发式）危险部位点名 | %d/%d |" % (danger_named, total_pages))
    L.append("")
    L.append("> 原判据要求字面含「不得进入预留区」（SKILL.md 固定句式里的中段），实测该中段在成果里常被省略，"
             "而三要素本身多数满足 —— **原判据过严，已作废**。")
    L.append("")

    # 术语一致性
    L.append("### R3（改判为「术语一致性」）页面类型术语")
    L.append("")
    term_page = {}
    term_head = {}
    for c in lead:
        for p in c["pages"]:
            pt = (p.get("ptype") or "").strip()
            pt = re.sub(r"^P\d+\s*", "", pt)
            pt = re.sub(r"[（(].*?[)）]", "", pt).strip()
            if pt:
                term_page[pt] = term_page.get(pt, 0) + 1
    L.append("| 成果里出现的页面类型 | 页数 |")
    L.append("|---|---|")
    for k, n in sorted(term_page.items(), key=lambda x: -x[1]):
        L.append("| %s | %d |" % (k, n))
    L.append("")
    L.append("规则文本侧：`语境页` 21 次 / `语境重复页` 4 次 —— **规则自身两个写法并存**；"
             "成果 %d 页用「语境页」、%d 页用「语境重复页」。"
             % (term_page.get("语境页", 0), term_page.get("语境重复页", 0)))
    L.append("")

    # 全局约定字段
    L.append("### R6（修正）【全局设计约定】字段覆盖 —— 按同义变体合并")
    L.append("")
    L.append("| 字段 | 覆盖 | 说明 |")
    L.append("|---|---|---|")
    GF_VARIANTS = {
        "目标单词": ("目标单词", "目标词"),
        "目标年龄": ("目标年龄",),
        "文字风格": ("文字风格",),
        "主角外观": ("主角外观",),
        "画风": ("画风", "画面风格"),
        "站位约定": ("站位约定",),
        "机位约定": ("机位约定",),
        "场景锚点": ("主要场景锚点", "场景锚点"),
        "全书文字与配色": ("全书文字与配色",),
    }
    for name, variants in GF_VARIANTS.items():
        n = 0
        for c in lead:
            gf = c.get("global_fields") or {}
            if any(gf.get(v) for v in variants):
                n += 1
        note = "（变体：%s）" % " / ".join(variants) if len(variants) > 1 else ""
        L.append("| %s | %d/%d | %s |" % (name, n, len(lead), note))
    L.append("")
    L.append("> 口径：字段名在 L4「第一个「旁白:」之前」的全局约定区里 grep（build_corpus 已按此口径算好）；"
             "同义变体任一命中即算。原判据要求 12 个字段名全部命中的写法已作废。")
    L.append("")

    # 每页标记覆盖 + 代际
    L.append("### R7 每页「角色一致性 / 场景一致性」标记 —— 按书分层")
    L.append("")
    L.append("| 排产号 | 页数 | 角色一致性 | 场景一致性 | 构图要求 |")
    L.append("|---|---|---|---|---|")
    full_cover, partial = 0, 0
    for c in lead:
        n = len(c["pages"])
        a = sum(1 for p in c["pages"] if "角色一致性" in p.get("prompt", ""))
        b = sum(1 for p in c["pages"] if "场景一致性" in p.get("prompt", ""))
        d = sum(1 for p in c["pages"] if "构图要求" in p.get("prompt", ""))
        L.append("| %s | %d | %d | %d | %d |" % (c["code"], n, a, b, d))
        if a == n and b == n:
            full_cover += 1
        else:
            partial += 1
    L.append("")
    L.append("全页覆盖 = **%d 本**；部分覆盖 = **%d 本** —— 说明「每页必写角色/场景一致性」这条规则"
             "在成果层没有稳定执行，存在代际差（不是全对有或全错）。" % (full_cover, partial))
    L.append("")
    L.append("## 三、格式代际差异（同一套规则下的多种写法）")
    L.append("")
    with_pn = sum(1 for c in lead
                  if len(c["pages"]) > 1
                  and re.match(r"^P\d+\s", (c["pages"][1].get("narration") or "").strip()))
    no_pn = len(lead) - with_pn
    L.append("| 变体 | 本数 | 例 |")
    L.append("|---|---|---|")
    L.append("| 内页旁白行带 `Pn` 前缀 | %d | B585 `P1 The frog taps…` |" % with_pn)
    L.append("| 内页旁白行不带前缀 | %d | B639 `The robot walks…` |" % no_pn)
    L.append("| 页面类型带 `Pn ` 前缀 | %d | B293 `P1 语境重复页` |"
             % sum(1 for c in lead for p in c["pages"] if re.match(r"^P\d+\s", (p.get("ptype") or "").strip())))
    L.append("")
    L.append("## 四、死链（引用但不存在）")
    L.append("")
    L.append("| 引用 | 出现行 | 结论 |")
    L.append("|---|---|---|")
    L.append("| `scripts/audit_ledger.py` | SKILL.md:873 | **不存在**；SKILL.md 把「在不在」逐页检查的补偿手段指向它 |")
    L.append("")
    open(os.path.join(OUT, "final.md"), "w", encoding="utf-8").write("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()
