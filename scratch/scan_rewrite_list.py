#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""扫描制作清单全部成员：围栏计数 / 标题粘连 / 简介段，输出需重归清单。"""
import sys
sys.path.insert(0, 'scripts')
import notion_archive as na

rows, cur = [], None
while True:
    body = {"page_size": 100}
    if cur:
        body["start_cursor"] = cur
    else:
        body["filter"] = {"or": [
            {"property": "状态", "select": {"equals": "待生图"}},
            {"property": "状态", "select": {"equals": "修改中"}},
            {"property": "状态", "select": {"equals": "有问题"}},
        ]}
    r = na.api(f"/v1/data_sources/{na.DEFAULT_DATA_SOURCE_ID}/query", "POST", body)
    rows.extend(r.get("results", []))
    if not r.get("has_more"):
        break
    cur = r.get("next_cursor")

need_rewrite = []
for row in rows:
    pid = row["id"]
    props = row.get("properties") or {}
    def rt(name):
        p = props.get(name) or {}
        return "".join(x.get("plain_text", "") for x in (p.get("rich_text") or p.get("title") or []))
    sched = rt("排产号")
    md = na.api(f"/v1/pages/{pid}/markdown").get("markdown", "")
    fences = md.count("```")
    n_creative = md.count("创作产出")
    glue = "创作产出" in md and "英文标题" in md
    # 粘连：英文标题行含 CJK
    import re
    m = re.search(r"英文标题[:：]\s*([^\n<]+)", md)
    glue_hit = bool(m and re.search(r"[\u4e00-\u9fff]", m.group(1)))
    title_seg = "选定标题" in md
    brief_seg = "选定简介" in md
    dup = n_creative > 1 or fences > 2
    flag = []
    if dup: flag.append(f"重复段(产出x{n_creative},围栏{fences})")
    if glue_hit: flag.append("标题粘连")
    if not title_seg: flag.append("缺标题段")
    if not brief_seg: flag.append("缺简介段")
    status = "REWRITE" if (dup or glue_hit) else "OK"
    if flag:
        print(f"{sched:6s} {status:8s} {'; '.join(flag)}")
    if status == "REWRITE":
        need_rewrite.append(sched)
print("\n需重归:", need_rewrite)
