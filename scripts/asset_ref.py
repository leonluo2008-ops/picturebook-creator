#!/usr/bin/env python3
"""Notion 绘本资产图库 CLI —— picturebook-creator「参考图资产」定位与联动。

零依赖（只用标准库 urllib）。角色/场景/物件参考图统一存 Notion「绘本资产图库」，
L1 定型时从库里定位资产，L4 交付时告诉生图的人去哪拿图，L5 归档时把资产行
relation 到台账排产行。

⚠️ 两套 API 版本并存（实测口径）：
- 资产图库：Notion-Version 2022-06-28（该库 data_sources 为空，新版 query 不可用）
- 排产台账：复用 notion_archive.py 的 resolve_row（新版 data_sources 链路）

────────────────────────────────────────────────────────────────
1) 列出资产（--type 按「资产类型」筛选；不筛=全部）
   python3 scripts/asset_ref.py --list
   python3 scripts/asset_ref.py --list --type 角色

2) 定位一条资产（打印全部字段 + S3 下载地址；--download 顺手存本地）
   python3 scripts/asset_ref.py --name 跳跳虎
   python3 scripts/asset_ref.py --name 跳跳虎 --download C:/tmp/ref.png

3) 把资产行 relation 到台账排产行（按核心词查行，幂等——已关联不重复加）
   python3 scripts/asset_ref.py --name 跳跳虎 --link-word bike

环境：NOTION_API_KEY（同 notion_archive.py 的读取链路）；出网走本机代理。
失败即 exit 1。
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from notion_archive import load_key, resolve_row, resolve_data_source  # 复用 key/台账查行/数据源解析链路

# 出网铁律：默认挂本机代理，环境里已有则以环境为准
os.environ.setdefault("HTTP_PROXY", "http://127.0.0.1:7897")
os.environ.setdefault("HTTPS_PROXY", "http://127.0.0.1:7897")

NOTION_BASE = "https://api.notion.com"
ASSET_DB_ID = "46d08001922c4ea9b329c1ac43977d2e"   # 绘本资产图库
ASSET_API_VERSION = "2022-06-28"                   # 该库必须走老版 query（实测）


# ─────────────────────────── 请求封装 ────────────────────────────
def _req(path: str, method: str = "GET", body=None):
    req = urllib.request.Request(
        NOTION_BASE + path,
        method=method,
        data=json.dumps(body).encode("utf-8") if body is not None else None,
        headers={
            "Authorization": f"Bearer {load_key()}",
            "Notion-Version": ASSET_API_VERSION,
            "Content-Type": "application/json",
        },
    )
    return json.load(urllib.request.urlopen(req, timeout=60))


def _plain(rich_list) -> str:
    return "".join(x.get("plain_text", "") for x in rich_list or [])


# ─────────────────────────── 资产读写 ────────────────────────────
def query_assets(asset_type: str = "") -> list:
    body = {"page_size": 100}
    if asset_type:
        body["filter"] = {"property": "资产类型", "select": {"equals": asset_type}}
    rows, cursor = [], None
    while True:
        if cursor:
            body["start_cursor"] = cursor
        res = _req(f"/v1/databases/{ASSET_DB_ID}/query", "POST", body)
        rows.extend(res.get("results", []))
        if not res.get("has_more"):
            return rows
        cursor = res.get("next_cursor")


def row_fields(row: dict) -> dict:
    p = row.get("properties") or {}
    files = (p.get("参考图片") or {}).get("files") or []
    urls = [(f.get("name", ""), (f.get("file") or {}).get("url", "")) for f in files]
    return {
        "id": row["id"],
        "name": _plain((p.get("资产名称") or {}).get("title")),
        "type": ((p.get("资产类型") or {}).get("select") or {}).get("name", ""),
        "use": ((p.get("使用定位") or {}).get("select") or {}).get("name", ""),
        "tags": [t["name"] for t in ((p.get("标签") or {}).get("multi_select") or [])],
        "source": (p.get("来源链接") or {}).get("url") or "",
        "note": _plain((p.get("复用说明") or {}).get("rich_text")),
        "files": urls,
        "relations": [r["id"] for r in ((p.get("关联排产") or {}).get("relation") or [])],
    }


def find_asset(name: str) -> dict:
    """按「资产名称」精确匹配；多行命中报错，禁止猜。"""
    hits = [row_fields(r) for r in query_assets() if row_fields(r)["name"] == name]
    if not hits:
        raise SystemExit(f"✗ 资产图库没有叫「{name}」的行（先在 Notion 建行传图，或检查名称）")
    if len(hits) > 1:
        ids = ", ".join(h["id"] for h in hits)
        raise SystemExit(f"✗ 「{name}」命中 {len(hits)} 行，禁止猜：{ids}")
    return hits[0]


def download(url: str, dest: str) -> str:
    """S3 签名 URL 只支持 GET（HEAD 会 403），现取现用。"""
    req = urllib.request.Request(url)  # 签名 URL 不带 Auth 头
    data = urllib.request.urlopen(req, timeout=120).read()
    Path(dest).write_bytes(data)
    return f"{dest}（{len(data)} bytes）"


def link_to_ledger(asset: dict, word: str) -> str:
    """把资产行 relation 到核心词所在台账行（幂等）。返回排产号。

    Notion 关系属性写入格式是 [{id: ...}] 对象数组；读回来的 relations
    有时是裸 id 字符串列表，直接拼回 body 必 400，逐个包成对象再发。
    """
    ledger = resolve_row(resolve_data_source(), word, False, "", "")
    page_id, sched_no = ledger["id"], ledger.get("_排产号", "")
    if page_id in asset["relations"]:
        return f"{sched_no}（已关联，跳过）"
    body = {"properties": {"关联排产": {"relation": [{"id": rid} for rid in asset["relations"]] + [{"id": page_id}]}}}
    _req(f"/v1/pages/{asset['id']}", "PATCH", body)
    return sched_no


def ledger_words_of(relations: list) -> list:
    """反查 relation 台账行的核心词（列表展示用，单行 GET）。"""
    words = []
    for rid in relations:
        try:
            page = _req(f"/v1/pages/{rid}")
            p = page.get("properties") or {}
            w = _plain((p.get("核心词") or {}).get("rich_text") or (p.get("核心词") or {}).get("title"))
            if w:
                words.append(w)
        except Exception:
            words.append(rid[:8])
    return words


# ─────────────────────────────── main ────────────────────────────
def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="绘本资产图库：定位参考图 / 下载 / 关联台账")
    ap.add_argument("--list", action="store_true", help="列出资产（可配 --type 筛选）")
    ap.add_argument("--type", default="", help="按「资产类型」筛选（角色/场景/物件…）")
    ap.add_argument("--name", default="", help="按「资产名称」精确定位一条资产")
    ap.add_argument("--download", default="", help="把该资产的图下载到本地路径（配 --name）")
    ap.add_argument("--link-word", default="", help="把该资产 relation 到此核心词的台账行（配 --name）")
    args = ap.parse_args()

    if args.list:
        rows = query_assets(args.type)
        if not rows:
            print(f"（资产图库暂无{'「' + args.type + '」类型的 ' if args.type else ''}资产）")
            return 0
        for r in rows:
            f = row_fields(r)
            words = ledger_words_of(f["relations"])
            print(f"- {f['name']} | {f['type']} | 定位:{f['use']} | 图×{len(f['files'])} | 关联排产:{'、'.join(words) or '—'}")
            if f["note"]:
                print(f"    复用说明: {f['note']}")
        return 0

    if args.name:
        asset = find_asset(args.name)
        print(f"✓ 资产：{asset['name']}（{asset['type']}｜定位:{asset['use']}）")
        print(f"  页面: https://www.notion.so/{asset['id'].replace('-', '')}")
        if asset["source"]:
            print(f"  来源: {asset['source']}")
        if asset["note"]:
            print(f"  复用说明: {asset['note']}")
        if not asset["files"]:
            raise SystemExit("✗ 该行「参考图片」为空，先在 Notion 上传图片")
        for fname, furl in asset["files"]:
            print(f"  图: {fname}")
            print(f"  下载地址(临时签名,现取现用): {furl[:120]}…")
        if args.download:
            print("  ↓ " + download(asset["files"][0][1], args.download))
        if args.link_word:
            sched = link_to_ledger(asset, args.link_word)
            print(f"  ✓ 已关联台账行（核心词 {args.link_word} → 排产号 {sched}）")
        return 0

    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
