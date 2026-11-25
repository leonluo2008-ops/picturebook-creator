#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""台账全量只读盘点：排产号/核心词/状态/备注是否含「全自动创作」"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scripts'))
import notion_archive as na

def main():
    ds = na.resolve_data_source()
    rows, cursor = [], None
    while True:
        body = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        res = na.api(f"/v1/data_sources/{ds}/query", "POST", body)
        rows.extend(res.get("results", []))
        if not res.get("has_more"):
            break
        cursor = res.get("next_cursor")
    def prop(r, name):
        p = r.get("properties", {}).get(name, {})
        t = p.get("type")
        if t == "title":
            parts = p.get("title") or []
            return "".join(x.get("plain_text", "") for x in parts)
        if t == "rich_text":
            parts = p.get("rich_text") or []
            return "".join(x.get("plain_text", "") for x in parts)
        if t == "select":
            s = p.get("select")
            return s.get("name", "") if s else ""
        return ""
    print("排产号\t核心词\t状态\t全自动\t备注40字")
    for r in rows:
        no = prop(r, "排产号"); w = prop(r, "核心词"); st = prop(r, "状态"); note = prop(r, "备注")
        auto = "Y" if "全自动创作" in note else "-"
        note40 = note.replace("\n", " ")[:40]
        print(f"{no}\t{w}\t{st}\t{auto}\t{note40}")

if __name__ == "__main__":
    main()
