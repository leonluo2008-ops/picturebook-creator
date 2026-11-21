"""从 Codex 版 SKILL.md 抽「可机检断言」与「路径/命令引用」，供规则×成果盘点使用。
输出: rules.json + rules.md（都在输出目录）
只读源文件。
"""
import io
import json
import os
import re
import sys

ROOT = r"E:\OneDrive\工作文件夹\儿童绘本\codex-workspace\picturebook-creator"
SKILL = os.path.join(ROOT, "SKILL.md")

ASSERT_KW = ("必须", "禁止", "硬规则", "硬约束", "不得", "一律", "只能", "固定", "判据",
             "EXIT", "机审", "强制", "绝对", "不许", "永不", "⚠️")
REF_RE = re.compile(r"(?<![\w/])((?:references|scripts|tools|projects)/[A-Za-z0-9_\-./%]+)")
CMD_RE = re.compile(r"(python3?|bash|node|powershell)\s+([A-Za-z0-9_\-./\\]+)")


def main():
    outdir = sys.argv[1]
    os.makedirs(outdir, exist_ok=True)
    lines = io.open(SKILL, encoding="utf-8").read().splitlines()

    headings, asserts = [], []
    cur_h1 = cur_h2 = cur_h3 = ""
    for i, ln in enumerate(lines, 1):
        m = re.match(r"^(#{1,4})\s+(.*)$", ln)
        if m:
            lvl = len(m.group(1))
            txt = m.group(2).strip()
            if lvl == 1:
                cur_h1, cur_h2, cur_h3 = txt, "", ""
            elif lvl == 2:
                cur_h2, cur_h3 = txt, ""
            elif lvl == 3:
                cur_h3 = txt
            headings.append({"line": i, "level": lvl, "text": txt,
                             "path": " / ".join([x for x in (cur_h1, cur_h2, cur_h3) if x])})
            continue
        if any(k in ln for k in ASSERT_KW) and len(ln.strip()) > 8:
            asserts.append({"line": i, "section": cur_h2 or cur_h1, "text": ln.strip()})

    refs = {}
    for i, ln in enumerate(lines, 1):
        for m in REF_RE.finditer(ln):
            p = m.group(1).rstrip(".,;)")
            refs.setdefault(p, []).append(i)
        for m in CMD_RE.finditer(ln):
            p = m.group(2).rstrip(".,;)")
            if "/" in p or "\\" in p or p.endswith(".py"):
                refs.setdefault("@" + p, []).append(i)

    # 判定引用是否存在
    checked = []
    for p, lns in sorted(refs.items()):
        kind = "cmd" if p.startswith("@") else "path"
        target = p.lstrip("@")
        if kind == "cmd" and not (target.endswith(".py") or target.endswith(".mjs")):
            checked.append({"ref": p, "kind": kind, "exists": None, "lines": lns[:8]})
            continue
        # 相对 skill 根；也试 projects/<code>/ 下的相对
        cands = [os.path.join(ROOT, target.replace("/", os.sep))]
        cands += [os.path.join(ROOT, "projects", d, target.replace("/", os.sep))
                  for d in os.listdir(os.path.join(ROOT, "projects"))[:200]
                  if os.path.isdir(os.path.join(ROOT, "projects", d))] if target.startswith("projects/") is False else []
        exists = any(os.path.exists(c) for c in cands)
        checked.append({"ref": p, "kind": kind, "exists": exists, "lines": lns[:8]})

    json.dump({"headings": headings, "asserts": asserts, "refs": checked},
              open(os.path.join(outdir, "rules.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    L = []
    L.append("# SKILL.md 规则候选清单（Codex 版 11.1.8-codex.10）")
    L.append("")
    L.append("源: %s" % SKILL)
    L.append("总行数: %d；章节标题 %d 个；含断言关键词的行 %d 条；引用 %d 个" % (
        len(lines), len(headings), len(asserts), len(checked)))
    L.append("")
    L.append("## 一、章节结构（行号）")
    for h in headings:
        L.append("%5d  %s%s" % (h["line"], "  " * (h["level"] - 1), h["text"]))
    L.append("")
    L.append("## 二、引用与死链核对")
    L.append("")
    L.append("| 引用 | 类型 | 存在 | 出现行 |")
    L.append("|---|---|---|---|")
    for c in checked:
        L.append("| `%s` | %s | %s | %s |" % (
            c["ref"], c["kind"], "是" if c["exists"] else ("否" if c["exists"] is False else "n/a"),
            ",".join(str(x) for x in c["lines"])))
    L.append("")
    L.append("## 三、断言候选（含行号，待逐条定可机检形式）")
    L.append("")
    for a in asserts:
        L.append("%5d  [%s] %s" % (a["line"], a["section"], a["text"]))
    open(os.path.join(outdir, "rules.md"), "w", encoding="utf-8").write("\n".join(L))
    print("写出 %s (headings=%d asserts=%d refs=%d)" % (outdir, len(headings), len(asserts), len(checked)))


if __name__ == "__main__":
    main()
