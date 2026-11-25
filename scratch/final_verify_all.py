#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""制作清单全量最终核验：逐本取页数与状态 → notion_verify 独立回读。"""
import io, json, re, subprocess, sys
sys.path.insert(0, 'scripts')
import notion_archive as na

res = na.api(f"/v1/data_sources/{na.DEFAULT_DATA_SOURCE_ID}/query", "POST", {
    "page_size": 100,
    "filter": {"property": "状态", "select": {"multi_select": {}} } if False else {
        "or": [
            {"property": "状态", "select": {"equals": "待生图"}},
            {"property": "状态", "select": {"equals": "修改中"}},
            {"property": "状态", "select": {"equals": "有问题"}},
        ]
    }
})
rows = []
cur = None
while True:
    body = {"page_size": 100}
    if cur:
        body["start_cursor"] = cur
    r = na.api(f"/v1/data_sources/{na.DEFAULT_DATA_SOURCE_ID}/query", "POST", body) if cur else res
    rows.extend(r.get("results", []))
    if not r.get("has_more"):
        break
    cur = r.get("next_cursor")

ok, fail = [], []
for row in rows:
    pid = row["id"]
    props = row.get("properties") or {}
    def rt(name):
        p = props.get(name) or {}
        return "".join(x.get("plain_text", "") for x in (p.get("rich_text") or p.get("title") or []))
    sched = rt("排产号")
    state = ((props.get("状态") or {}).get("select") or {}).get("name", "")
    md = na.api(f"/v1/pages/{pid}/markdown").get("markdown", "")
    pages = md.count("比例: 16:9") + 1  # 内页数 + 封面
    r = subprocess.run([sys.executable, "scripts/notion_verify.py", "--page-id", pid,
                        "--pages", str(pages), "--any-active-state"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    verdict = "PASS" if r.returncode == 0 else "FAIL"
    print(f"{sched}: {verdict} pages={pages} state={state}")
    if r.returncode != 0:
        detail = [l for l in (r.stdout or "").splitlines() if "✗" in l or "⚠" in l]
        print("   " + " | ".join(detail[:6]))
        fail.append(sched)
    else:
        ok.append(sched)

print(f"\n== 最终核验 {len(ok)} 过 / {len(fail)} 败 ==")
if fail:
    print("FAIL:", fail)
