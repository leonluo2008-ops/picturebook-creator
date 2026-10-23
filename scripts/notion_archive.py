#!/usr/bin/env python3
"""Notion 排产台账归档 CLI —— picturebook-creator「步骤 L5」的可执行实现。

零依赖（只用标准库 urllib）。L4 生图提示词确认后直接跑这一条命令即可完成归档，
不需要再让 agent 现场手写 Notion API 调用。

────────────────────────────────────────────────────────────────
1) 只定位行（只读，不写任何东西）
   python3 scripts/notion_archive.py --word day --locate

2) 完整归档（L4 确认后的默认动作）
   python3 scripts/notion_archive.py --word day \
       --title '一起学 DAY / English: Let us Learn "DAY"' \
       --brief '太阳升起是 day，玩耍的日子是 day……' \
       --narration narration.md \
       --l4 l4.md \
       --date 2026-10-23

3) 干跑（打印将要写入的 block 清单，不发写请求）
   ... 同上 ...  --dry-run

4) 指定目标行（跳过按核心词查行，用于已确认 page_id 的场合）
   ... 同上 ...  --page-id 3e0a3f92-69aa-81dd-989c-fa702010ba1c

5) 可选属性回填（默认关闭：用户 2026-10-23 明确「直接回填到正文就可以了」）
   ... 同上 ...  --attr-title --attr-brief

6) 台账没有该核心词的行时（默认行为 = 自动建行）
   · 按「核心词」精确查行：查到 → 直接用该行，**绝不重复建行**
   · 查不到 → 自动在台账新建一行（排产号取全库最大 B### +1，状态列留空交给排产流水线）
   · 想禁用自动建行：--no-create
   · 新行需要词型/指定排产号：--word-type 名词 --sched-no B301

narration.md 支持两种格式：
  A) markdown 表格（首行表头 + 分隔行自动跳过）
       | 页码 | 英文 | 中文 |
       |------|------|------|
       | 封面 | DAY  | 白天 DAY |
  B) JSON
       [{"page": "封面", "en": "DAY", "cn": "白天 DAY"}, ...]

────────────────────────────────────────────────────────────────
台账定位（三段式，缺一不可 —— 2026-10-23 实测）
  中控台页 page_id  ──▶ 正文 child_database(台账库) id  ──▶ GET /v1/databases/{db_id}
  ──▶ data_sources[].id  ──▶ POST /v1/data_sources/{ds_id}/query
  ⚠️ child_database id ≠ data_source id：直接拿 child_database id 去 query 会 404。

实测常量（默认值，可用环境变量覆盖）
  NOTION_CONTROL_PAGE_ID  中控台页  3e0a3f92-69aa-81b4-8385-c2a5309d0824
  NOTION_LEDGER_DB_ID     台账库   3e0a3f92-69aa-81a6-a5b5-e2bb7962e207
  NOTION_DATA_SOURCE_ID   数据源   3e0a3f92-69aa-8181-b457-000bcba7fc09
若默认值失效（404），脚本自动走「搜索『中控』→ child_database → data_sources」重新发现。

环境
  NOTION_API_KEY  在 ~/.hermes/.env（脚本自动读取，也可直接 export）
  台账库必须已 Connect 到该 integration，否则 404 object_not_found。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

NOTION_BASE = "https://api.notion.com"
NOTION_VERSION = "2025-09-03"

# 实测常量（2026-10-23，绘本排产中控台）
DEFAULT_CONTROL_PAGE_ID = "3e0a3f92-69aa-81b4-8385-c2a5309d0824"
DEFAULT_LEDGER_DB_ID = "3e0a3f92-69aa-81a6-a5b5-e2bb7962e207"
DEFAULT_DATA_SOURCE_ID = "3e0a3f92-69aa-8181-b457-000bcba7fc09"

MAX_RICH_TEXT = 1900   # Notion rich_text.content 上限 2000，留余量
MAX_BLOCKS_PER_REQ = 90


# ────────────────────────────── HTTP ──────────────────────────────
def load_key() -> str:
    key = os.environ.get("NOTION_API_KEY")
    if key:
        return key.strip()
    for env_path in (Path.home() / ".hermes" / ".env", Path(".env")):
        if env_path.exists():
            for line in env_path.read_text(encoding="utf-8").splitlines():
                if line.strip().startswith("NOTION_API_KEY"):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    sys.exit("✗ 找不到 NOTION_API_KEY（请在 ~/.hermes/.env 或环境变量中配置）")


KEY = None


def api(path: str, method: str = "GET", body=None):
    global KEY
    if KEY is None:
        KEY = load_key()
    req = urllib.request.Request(
        NOTION_BASE + path,
        method=method,
        data=json.dumps(body).encode("utf-8") if body is not None else None,
        headers={
            "Authorization": "Bearer " + KEY,
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:600]
        raise SystemExit(f"✗ Notion API {method} {path} → {e.code}\n{detail}") from None


# ─────────────────────────── 台账定位 ────────────────────────────
def _title_of_page(page: dict) -> str:
    for v in (page.get("properties") or {}).values():
        if v.get("type") == "title":
            return "".join(x.get("plain_text", "") for x in v.get("title", []))
    return ""


def discover_ledger() -> tuple[str, str]:
    """搜索『中控』→ 中控台页 → child_database → data_sources[].id"""
    res = api("/v1/search", "POST", {"query": "中控", "page_size": 20})
    page = next(
        (o for o in res.get("results", []) if o.get("object") == "page" and "中控" in _title_of_page(o)),
        None,
    )
    if not page:
        raise SystemExit("✗ 找不到「中控台」页面，确认 integration 已 Connect 到该页面")
    pid = page["id"]
    kids = api(f"/v1/blocks/{pid}/children?page_size=100")
    db = next((b for b in kids.get("results", []) if b.get("type") == "child_database"), None)
    if not db:
        raise SystemExit("✗ 中控台页正文没有 child_database（台账库）")
    db_id = db["id"]
    meta = api(f"/v1/databases/{db_id}")
    sources = meta.get("data_sources") or []
    if not sources:
        raise SystemExit("✗ 台账库没有 data_sources，无法 query")
    print(f"  · 发现台账：page={pid} db={db_id} data_source={sources[0]['id']}", file=sys.stderr)
    return db_id, sources[0]["id"]


def resolve_data_source() -> str:
    ds = os.environ.get("NOTION_DATA_SOURCE_ID") or DEFAULT_DATA_SOURCE_ID
    try:
        api(f"/v1/data_sources/{ds}/query", "POST", {"page_size": 1})
        return ds
    except SystemExit:
        print("  · 默认 data_source 失效，重新发现台账…", file=sys.stderr)
        _, ds2 = discover_ledger()
        return ds2


def query_rows(ds_id: str, word: str) -> list:
    """按「核心词」精确匹配查行。"""
    res = api(
        f"/v1/data_sources/{ds_id}/query",
        "POST",
        {
            "page_size": 10,
            "filter": {"property": "核心词", "rich_text": {"equals": word}},
        },
    )
    return res.get("results", [])


def next_sched_no(ds_id: str) -> str:
    """扫全库取最大 B### +1（必须分页到 has_more=false，单页会漏）。"""
    nums, cur = [], None
    while True:
        body = {"page_size": 100}
        if cur:
            body["start_cursor"] = cur
        res = api(f"/v1/data_sources/{ds_id}/query", "POST", body)
        for row in res.get("results", []):
            t = (row.get("properties") or {}).get("排产号", {}).get("title") or []
            s = "".join(x.get("plain_text", "") for x in t).strip()
            if s[:1] == "B" and s[1:].isdigit():
                nums.append(int(s[1:]))
        if not res.get("has_more"):
            break
        cur = res.get("next_cursor")
    return "B%03d" % ((max(nums) + 1) if nums else 1)


def create_row(ds_id: str, word: str, word_type: str = "", sched_no: str = "") -> dict:
    """在台账新建一行（只在按核心词查不到时调用）。状态列不设值 —— 归排产流水线管。"""
    sched_no = sched_no or next_sched_no(ds_id)
    props = {
        "排产号": {"title": [{"type": "text", "text": {"content": sched_no}}]},
        "核心词": {"rich_text": rt(word)},
    }
    if word_type:
        props["词型"] = {"rich_text": rt(word_type)}
    pg = api("/v1/pages", "POST", {"parent": {"data_source_id": ds_id}, "properties": props})
    pg["_排产号"] = sched_no
    pg["_created"] = True
    return pg


def resolve_row(ds_id: str, word: str, allow_create: bool, word_type: str, sched_no: str) -> dict:
    """有则复用、无则新建。幂等：同一核心词永远不会产生第二行。"""
    rows = query_rows(ds_id, word)
    if len(rows) > 1:
        nums = [rich_text_of(r, "排产号") or r["id"] for r in rows]
        raise SystemExit(f"✗ 「核心词 = {word}」命中多行：{nums}。请用 --page-id 明确指定。")
    if rows:
        rows[0]["_排产号"] = rich_text_of(rows[0], "排产号")
        return rows[0]
    if not allow_create:
        raise SystemExit(
            f"✗ 台账里没有「核心词 = {word}」的行，且已显式禁用自动建行(--no-create)。"
        )
    print(f"  · 台账无「核心词 = {word}」的行 → 自动建行", file=sys.stderr)
    return create_row(ds_id, word, word_type, sched_no)


def has_archive(page_id: str) -> bool:
    """该行正文是否已经有「创作产出」段落（防重复归档）。"""
    try:
        md = api(f"/v1/pages/{page_id}/markdown").get("markdown", "")
    except SystemExit:
        return False
    return "📚 创作产出" in md


def rich_text_of(page: dict, prop: str) -> str:
    p = (page.get("properties") or {}).get(prop) or {}
    return "".join(x.get("plain_text", "") for x in (p.get("rich_text") or p.get("title") or []))


# ─────────────────────────── 旁白解析 ───────────────────────────
def parse_narration(path: str) -> list[tuple[str, str, str]]:
    text = Path(path).read_text(encoding="utf-8").strip()
    if text.startswith("[") or text.startswith("{"):
        data = json.loads(text)
        return [(str(r["page"]), str(r["en"]), str(r["cn"])) for r in data]
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 3:
            continue
        if re.fullmatch(r"[-:\s]+", cells[0]):        # 分隔行 |---|---|
            continue
        if cells[0] in ("页码", "Page", "page"):      # 表头
            continue
        rows.append((cells[0], cells[1], cells[2]))
    if not rows:
        raise SystemExit(f"✗ 从 {path} 没解析出旁白行（需要 | 页码 | 英文 | 中文 | 表格 或 JSON）")
    return rows


# ─────────────────────────── block 构造 ──────────────────────────
def rt(text: str) -> list:
    return [{"type": "text", "text": {"content": text[:2000]}}]


def code_blocks(text: str):
    """按行边界切 ≤1900 字符的 code 块（rich_text 上限 2000）。"""
    chunks, cur = [], ""
    for line in text.splitlines(keepends=True):
        if len(cur) + len(line) > MAX_RICH_TEXT:
            if cur:
                chunks.append(cur)
            while len(line) > MAX_RICH_TEXT:          # 极端超长行硬切
                chunks.append(line[:MAX_RICH_TEXT])
                line = line[MAX_RICH_TEXT:]
            cur = line
        else:
            cur += line
    if cur:
        chunks.append(cur)
    return [
        {
            "type": "code",
            "code": {"rich_text": rt(c), "language": "plain text"},
        }
        for c in chunks
        if c.strip()
    ]


def table_block(rows: list[tuple[str, str, str]]) -> dict:
    header = ("页码", "英文", "中文")
    cells = [header] + rows
    table_rows = [
        {
            "type": "table_row",
            "table_row": {"cells": [rt(c) for c in row]},   # 单元格 = rich_text 数组，不外包 type
        }
        for row in cells
    ]
    return {
        "type": "table",
        "table": {
            "table_width": 3,
            "has_column_header": True,
            "children": table_rows,
        },
    }


def build_blocks(date: str, title: str, brief: str, narration: list, l4: str) -> list:
    blocks = [{"type": "heading_2", "heading_2": {"rich_text": rt(f"📚 创作产出（{date} 归档）")}}]
    if title:
        blocks.append({"type": "paragraph", "paragraph": {"rich_text": rt("选定标题：" + title)}})
    if brief:
        blocks.append({"type": "paragraph", "paragraph": {"rich_text": rt("选定简介：" + brief)}})
    blocks.append({"type": "heading_3", "heading_3": {"rich_text": rt("双语旁白")}})
    blocks.append(table_block(narration))
    blocks.append({"type": "heading_3", "heading_3": {"rich_text": rt("L4 生图提示词")}})
    blocks.extend(code_blocks(l4))
    return blocks


# ─────────────────────────── 写入 / 回读 ──────────────────────────
def append_blocks(page_id: str, blocks: list) -> int:
    """分批 append（≤90 块/请求），返回写入块数。"""
    written = 0
    for i in range(0, len(blocks), MAX_BLOCKS_PER_REQ):
        batch = blocks[i : i + MAX_BLOCKS_PER_REQ]
        api(f"/v1/blocks/{page_id}/children", "PATCH", {"children": batch})
        written += len(batch)
    return written


def backfill_props(page_id: str, title: str, brief: str) -> None:
    props = {}
    if title:
        props["选定标题"] = {"rich_text": rt(title)}
    if brief:
        props["选定简介"] = {"rich_text": rt(brief)}
    if props:
        api(f"/v1/pages/{page_id}", "PATCH", {"properties": props})


def verify(page_id: str, word: str, narration: list, l4: str) -> list[str]:
    """回读 markdown 校验，返回缺失项列表（空 = 通过）。"""
    md = api(f"/v1/pages/{page_id}/markdown").get("markdown", "")
    missing = []
    if "双语旁白" not in md:
        missing.append("heading『双语旁白』")
    if "L4 生图提示词" not in md:
        missing.append("heading『L4 生图提示词』")
    if narration and narration[0][1] not in md:
        missing.append(f"旁白首行『{narration[0][1]}』")
    anchors = re.findall(r"场景锚点[:：]\s*([^\n，,]+)", l4)
    if anchors and anchors[-1].strip() not in md:
        missing.append(f"L4 场景锚点『{anchors[-1].strip()}』")
    # 核心词校验看台账行属性（正文里不一定会出现该词，尤其新建行）
    try:
        row_word = rich_text_of(api(f"/v1/pages/{page_id}"), "核心词")
    except SystemExit:
        row_word = ""
    if row_word and word and word.strip().lower() not in row_word.lower():
        missing.append(f"台账『核心词』应为『{word}』，实际『{row_word}』")
    return missing


# ─────────────────────────────── main ────────────────────────────
def main() -> int:
    ap = argparse.ArgumentParser(description="picturebook-creator L5：Notion 排产台账归档")
    ap.add_argument("--word", required=True, help="核心词，用于在台账『核心词』列精确匹配")
    ap.add_argument("--title", default="", help="选定标题（写入正文一段）")
    ap.add_argument("--brief", default="", help="选定简介（写入正文一段）")
    ap.add_argument("--narration", help="旁白 md/json 文件")
    ap.add_argument("--l4", help="L4 生图提示词纯文本文件")
    ap.add_argument("--date", default=None, help="归档日期 YYYY-MM-DD，默认今天")
    ap.add_argument("--page-id", default=None, help="直接指定台账 row 的 page_id（跳过查行）")
    ap.add_argument("--attr-title", action="store_true", help="属性回填『选定标题』")
    ap.add_argument("--attr-brief", action="store_true", help="属性回填『选定简介』")
    ap.add_argument("--word-type", default="", help="新建行时写入『词型』（名词/动作动词/形容词…）")
    ap.add_argument("--sched-no", default="", help="新建行时指定排产号，默认自动取 B###+1")
    ap.add_argument("--no-create", action="store_true", help="查不到该核心词时禁止建行（默认会建）")
    ap.add_argument("--force", action="store_true", help="该行已有创作产出时仍追加一段（默认拦截）")
    ap.add_argument("--locate", action="store_true", help="只定位台账行并打印，不写")
    ap.add_argument("--dry-run", action="store_true", help="打印 block 清单，不发写请求")
    args = ap.parse_args()

    date = args.date or __import__("datetime").date.today().isoformat()

    # 1) 定位行（有则复用 / 无则新建，除非 --no-create / --page-id）
    if args.page_id:
        page_id, sched_no = args.page_id, "(--page-id 指定)"
        print(f"✓ 台账行：{sched_no}  page_id={page_id}")
    elif args.locate:
        ds_id = resolve_data_source()
        rows = query_rows(ds_id, args.word)
        if len(rows) > 1:
            nums = [rich_text_of(r, "排产号") or r["id"] for r in rows]
            raise SystemExit(f"✗ 「核心词 = {args.word}」命中多行：{nums}。请用 --page-id 明确指定。")
        if rows:
            print(f"✓ 台账已有该行：{rich_text_of(rows[0], '排产号')}  page_id={rows[0]['id']}（不会重复建行）")
            if has_archive(rows[0]["id"]):
                print("  ⚠ 该行正文已有『创作产出』段落 —— 再归档需加 --force")
        elif args.no_create:
            print(f"✗ 台账无「核心词 = {args.word}」的行，且已禁用自动建行(--no-create)")
        else:
            print(f"· 台账无「核心词 = {args.word}」的行 → 归档时会自动建行（排产号预计 {next_sched_no(ds_id)}）")
        return 0
    else:
        ds_id = resolve_data_source()
        row = resolve_row(ds_id, args.word, not args.no_create, args.word_type, args.sched_no)
        page_id, sched_no = row["id"], row.get("_排产号", "")
        tag = "【新建行】" if row.get("_created") else ""
        print(f"✓ 台账行{tag}：{sched_no}  page_id={page_id}")

    # 防重复归档：该行已有创作产出 → 默认拦截
    if has_archive(page_id) and not args.force:
        raise SystemExit(
            f"✗ 该行正文已有『📚 创作产出』段落，为防重复归档已拦截。\n"
            f"  确认要再加一段（例如 L4 重出后补档）→ 加 --force。"
        )

    if not (args.narration and args.l4):
        raise SystemExit("✗ 归档需要 --narration 和 --l4（或用 --locate 只查看行）")

    narration = parse_narration(args.narration)
    l4 = Path(args.l4).read_text(encoding="utf-8")
    blocks = build_blocks(date, args.title, args.brief, narration, l4)

    if args.dry_run:
        print(f"[dry-run] 将写入 {len(blocks)} 个顶层 block：")
        for b in blocks:
            t = b["type"]
            if t == "table":
                print(f"  - table  3×{len(b['table']['children'])} 行（首行表头）")
            elif t == "code":
                print(f"  - code   {len(b['code']['rich_text'][0]['text']['content'])} 字")
            else:
                print(f"  - {t:8s} {b[t]['rich_text'][0]['text']['content'][:40]}")
        if args.attr_title or args.attr_brief:
            props = {}
            if args.attr_title:
                props["选定标题"] = {"rich_text": rt(args.title)}
            if args.attr_brief:
                props["选定简介"] = {"rich_text": rt(args.brief)}
            print("[dry-run] 另将回填属性：" + "、".join(props) if props else "")
        return 0

    # 2) 写正文
    n = append_blocks(page_id, blocks)
    print(f"✓ 已写入 {n} 个 block")

    # 3) 可选属性回填
    if args.attr_title or args.attr_brief:
        backfill_props(page_id, args.title if args.attr_title else "", args.brief if args.attr_brief else "")
        print("✓ 属性回填完成")

    # 4) 回读校验
    missing = verify(page_id, args.word, narration, l4)
    if missing:
        print("✗ 回读校验未通过，缺失：" + "、".join(missing))
        return 1
    print(f"✓ 回读校验通过 —— 已归档 Notion（{sched_no}）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
