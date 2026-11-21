"""只读查询 Notion 绘本台账库。凭据仅在进程内从 Hermes .env 加载，不打印值。
输出: JSON 到 --out 指定文件。零写操作（只用 GET）。
"""
import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone

ENV_PATH = r"C:\Users\leon3\AppData\Local\hermes\.env"
NOTION_VERSION = "2022-06-28"
DB_ID_RAW = "3e0a3f9269aa81a6a5b5e2bb7962e207"


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


def api(key, path, body=None, method="GET"):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        "https://api.notion.com/v1" + path,
        data=data,
        method=method,
        headers={
            "Authorization": "Bearer " + key,
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        return {"__error__": e.code, "body": e.read().decode("utf-8", "replace")[:2000]}


def plain(prop):
    t = prop.get("type")
    v = prop.get(t) if t else None
    if v is None:
        return None
    if t == "title":
        return "".join(x.get("plain_text", "") for x in v)
    if t == "rich_text":
        return "".join(x.get("plain_text", "") for x in v)
    if t == "select":
        return v.get("name")
    if t == "status":
        return v.get("name")
    if t == "multi_select":
        return [x.get("name") for x in v]
    if t == "date":
        return v.get("start")
    if t in ("number", "checkbox", "url"):
        return v
    if t == "unique_id":
        return "{}{}".format(v.get("prefix") or "", v.get("number"))
    if t == "files":
        return [x.get("name") for x in v]
    return str(v)[:200]


def main():
    out_path = sys.argv[1]
    env = load_env(ENV_PATH)
    key = env.get("NOTION_API_KEY")
    if not key:
        json.dump({"error": "NOTION_API_KEY 未在 Hermes .env 中找到"}, open(out_path, "w", encoding="utf-8"), ensure_ascii=False)
        return 2

    db_id = fmt_id(DB_ID_RAW)
    result = {"db_id": db_id}

    meta = api(key, "/databases/" + db_id)
    if "__error__" in meta:
        page = api(key, "/pages/" + db_id)
        result["as_page_error"] = meta
        result["as_page"] = {"object": page.get("object"), "parent": page.get("parent")}
        if page.get("parent", {}).get("database_id"):
            db_id = page["parent"]["database_id"]
            result["db_id_from_page_parent"] = db_id
            meta = api(key, "/databases/" + db_id)
    if "__error__" in meta:
        result["db_meta"] = meta
        json.dump(result, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        return 3

    result["db_title"] = "".join(x.get("plain_text", "") for x in meta.get("title", []))
    result["properties"] = {k: v.get("type") for k, v in meta.get("properties", {}).items()}

    rows = []
    cursor = None
    pages_fetched = 0
    while True:
        body = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        resp = api(key, "/databases/" + db_id + "/query", body=body, method="POST")
        if "__error__" in resp:
            result["query_error"] = resp
            break
        pages_fetched += 1
        for p in resp.get("results", []):
            props = p.get("properties", {})
            row = {
                "page_id": p.get("id"),
                "created": p.get("created_time"),
                "last_edited": p.get("last_edited_time"),
                "url": p.get("url"),
            }
            for k, v in props.items():
                row[k] = plain(v)
            rows.append(row)
        if not resp.get("has_more"):
            break
        cursor = resp.get("next_cursor")

    result["pages_fetched"] = pages_fetched
    result["row_count"] = len(rows)

    cutoff = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
    recent = [r for r in rows if (r.get("last_edited") or "") >= cutoff]
    statuses = sorted({str(r.get("状态")) for r in rows if r.get("状态") is not None})
    result["status_values"] = statuses
    result["recent_10d_count"] = len(recent)
    result["recent_10d"] = sorted(recent, key=lambda r: r.get("last_edited") or "", reverse=True)
    result["all_rows"] = rows
    json.dump(result, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
