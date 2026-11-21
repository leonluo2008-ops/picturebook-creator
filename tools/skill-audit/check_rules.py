"""规则 × 成果 机器判据比对。
输入: corpus.json（build_corpus.py 产出）
输出: verdict.json + report.md
每条判据都给「样本数 / 满足数 / 口径」，可复跑。
"""
import json
import os
import re
import sys

REPO = r"E:\OneDrive\工作文件夹\儿童绘本\codex-workspace\picturebook-creator"
sys.path.insert(0, os.path.join(REPO, "tools"))
try:
    import l4_case_check as L4  # 复用项目自带门禁的形态判定
except Exception as e:  # pragma: no cover
    L4 = None
    print("警告: 无法导入 l4_case_check:", e)

CURRENT_PAGE_TYPES = ("认知页", "语境重复页", "词族拓展页", "互动练习页")
SAFETY_BITS = ("80%", "10%", "不得进入预留区")
GLOBAL_FIELDS = ("目标单词", "目标年龄", "文字风格", "主角外观", "画风", "画面风格",
                 "站位约定", "机位约定", "主要场景锚点", "场景锚点", "全书文字与配色", "核心物件")


def norm_ptype(s):
    s = (s or "").strip()
    s = re.sub(r"^P\d+\s*", "", s)          # 去掉 "P1 " 前缀
    s = re.sub(r"[（(].*?[)）]", "", s)      # 去掉括注
    return s.strip()


def eng_part(narration):
    """旁白行「英文 / 中文」取英文段"""
    if "/" in narration:
        return narration.split("/")[0].strip()
    return narration.strip()


def cn_part(narration):
    if "/" in narration:
        return narration.split("/", 1)[1].strip()
    return ""


def main():
    corp_dir = sys.argv[1]
    out_dir = sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)
    corpus = json.load(open(os.path.join(corp_dir, "corpus.json"), encoding="utf-8"))

    results = []      # 每条判据: dict(id, 名称, 口径, 样本, 满足, 失败明细[])
    for c in corpus:
        pages = c.get("pages") or []
        word = (c.get("核心词") or "").strip()
        code = c.get("code")
        fails = {}

        def add(rid, detail):
            fails.setdefault(rid, []).append(detail)

        # R1 页数一致性: L4 页数 == 旁白表数据行数
        n_l4 = len(pages)
        n_nar = c.get("narration_row_count") or 0
        if n_l4 != n_nar:
            add("R1", "%s: L4 %d 页 vs 旁白表 %d 行" % (code, n_l4, n_nar))

        # R2 比例: 封面 3:4，其余 16:9
        for i, p in enumerate(pages):
            want = "3:4" if i == 0 else "16:9"
            got = (p.get("ratio") or "").strip()
            if got != want:
                add("R2", "%s P%d: 比例 %r（应 %s）" % (code, i, got, want))

        # R3 页面类型 ∈ 现行词表
        for i, p in enumerate(pages):
            pt = norm_ptype(p.get("ptype"))
            if pt not in CURRENT_PAGE_TYPES:
                add("R3", "%s 第%d条: 页面类型 %r 不在现行词表" % (code, i, (p.get("ptype") or "").strip()))

        # R4 每页带「构图要求」且含三要素
        for i, p in enumerate(pages):
            pr = p.get("prompt") or ""
            if "构图要求" not in pr:
                add("R4", "%s 第%d条: 缺「构图要求」" % (code, i))
                continue
            seg = pr.split("构图要求", 1)[1]
            miss = [b for b in SAFETY_BITS if b not in seg]
            if miss:
                add("R4", "%s 第%d条: 构图要求缺 %s" % (code, i, ",".join(miss)))

        # R5 目标词「在不在」: 构图要求之前的场景段必须出现核心词（封面看英文标题行）
        for i, p in enumerate(pages):
            pr = p.get("prompt") or ""
            scene = pr.split("构图要求", 1)[0]
            if word and word.lower() not in scene.lower():
                add("R5", "%s 第%d条: 场景段未出现核心词 %r" % (code, i, word))

        # R6 全局约定字段覆盖（整本只算一次）
        head = c.get("global_fields") or {}
        for f in GLOBAL_FIELDS:
            if not head.get(f):
                add("R6", "%s: 缺字段 %s" % (code, f))

        # R7 每页角色一致性 / 场景一致性
        for i, p in enumerate(pages):
            pr = p.get("prompt") or ""
            if "角色一致性" not in pr:
                add("R7", "%s 第%d条: 缺「角色一致性」" % (code, i))
            if "场景一致性" not in pr:
                add("R7", "%s 第%d条: 缺「场景一致性」" % (code, i))

        # R8 大小写形态（复用 l4_case_check）
        if L4 and word:
            try:
                header, parsed = L4.parse_pages("\n".join(
                    ["旁白: %s" % p.get("narration", "") for p in pages]))
                for i, pg in enumerate(parsed):
                    exp = L4.expected_forms(word, pg["narration"], str(i), i == 0)
                    variants = L4.scan_prompt_variants(word, pages[i].get("prompt", ""))
                    for tok in variants:
                        n = L4.norm(tok)
                        if n in exp:
                            continue
                        if n == word.lower() and i != 0:
                            continue
                        add("R8", "%s 第%d条: 画面词 %r 与文稿形态 %s 不一致" % (code, i, tok, sorted(exp) or "未出现"))
            except Exception as e:
                add("R8", "%s: 判据异常 %r" % (code, e))

        # R9 提示词不得混入 URL
        for i, p in enumerate(pages):
            pr = p.get("prompt") or ""
            if re.search(r"https?://|www\.|notion\.so", pr, flags=re.I):
                add("R9", "%s 第%d条: 提示词混入链接" % (code, i))

        # R10 封面旁白行格式「封面（中 / 英）」
        if pages:
            first = pages[0].get("narration") or ""
            if not (first.startswith("封面") and "/" in first):
                add("R10", "%s: 首条旁白 %r 不符合「封面（中 / 英）」" % (code, first[:40]))

        # R11 页面英文词数 ≤ 10（领读模式禁止项）
        for i, p in enumerate(pages):
            e = eng_part(p.get("narration") or "")
            n = len(re.findall(r"[A-Za-z][A-Za-z'\-]*", e))
            if n > 10:
                add("R11", "%s 第%d条: 英文 %d 词 > 10" % (code, i, n))

        # R12 旁白表：英文含词的行，中文须同现该词（封面行豁免）
        rows = c.get("narration_rows") or []
        for r_i, cells in enumerate(rows):
            if len(cells) < 3:
                continue
            page, en, cn = cells[0], cells[1], cells[2]
            if "封面" in (page or ""):
                continue
            if word and word.lower() in (en or "").lower() and word.lower() not in (cn or "").lower():
                add("R12", "%s %s: 英文含 %s 中文列未同现（%r）" % (code, page, word, (cn or "")[:30]))

        results.append({"code": code, "状态": c.get("状态"), "核心词": word, "页数": n_l4, "fails": fails})

    RULES = [
        ("R1", "L4 页数 == 旁白表数据行数", "两者字符串计数"),
        ("R2", "封面 3:4、内页 16:9", "逐页 比例: 字段等值"),
        ("R3", "页面类型 ∈ 现行四类词表", "去 Pn 前缀与括注后严格匹配"),
        ("R4", "每页「构图要求」含三要素", "80% / 10% / 不得进入预留区"),
        ("R5", "每页场景段出现核心词（在不在）", "构图要求之前的段落，大小写不敏感"),
        ("R6", "【全局设计约定】字段齐全", "12 个字段名逐一 grep"),
        ("R7", "每页含角色一致性+场景一致性", "逐页字符串包含"),
        ("R8", "画面词大小写形态 == 文稿形态", "复用 tools/l4_case_check.py 判定"),
        ("R9", "提示词不混入链接", "正则 http/https/www/notion"),
        ("R10", "首条旁白为「封面（中 / 英）」", "前缀+斜杠"),
        ("R11", "单页英文 ≤ 10 词", "英文段词数正则"),
        ("R12", "英文含词行中文须同现（封面豁免）", "grammar_check 硬闸口径"),
    ]

    L = ["# 规则 × 成果 盘点（机器判据部分）", ""]
    L.append("语料：近 10 天、状态∈{待生图,已制作} 的 **%d 本**；每本取其 Notion 页面正文里的 L4 代码块。" % len(corpus))
    L.append("规则源：`picturebook-creator/SKILL.md`（11.1.8-codex.10）。")
    L.append("")
    L.append("| 判据 | 内容 | 口径 | 通过/样本 | 判定 |")
    L.append("|---|---|---|---|---|")
    verdict = {}
    for rid, name, how in RULES:
        total = len(results)
        ok = sum(1 for r in results if rid not in r["fails"])
        rate = ok / total if total else 0
        tag = "匹配" if rate >= 0.9 else ("部分匹配" if rate >= 0.6 else "冲突")
        verdict[rid] = {"ok": ok, "total": total, "rate": rate, "tag": tag,
                        "name": name, "how": how}
        L.append("| %s | %s | %s | **%d/%d** | %s |" % (rid, name, how, ok, total, tag))
    L.append("")
    L.append("## 失败明细（按判据，最多各 12 条）")
    for rid, name, _ in RULES:
        rows = [(r["code"], d) for r in results for d in r["fails"].get(rid, [])]
        if not rows:
            continue
        L.append("")
        L.append("### %s · %s（%d 条）" % (rid, name, len(rows)))
        for code, d in rows[:12]:
            L.append("- " + d)
        if len(rows) > 12:
            L.append("- …另有 %d 条" % (len(rows) - 12))

    json.dump({"verdict": verdict, "results": results},
              open(os.path.join(out_dir, "verdict.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    open(os.path.join(out_dir, "report.md"), "w", encoding="utf-8").write("\n".join(L))
    print("\n".join(L[:40]))
    print("\n写出:", os.path.join(out_dir, "report.md"))


if __name__ == "__main__":
    main()
