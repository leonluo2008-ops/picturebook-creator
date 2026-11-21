"""只读抓取指定排产号 Notion 页面正文（blocks，含子块），验证 L4 全文是否归档在正文里。
凭据仅在进程内加载，不打印。只发 GET。
"""
import json
import sys
import time
import urllib.request
import urllib.error

ENV_PATH = r"C:\Users\leon3\AppData\Local\hermes\.env"
NOTION_VERSION = "2022-06-28"
OUT_JSON = r"C:\Users\leon3\AppData\Local\Temp\pb-notion\out.json"


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


def api(key, path):
    last = None
    for attempt in range(5):
        req = urllib.request.Request(
            "https://api.notion.com/v1" + path,
            headers={"Authorization": "Bearer " + key, "Notion-Version": NOTION_VERSION},
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")[:800]
            if e.code == 429 or e.code >= 500:
                last = {"__error__": e.code, "body": body}
                time.sleep(1.5 * (attempt + 1))
                continue
            return {"__error__": e.code, "body": body}
        except Exception as e:  # 网络层（含 TLS 重置 10054）
            last = {"__error__": "net", "body": repr(e)[:300]}
            time.sleep(1.5 * (attempt + 1))
            continue
    return last


def rich_text(arr):
    return "".join(x.get("plain_text", "") for x in arr or [])


def block_text(b):
    t = b.get("type")
    payload = b.get(t, {})
    if t in ("paragraph", "heading_1", "heading_2", "heading_3", "quote", "code", "callout"):
        return rich_text(payload.get("rich_text"))
    if t == "bulleted_list_item" or t == "numbered_list_item" or t == "toggle":
        return rich_text(payload.get("rich_text"))
    if t == "table_row":
        return " | ".join(rich_text(c) for c in payload.get("cells", []))
    return ""


def walk(key, block_id, depth, lines, stats):
    cursor = None
    while True:
        path = "/blocks/" + block_id + "/children?page_size=100" + ("&start_cursor=" + cursor if cursor else "")
        resp = api(key, path)
        if "__error__" in resp:
            lines.append("[ERROR] " + json.dumps(resp, ensure_ascii=False)[:300])
            return
        for b in resp.get("results", []):
            stats["n"] += 1
            txt = block_text(b)
            lines.append(("  " * depth) + "[" + b.get("type", "?") + "] " + txt)
            if b.get("has_children") and depth < 3:
                walk(key, b["id"], depth + 1, lines, stats)
        if not resp.get("has_more"):
            return
        cursor = resp.get("next_cursor")


def main():
    codes = sys.argv[1].split(",")
    outp = sys.argv[2]
    env = load_env(ENV_PATH)
    key = env.get("NOTION_API_KEY")
    data = json.load(open(OUT_JSON, encoding="utf-8"))
    rows = {str(r.get("排产号")): r for r in data.get("all_rows", [])}
    result = {}
    for code in codes:
        r = rows.get(code.strip())
        if not r:
            result[code] = {"error": "该排产号不在台账里"}
            continue
        lines = []
        stats = {"n": 0}
        walk(key, r["page_id"], 0, lines, stats)
        body = "\n".join(lines)
        result[code] = {
            "page_id": r["page_id"],
            "url": r.get("url"),
            "状态": r.get("状态"),
            "核心词": r.get("核心词"),
            "词型": r.get("词型"),
            "选定标题": r.get("选定标题"),
            "选定简介": r.get("选定简介"),
            "block_count": stats["n"],
            "has_L4_heading": ("L4" in body) or ("生图提示词" in body),
            "n_旁白": body.count("旁白"),
            "n_生图提示词": body.count("生图提示词"),
            "body_len": len(body),
            "body_head": body[:1500],
        }
        fn = outp + "." + code + ".txt"
        open(fn, "w", encoding="utf-8").write(body)
        result[code]["body_file"] = fn
    json.dump(result, open(outp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    for code, v in result.items():
        print(code, "state=", v.get("状态"), "blocks=", v.get("block_count"),
              "has_L4=", v.get("has_L4_heading"), "旁白x", v.get("n_旁白"),
              "生图提示词x", v.get("n_生图提示词"), "body_len=", v.get("body_len"))


if __name__ == "__main__":
    main()
