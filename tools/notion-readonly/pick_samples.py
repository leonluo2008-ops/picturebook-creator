"""从只读查询结果里挑 N1 回归样本：近10天 + 状态∈{待生图,已制作} + 本地存在 L4 文件。
只读，不改任何文件。
"""
import json
import os
import glob
import sys

OUT_JSON = r"C:\Users\leon3\AppData\Local\Temp\pb-notion\out.json"
PROJ = r"E:\OneDrive\工作文件夹\儿童绘本\codex-workspace\picturebook-creator\projects"
TARGET = {"待生图", "已制作"}

data = json.load(open(OUT_JSON, encoding="utf-8"))
rows = data.get("recent_10d", [])
cand = [r for r in rows if r.get("状态") in TARGET]

def local_l4(code):
    d = os.path.join(PROJ, str(code).strip())
    if not os.path.isdir(d):
        return None, 0
    files = sorted(glob.glob(os.path.join(d, "L4*.txt")) + glob.glob(os.path.join(d, "l4*.txt")))
    return d, files

lines = []
lines.append("近10天行数=%d, 其中状态∈%s 的行数=%d" % (len(rows), sorted(TARGET), len(cand)))
lines.append("")
hdr = "%-8s %-6s %-14s %-10s %-30s %-12s %s"
lines.append(hdr % ("排产号", "状态", "核心词", "词型", "选定标题", "最近编辑", "本地L4文件"))
lines.append("-" * 150)
hit = []
for r in cand:
    code = r.get("排产号")
    d, files = local_l4(code)
    title = (r.get("选定标题") or "").replace("\n", " ")[:28]
    le = (r.get("last_edited") or "")[:10]
    mark = ""
    if files:
        mark = "; ".join(os.path.basename(f) for f in files)
        hit.append((code, r.get("状态"), r.get("核心词"), files))
    lines.append(hdr % (str(code), str(r.get("状态")), str(r.get("核心词"))[:14], str(r.get("词型"))[:10], title, le, mark))

lines.append("")
lines.append("=== 命中(有本地L4)候选 %d 本 ===" % len(hit))
for code, st, word, files in hit:
    lines.append("%s | %s | 核心词=%s | %s" % (code, st, word, [os.path.basename(f) for f in files]))

open(r"C:\Users\leon3\AppData\Local\Temp\pb-notion\samples.txt", "w", encoding="utf-8").write("\n".join(lines))
print("\n".join(lines[:6]))
print("... written samples.txt, hits=%d" % len(hit))
