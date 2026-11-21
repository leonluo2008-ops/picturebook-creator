# -*- coding: utf-8 -*-
"""通用只读：按 database_id 拉 schema + 全部行；可再按关键词抓页面正文。
凭据仅在进程内从 Hermes .env 加载，不打印。只发 GET/POST query（只读）。
用法:
  python read_db.py <db_id_raw_32hex> <out_prefix> [--body 关键词] [--max-body 10]
"""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

ENV_PATH = r"C:\Users\leon3\AppData\Local\hermes\.env"
NOTION_VERSION = "2022-06-28"


def load_env(path):
    d = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            d[k.strip()] = v.strip().strip('"').strip("'")
    return d


def fmt_id(raw):
    raw = raw.replace("-", "")
    return "-".join([raw[0:8], raw[8:12], raw[12:16], raw[16:20], raw[20:32]])


def api(key, path, body=None, method="GET", tries=5):
    last = None
    for attempt in range(tries):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(
            "https://api.notion.com/v1" + path, data=data, method=method,
            headers={"Authorization": "Bearer " + key, "Notion-Version": NOTION_VERSION,
                     "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            txt = e.read().decode("utf-8", "replace")[:500]
            if e.code == 429 or e.code >= 500:
                last = {"__error__": e.code, "body": txt}
                time.sleep(2 * (attempt + 1)); continue
            return {"__error__": e.code, "body": txt}
        except Exception as e:
            last = {"__error__": "net", "body": repr(e)[:200]}
            time.sleep(2 * (attempt + 1))
    return last


def plain(prop):
    t = prop.get("type"); v = prop.get(t) if t else None
    if v is None:
        return None
    if t in ("title", "rich_text"):
        return "".join(x.get("plain_text", "") for x in v)
    if t in ("select", "status"):
        return v.get("name")
    if t == "multi_select":
        return [x.get("name") for x in v]
    if t == "date":
        return v.get("start")
    if t == "files":
        return [x.get("name") for x in v]
    if t in ("number", "checkbox", "url"):
        return v
    return None


def rich(arr):
    return "".join(x.get("plain_text", "") for x in arr or [])


def block_text(b):
    t = b.get("type"); p = b.get(t, {})
    if t == "table_row":
        return " | ".join(rich(c) for c in p.get("cells", []))
    return rich(p.get("rich_text"))


def dump_body(key, block_id, lines, depth=0):
    cursor = None
    while True:
        path = "/blocks/%s/children?page_size=100%s" % (block_id, ("&start_cursor=" + cursor) if cursor else "")
        resp = api(key, path)
        if "__error__" in resp:
            lines.append("[ERR] " + json.dumps(resp, ensure_ascii=False)[:200]); return
        for b in resp.get("results", []):
            lines.append(("  " * depth) + "[%s] %s" % (b.get("type"), block_text(b)))
            if b.get("has_children") and depth < 3:
                dump_body(key, b["id"], lines, depth + 1)
        if not resp.get("has_more"):
            return
        cursor = resp.get("next_cursor")


def main():
    db_raw = sys.argv[1]
    out_prefix = sys.argv[2]
    kw = None
    max_body = 10
    if "--body" in sys.argv:
        kw = sys.argv[sys.argv.index("--body") + 1]
    if "--max-body" in sys.argv:
        max_body = int(sys.argv[sys.argv.index("--max-body") + 1])

    env = load_env(ENV_PATH)
    key = env.get("NOTION_API_KEY")
    if not key:
        print("NOTION_API_KEY 缺失"); return 2
    db_id = fmt_id(db_raw)
    result = {"db_id": db_id}

    meta = api(key, "/databases/" + db_id)
    if "__error__" in meta:
        result["meta_error"] = meta
        json.dump(result, open(out_prefix + ".json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("meta 失败:", meta); return 3

    result["title"] = "".join(x.get("plain_text", "") for x in meta.get("title", []))
    result["properties"] = {k: v.get("type") for k, v in meta.get("properties", {}).items()}
    # 找到 data_source_id（Notion 新版：query 走 data_sources）
    ds_id = None
    for d in meta.get("data_sources", []) or []:
        ds_id = d.get("id"); break

    rows, cursor = [], None
    while True:
        body = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        if ds_id:
            resp = api(key, "/data_sources/%s/query" % ds_id, body=body, method="POST")
        else:
            resp = api(key, "/databases/%s/query" % db_id, body=body, method="POST")
        if "__error__" in resp:
            result["query_error"] = resp
            break
        for p in resp.get("results", []):
            row = {"page_id": p.get("id"), "url": p.get("url"),
                   "created": p.get("created_time"), "last_edited": p.get("last_edited_time")}
            for k, v in (p.get("properties") or {}).items():
                row[k] = plain(v)
            rows.append(row)
        if not resp.get("has_more"):
            break
        cursor = resp.get("next_cursor")

    result["ds_id"] = ds_id
    result["row_count"] = len(rows)
    result["rows"] = rows

    # 关键词筛正文
    if kw:
        hits = []
        pat = re.compile(kw, re.I)
        picked = 0
        for r in rows:
            if picked >= max_body:
                break
            blob = json.dumps(r, ensure_ascii=False)
            if pat.search(blob):
                lines = []
                dump_body(key, r["page_id"], lines)
                body = "\n".join(lines)
                fn = "%s.body.%s.txt" % (out_prefix, (r.get("排产号") or r.get("资产名称") or r["page_id"])[:12])
                open(fn, "w", encoding="utf-8").write(body)
                hits.append({"page_id": r["page_id"], "file": fn, "chars": len(body)})
                picked += 1
        result["body_hits"] = hits

    json.dump(result, open(out_prefix + ".json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("库标题:", result["title"])
    print("属性:", json.dumps(result["properties"], ensure_ascii=False))
    print("行数:", result["row_count"], " data_source:", ds_id)
    print("写出:", out_prefix + ".json")
    if result.get("query_error"):
        print("查询错误:", result["query_error"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
