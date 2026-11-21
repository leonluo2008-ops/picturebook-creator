"""构建「规则 × 成果」盘点的语料：拉取近 10 天、状态∈{待生图,已制作} 的绘本页面正文，
做结构化抽取，输出 corpus.json + corpus_summary.txt。

只读：仅 GET；凭据仅进程内从 Hermes .env 加载，不打印。
用法: python build_corpus.py <输出目录>
"""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

ENV_PATH = r"C:\Users\leon3\AppData\Local\hermes\.env"
NOTION_VERSION = "2022-06-28"
DB_ID = "3e0a3f92-69aa-81a6-a5b5-e2bb7962e207"
TARGET_STATUS = {"待生图", "已制作"}
RECENT_DAYS = 10


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


def api(key, path, body=None, method="GET", tries=5):
    last = None
    for attempt in range(tries):
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
            code = e.code
            txt = e.read().decode("utf-8", "replace")[:400]
            if code == 429 or code >= 500:
                last = {"__error__": code, "body": txt}
                time.sleep(2.0 * (attempt + 1))
                continue
            return {"__error__": code, "body": txt}
        except Exception as e:
            last = {"__error__": "net", "body": repr(e)[:200]}
            time.sleep(2.0 * (attempt + 1))
    return last


def plain(prop):
    t = prop.get("type")
    v = prop.get(t) if t else None
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


def rich_text(arr):
    return "".join(x.get("plain_text", "") for x in arr or [])


def block_payload(b):
    t = b.get("type")
    p = b.get(t, {})
    txt = rich_text(p.get("rich_text"))
    return t, p, txt


def walk_blocks(key, block_id, out, stats, depth=0):
    cursor = None
    while True:
        path = "/blocks/" + block_id + "/children?page_size=100" + ("&start_cursor=" + cursor if cursor else "")
        resp = api(key, path)
        if "__error__" in resp:
            out.append({"type": "__error__", "text": json.dumps(resp, ensure_ascii=False)[:300]})
            return
        for b in resp.get("results", []):
            stats["blocks"] += 1
            t, p, txt = block_payload(b)
            rec = {"type": t, "text": txt, "id": b.get("id")}
            if t == "table":
                rec["rows"] = []
            if t == "table_row":
                rec["cells"] = [rich_text(c) for c in p.get("cells", [])]
            out.append(rec)
            if b.get("has_children") and depth < 3:
                kids = []
                walk_blocks(key, b["id"], kids, stats, depth + 1)
                rec["children"] = kids
        if not resp.get("has_more"):
            return
        cursor = resp.get("next_cursor")


def flatten(blocks, acc=None):
    """把嵌套 blocks 摊平成有序列表：table 展开成 table_row，code 保留整块文本。"""
    if acc is None:
        acc = []
    for b in blocks:
        t = b.get("type")
        if t == "table":
            acc.append({"type": "__table_start__", "text": ""})
            for kid in b.get("children", []):
                if kid.get("type") == "table_row":
                    acc.append({"type": "table_row", "cells": kid.get("cells", []), "text": " | ".join(kid.get("cells", []))})
            acc.append({"type": "__table_end__", "text": ""})
        else:
            item = {"type": t, "text": b.get("text", "")}
            if t == "code":
                item["code_text"] = b.get("text", "")
            acc.append(item)
            if b.get("children"):
                flatten(b["children"], acc)
    return acc


PAGE_TYPE_KEYS = ("认知页", "语境重复页", "语境页", "语境收尾页", "词族拓展页", "词族页",
                  "互动练习页", "互动页", "字母拆解页", "拼读示范页", "故事页")
GLOBAL_FIELDS = ("目标单词", "目标词", "目标年龄", "文字风格", "主角外观", "画风", "画面风格",
                 "站位约定", "机位约定", "主要场景锚点", "场景锚点", "全书文字与配色", "核心物件", "角色一致性")
BLOCK_MARKERS = ("角色一致性", "场景一致性", "构图要求", "文字载体约定", "参考图约定")


def parse_l4(code_text):
    """解析 L4 全文 -> 页记录列表"""
    if not code_text:
        return []
    pages = []
    cur = None
    for line in code_text.splitlines():
        s = line.strip()
        m = re.match(r"^旁白[:：]\s*(.*)$", s)
        if m:
            cur = {"narration": m.group(1), "ratio": "", "ptype": "", "prompt": ""}
            pages.append(cur)
            continue
        if cur is None:
            continue
        for key, field in (("比例", "ratio"), ("页面类型", "ptype"), ("生图提示词", "prompt")):
            mm = re.match(r"^" + key + r"[:：]\s*(.*)$", s)
            if mm:
                cur[field] = mm.group(1)
                break
        else:
            if cur["prompt"]:
                cur["prompt"] += "\n" + s
    return pages


def analyze_book(key, row):
    stats = {"blocks": 0}
    raw = []
    walk_blocks(key, row["page_id"], raw, stats)
    flat = flatten(raw)
    body_text = "\n".join(x.get("text", "") for x in flat)

    # 旁白表
    narration_rows = []
    in_table = False
    for x in flat:
        if x["type"] == "__table_start__":
            in_table = True
        elif x["type"] == "__table_end__":
            in_table = False
        elif in_table and x["type"] == "table_row":
            narration_rows.append(x["cells"])

    # L4 代码块（取最长的一个 code block）
    codes = [x.get("code_text", "") for x in flat if x["type"] == "code"]
    l4 = max(codes, key=len) if codes else ""
    has_code_block = bool(codes)
    pages = parse_l4(l4)

    # 标题/简介
    title_lines, intro_lines = [], []
    for x in flat:
        t = x.get("text", "")
        if t.startswith("选定标题"):
            title_lines.append(t)
        if t.startswith("选定简介"):
            intro_lines.append(t)

    # 全局约定字段覆盖
    head = l4.split("旁白:")[0] if "旁白:" in l4 else l4[:3000]
    global_hits = {f: (f in head) for f in GLOBAL_FIELDS}
    block_hits = {b: sum(1 for p in pages if b in p["prompt"]) for b in BLOCK_MARKERS}

    page_types = [p["ptype"] for p in pages]
    ratios = [p["ratio"] for p in pages]

    # 提示词内块序（每页出现的第一批标记顺序）
    order_per_page = []
    for p in pages:
        pos = [(p["prompt"].find(b), b) for b in BLOCK_MARKERS if b in p["prompt"]]
        pos.sort()
        order_per_page.append([b for _, b in pos])

    return {
        "code": row.get("code"),
        "状态": row.get("状态"),
        "核心词": row.get("核心词"),
        "词型": row.get("词型"),
        "last_edited": row.get("last_edited"),
        "page_id": row["page_id"],
        "url": row.get("url"),
        "block_count": stats["blocks"],
        "body_chars": len(body_text),
        "has_code_block": has_code_block,
        "code_block_count": len(codes),
        "l4_chars": len(l4),
        "narration_rows": narration_rows[1:] if narration_rows and narration_rows[0] and "页码" in (narration_rows[0][0] or "") else narration_rows,
        "narration_row_count": len(narration_rows) - (1 if narration_rows and narration_rows[0] and "页码" in (narration_rows[0][0] or "") else 0),
        "title_lines": title_lines,
        "intro_lines": intro_lines,
        "l4_page_count": len(pages),
        "ratios": ratios,
        "page_types": page_types,
        "global_fields": global_hits,
        "block_marker_counts": block_hits,
        "block_order_per_page": order_per_page,
        "pages": pages,
    }


def main():
    outp = sys.argv[1]
    os.makedirs(outp, exist_ok=True)
    env = load_env(ENV_PATH)
    key = env.get("NOTION_API_KEY")
    if not key:
        print("NOTION_API_KEY 缺失")
        return 2

    rows, cursor = [], None
    while True:
        body = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        resp = api(key, "/databases/" + DB_ID + "/query", body=body, method="POST")
        if "__error__" in resp:
            print("query error", resp)
            return 3
        for p in resp.get("results", []):
            props = p.get("properties", {})
            row = {
                "page_id": p.get("id"),
                "url": p.get("url"),
                "last_edited": p.get("last_edited_time"),
            }
            for k, v in props.items():
                row[k] = plain(v)
            row["code"] = row.get("排产号")
            rows.append(row)
        if not resp.get("has_more"):
            break
        cursor = resp.get("next_cursor")

    cutoff = (datetime.now(timezone.utc) - timedelta(days=RECENT_DAYS)).isoformat()
    cand = [r for r in rows if (r.get("last_edited") or "") >= cutoff and r.get("状态") in TARGET_STATUS]
    print("台账总行 %d；近%d天且状态∈%s 的候选 %d 本" % (len(rows), RECENT_DAYS, sorted(TARGET_STATUS), len(cand)))

    corpus = []
    for i, row in enumerate(cand, 1):
        info = analyze_book(key, row)
        corpus.append(info)
        print("[%2d/%2d] %s %s 状态=%s blocks=%d 页数=%d 页面类型=%s" % (
            i, len(cand), info["code"], info["核心词"], info["状态"], info["block_count"],
            info["l4_page_count"], ",".join(sorted(set(info["page_types"])))))
        time.sleep(0.4)

    json.dump(corpus, open(os.path.join(outp, "corpus.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    # 概览
    L = []
    L.append("候选 %d 本（近%d天，状态∈%s）" % (len(cand), RECENT_DAYS, sorted(TARGET_STATUS)))
    L.append("")
    L.append("%-7s %-6s %-13s %-6s %-5s %-6s %s" % ("排产号", "状态", "核心词", "blocks", "页数", "L4字数", "页面类型"))
    for c in corpus:
        L.append("%-7s %-6s %-13s %-6d %-5d %-6d %s" % (
            c["code"], c["状态"], c["核心词"], c["block_count"], c["l4_page_count"], c["l4_chars"],
            ",".join(sorted(set(c["page_types"])))))
    L.append("")
    L.append("=== 有无 L4 代码块 ===")
    L.append("有: %d 本；无: %d 本" % (sum(1 for c in corpus if c["has_code_block"]), sum(1 for c in corpus if not c["has_code_block"])))
    L.append("")
    L.append("=== 全局约定字段覆盖（分母=有L4的书） ===")
    withl4 = [c for c in corpus if c["l4_page_count"] > 0]
    for f in GLOBAL_FIELDS:
        n = sum(1 for c in withl4 if c["global_fields"].get(f))
        L.append("  %-10s %d/%d" % (f, n, len(withl4)))
    L.append("")
    L.append("=== 每页块标记覆盖（分母=总页数） ===")
    total_pages = sum(c["l4_page_count"] for c in withl4)
    for b in BLOCK_MARKERS:
        n = sum(c["block_marker_counts"].get(b, 0) for c in withl4)
        L.append("  %-10s %d/%d 页" % (b, n, total_pages))
    open(os.path.join(outp, "corpus_summary.txt"), "w", encoding="utf-8").write("\n".join(L))
    print("写出: " + os.path.join(outp, "corpus.json") + " / corpus_summary.txt")
    return 0


if __name__ == "__main__":
    sys.exit(main())
