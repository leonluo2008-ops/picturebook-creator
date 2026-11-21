# ⚠️ 历史一次性补丁（2026-11-21 搬迁前布局）：docs/ 与 tools/ 已移入 picturebook-creator 仓内。
#    本脚本内的相对路径按搬迁前（工作区根）写；如需重放，把 JOBS 里的 `docs/` 改为仓内 `docs/` 的对应路径。
# -*- coding: utf-8 -*-
"""V10 批 B1/B2/B4/B7/B8/B9/B10：文档层闭合两路审计。

依据：轻活路 6 条 P0 + 重活路 5 条 BLOCKING 的并集（见 docs/nodes/V10-规则层收口.md）。
本脚本只改文档（SKILL.md 与 docs/），不改脚本行为；脚本修复在下一批（B3/B5/B6）。

用法: python apply_moduleV10_docs.py <workspace_root> [--check]
"""
import io
import os
import re
import sys

ROOT_MARK = r"E:\OneDrive\工作文件夹\儿童绘本\codex-workspace"

JOBS = [
    # ── B1：G4 被旧条款反向授权（重活路 BLOCKING） ──
    ("picturebook-creator/SKILL.md", "B1-短句串联反向授权",
     "> 词族拓展保留时，旁白带读完整词，可用自然的短句串联。入选仍按边界条件核对，发音或拼写规律仅用于选词。",
     "> 词族拓展保留时，旁白带读完整词；**词族页英文列用词表（逗号分隔单词），不写成句子、不加引导句**（见「词族拓展页执行细则」第 1 条）。入选仍按边界条件核对，发音或拼写规律仅用于选词。"),

    # ── B2：G8 反面示例仍在正文（重活路 BLOCKING） ──
    ("picturebook-creator/SKILL.md", "B2-纯英文示例",
     "旁白: A little cat on a mat.",
     "旁白: A little cat on a mat. / 小猫咪坐在垫子上。"),

    # ── I1：G8 缺封面例外（两路都提） ──
    ("picturebook-creator/SKILL.md", "I1-封面行例外",
     "机审与本 skill 的脚本按 `/` 前为英文、`/` 后为中文解析。",
     "机审与本 skill 的脚本按 `/` 前为英文、`/` 后为中文解析。**封面行例外**：封面写成 `封面（[中文标题] / [英文标题]）`——中文在前、英文在后（与内页相反），脚本按此解析。"),

    # ── B4：--expect-pages 落地成坏命令（重活路 BLOCKING） ──
    ("picturebook-creator/SKILL.md", "B4-页数断言只对门禁3",
     "**建议三条门禁都带 `--expect-pages <页数>`**：不带时脚本只校验解析到的页，页数漏解析会静默放过。",
     "**门禁 3（`l4_presence_check.py`）必须带 `--expect-pages <页数>`**：不带时它只校验解析到的页，页数漏解析会静默放过。**另两道（grammar_check / l4_case_check）没有这个参数，传了会 `exit 2`。**"),

    # ── I3：presence 词族页不再自动跳过，改口径 ──
    ("picturebook-creator/SKILL.md", "I3-词族页用法改写",
     "- **词族拓展页例外**：该页的教学载体是词族词（如 ball / tall / wall），不要求核心词入画——脚本对这类页自动跳过并在输出里点名；改按「页内列出的每个词族词都在位」人工核对。",
     "- **词族拓展页例外**：该页教学载体是词族词（如 ball / tall / wall），不要求核心词入画——**必须给 `l4_presence_check.py` 传 `--page-words \"<页号>=词1,词2\"` 逐页指定本页词集**，否则门禁会按核心词判缺；再用 `l4_structure_check.py --family-words` 核对词族词是否都在位。"),

    # ── P1：G6 的理由算错（重活路 POLISH） ──
    ("picturebook-creator/SKILL.md", "P1-词族数理由",
     "；超过 4 个会挤爆「每页 10 词」上限。",
     "（理由：画面容得下的格数与朗读节奏；**不是**「每页 10 词」上限——实测 4 词=4 词、6 词=6 词，都远低于 10 词硬上限）。"),

    # ── I2：词表与「句子完整」冲突，加豁免 ──
    ("picturebook-creator/SKILL.md", "I2-句子完整豁免",
     "- 句子完整，主语不能省略到读不懂（祈使句除外）",
     "- 句子完整，主语不能省略到读不懂（祈使句除外）；**词族拓展页的词表行例外**（`Pot, hot, dot, cot.` 不是句子，不受本条约束）"),

    # ── B8：CHANGELOG 伪证句订正（轻活路 P0） ──
    ("picturebook-creator/CHANGELOG.md", "B8-伪证订正",
     "解析口径正确（`/` 前英文、`/` 后中文）。",
     "**（订正 2026-11-21：此句曾被视为「已有机器判据」的证据，属伪证——当时三道门禁都不按 `/` 切分、也不查双语；G8 机检在 V10 才落地，见 `docs/nodes/V10-规则层收口.md`。）**"),
]

DOC_JOBS = [
    # ── B9：L2 §4 把 G8 不合规样本列为「可信」（轻活路 P0） ──
    ("docs/项目适配包.md", "B9-五本移出可信",
     "| 5 本实测产物 | `./nodes/V7*-v13/`：四类词型覆盖，五本×五道门禁 25 次全 exit 0（**文本层**；成图未验） |",
     "| 5 本实测产物（**仅作词型覆盖与文本层证据**） | `./nodes/V7*-v13/`；⚠️ **G8 不合规样本**（coin/pot/whisper 内页旁白纯英文、pot/long 词族页写句子），**不得作验收依据**；V12 会按新口径改写 |"),

    # ── B10：L2 §9 节点表改为指针（避免与看板双真源） ──
    ("docs/项目适配包.md", "B10-L2节点表改指针",
     "| V1–V6 | 基线/分支、族4、族2+3、术语统一、双路审计、13.0.0 版本资料 | 已完成（提交见 CHANGELOG） |\n| V7 | 实测 5 本（coin / pot / whisper / long / behind，四类词型） | **文本层已交**，所有者不逐本审；成图未验 |\n| V7.5–V7.8 | 第二轮复审、结构闸、词族页补测、门禁脚本行为审计 | 已完成（`d6a623c`…`b726f34`） |\n| V8 | 归档到台账 | **本轮取消**（所有者明确：不需要更新归档库） |\n| V9 | 所有者裁定落地（G4/G6/G8 + 8 项缺口）+ 分支模型 main/dev/frozen + **v13.1.0** | 已完成（`affbadd`，tag `v13.1.0`） |\n| V10 | 本批：规则层与适配包更新 + 双路审计 + 收口 | 进行中 |",
     "> 节点清单、状态与执行顺序**只在** `./开发计划书.md` 维护（唯一真源）；本文件不复制节点表。"),
]

FILES_BANNER = [
    ("docs/nodes/V7-coin-v13/01-structure.md", "G4/G8 已翻案"),
    ("docs/nodes/V7b-pot-v13/01-structure.md", "G4/G8 已翻案"),
    ("docs/nodes/V7c-whisper-v13/01-structure.md", "G4/G8 已翻案"),
    ("docs/nodes/V7d-long-v13/01-structure.md", "G4/G8 已翻案"),
    ("docs/nodes/V7e-behind-v13/01-structure.md", "G4/G8 已翻案"),
]

BANNER = ("> ⚠️ **本形态已作废（2026-11-21）**：所有者已裁定「词族页英文列用词表、不加引导句」（G4）与「L4 旁白必须英文 / 中文双语」（G8）。\n"
          "> 本目录产物是按旧形态产出的**不合规样本**，仅作词型覆盖与文本层证据，**不得作为验收依据**；按新口径的改写见 V12（`docs/开发计划书.md` §七）。\n\n")


def patch(root, rel, rid, old, new, results):
    p = os.path.join(root, rel.replace("/", os.sep))
    if not os.path.exists(p):
        results.append((rid, rel, -1)); return
    t = io.open(p, encoding="utf-8").read()
    n = t.count(old)
    results.append((rid, rel, n))
    if n == 1:
        io.open(p, "w", encoding="utf-8", newline="").write(t.replace(old, new))


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else ROOT_MARK
    check_only = "--check" in sys.argv
    results = []
    if check_only:
        for rel, rid, old, new in JOBS:
            p = os.path.join(root, rel.replace("/", os.sep))
            n = io.open(p, encoding="utf-8").read().count(old) if os.path.exists(p) else -1
            results.append((rid, rel, n))
        for rel, rid, old, new in DOC_JOBS:
            p = os.path.join(root, rel.replace("/", os.sep))
            n = io.open(p, encoding="utf-8").read().count(old) if os.path.exists(p) else -1
            results.append((rid, rel, n))
    else:
        for rel, rid, old, new in JOBS + DOC_JOBS:
            patch(root, rel, rid, old, new, results)
        for rel, tag in FILES_BANNER:
            p = os.path.join(root, rel.replace("/", os.sep))
            if os.path.exists(p):
                t = io.open(p, encoding="utf-8").read()
                if "本形态已作废" not in t:
                    io.open(p, "w", encoding="utf-8", newline="").write(BANNER + t)
                    results.append(("BANNER", rel, 1))
                else:
                    results.append(("BANNER", rel, 0))
            else:
                results.append(("BANNER", rel, -1))

    bad = [r for r in results if r[2] != 1]
    for rid, rel, n in results:
        print("%-26s %-44s 命中 %d %s" % (rid, rel, n, "" if n == 1 else "  <<< 需查"))
    if check_only:
        print("\n[check] 未命中 %d 处" % len(bad))
        return 0 if not bad else 2
    print("\n[完成] 成功 %d 处；未命中 %d 处" % (len(results) - len(bad), len(bad)))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
