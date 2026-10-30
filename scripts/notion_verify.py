#!/usr/bin/env python3
"""L5 归档后的独立回读校验 —— 不 import notion_archive(归档脚本自报的「回读校验通过」不采信)。

用法:
  python3 scripts/notion_verify.py --word stack
  python3 scripts/notion_verify.py --word glue --pages 9
  python3 scripts/notion_verify.py --page-id 62e84647-d916-47c6-9d08-970f14892b82 --pages 9
  python3 scripts/notion_verify.py --word glue --set-word-type 名词   # 顺带把「词型」改成与本本义项一致

--word 模式的定位走子进程调 scripts/notion_archive.py --locate(复用其定位链),
校验本身全部用本文件自己的 HTTP 调用。

--pages = 页数(含封面),默认 9(封面 + 8 内页)。
EXIT=0 全部通过; EXIT=1 有项不符(逐项打印实际 vs 期望)。

内置两个坑的处置:
  · Windows IPv6 路由抖动会被映射成 `URLError: [Errno 2] No such file or directory`,
    堆栈落在 ssl.py/do_handshake —— 进程内把 socket.getaddrinfo 强制成 AF_INET 规避。
  · 网络抖动 —— 每条请求包 4 次 sleep 重试。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

# ── Windows: IPv6 抖动伪装成 ENOENT,强制 IPv4 ──────────────────────────
_orig_getaddrinfo = socket.getaddrinfo


def _ipv4_only(host, port, family=0, type=0, proto=0, flags=0):
    return _orig_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)


socket.getaddrinfo = _ipv4_only

BASE = "https://api.notion.com"
NOTION_VERSION = "2025-09-03"
HERE = Path(__file__).resolve().parent
FENCE = "`" * 3


# ── HTTP ────────────────────────────────────────────────────────────────
def load_key() -> str:
    key = os.environ.get("NOTION_API_KEY")
    if key:
        return key.strip()
    candidates = []
    localappdata = os.environ.get("LOCALAPPDATA")
    if localappdata:
        candidates.append(Path(localappdata) / "hermes" / ".env")
    candidates.append(Path.home() / ".hermes" / ".env")
    for env_path in candidates:
        if env_path.exists():
            for line in env_path.read_text(encoding="utf-8").splitlines():
                if line.strip().startswith("NOTION_API_KEY"):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    sys.exit("✗ 找不到 NOTION_API_KEY(%LOCALAPPDATA%\\hermes\\.env 或环境变量)")


KEY = None


def api(path: str, method: str = "GET", body=None, tries: int = 4):
    global KEY
    if KEY is None:
        KEY = load_key()
    req = urllib.request.Request(
        BASE + path,
        method=method,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None,
        headers={
            "Authorization": "Bearer " + KEY,
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json",
        },
    )
    last = None
    for i in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                raw = r.read()
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:400]
            raise SystemExit(f"✗ Notion API {method} {path} → {e.code}\n{detail}") from None
        except Exception as e:  # 网络抖动 / IPv6 抖动
            last = e
            time.sleep(2 + 2 * i)
    raise SystemExit(f"✗ 网络失败({tries} 次重试仍不通): {last}")


# ── 定位 ────────────────────────────────────────────────────────────────
def locate_page_id(word: str) -> str:
    """复用归档脚本的定位链(子进程,只读 --locate),保持校验侧独立。"""
    script = HERE / "notion_archive.py"
    if not script.exists():
        sys.exit(f"✗ 找不到 {script}")
    proc = subprocess.run(
        [sys.executable, str(script), "--word", word, "--locate"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    out = (proc.stdout or "") + (proc.stderr or "")
    m = re.search(r"page_id=([0-9a-fA-F-]{36})", out)
    if not m:
        sys.exit("✗ 定位失败,归档脚本输出:\n" + out.strip())
    return m.group(1)


# ── 属性读取 ─────────────────────────────────────────────────────────────
def plain(prop: dict) -> str:
    for t in ("title", "rich_text"):
        if t in prop:
            return "".join(x.get("plain_text", "") for x in prop.get(t) or [])
    if prop.get("type") == "select" and prop.get("select"):
        return prop["select"].get("name", "")
    if prop.get("type") == "multi_select":
        return ",".join(x.get("name", "") for x in prop.get("multi_select") or [])
    if prop.get("type") == "status" and prop.get("status"):
        return prop["status"].get("name", "")
    return ""


def set_word_type(page_id: str, value: str) -> None:
    """按属性的真实 type 构造 PATCH —— 词型是 rich_text,按 select 写会 400。"""
    before = api(f"/v1/pages/{page_id}")["properties"].get("词型")
    if before is None:
        sys.exit("✗ 该行没有「词型」属性")
    kind = before.get("type")
    if kind == "select":
        payload = {"select": {"name": value}}
    elif kind == "multi_select":
        payload = {"multi_select": [{"name": value}]}
    elif kind in ("rich_text", "title"):
        payload = {kind: [{"type": "text", "text": {"content": value}}]}
    else:
        sys.exit(f"✗ 「词型」属性类型是 {kind},不认识的写法,先 GET 看清楚再改")
    api(f"/v1/pages/{page_id}", "PATCH", {"properties": {"词型": payload}})
    after = plain(api(f"/v1/pages/{page_id}")["properties"]["词型"])
    print(f"词型: {plain(before)!r} → {after!r}  ({kind} 口径)")
    if after != value:
        raise SystemExit("✗ 词型回读不符")


# ── 校验 ────────────────────────────────────────────────────────────────
def main() -> int:
    ap = argparse.ArgumentParser(description="L5 归档后独立回读校验")
    ap.add_argument("--word", help="台账核心词(自动定位行)")
    ap.add_argument("--page-id", help="直接指定台账行 page_id(优先于 --word)")
    ap.add_argument("--pages", type=int, default=9, help="页数(含封面),默认 9")
    ap.add_argument("--set-word-type", dest="word_type", help="把「词型」改成该值后再校验")
    args = ap.parse_args()

    if not args.page_id and not args.word:
        ap.error("需要 --word 或 --page-id")
    page_id = args.page_id or locate_page_id(args.word)
    pages = args.pages

    if args.word_type:
        set_word_type(page_id, args.word_type)

    props = api(f"/v1/pages/{page_id}").get("properties", {})
    state = plain(props.get("状态", {}))
    sched = plain(props.get("排产号", {}))
    word = plain(props.get("核心词", {}))
    wtype = plain(props.get("词型", {}))
    print(f"行 {sched or '-'}  page_id={page_id}")
    print(f"核心词={word!r}  词型={wtype!r}  状态={state!r}")

    md = api(f"/v1/pages/{page_id}/markdown").get("markdown", "") or ""
    print(f"markdown 长度: {len(md)}")

    def cnt(s: str) -> int:
        return md.count(s)

    checks = [
        ("状态=待生图", state == "待生图", f"实际 {state!r}"),
        ("创作产出 heading", cnt("创作产出") == 1, f"实际 {cnt('创作产出')}"),
        ("双语旁白 heading", cnt("### 双语旁白") == 1, f"实际 {cnt('### 双语旁白')}"),
        ("L4 heading", cnt("### L4 生图提示词") == 1, f"实际 {cnt('### L4 生图提示词')}"),
        ("旁白表 <tr> = 页数+1", cnt("<tr") == pages + 1, f"实际 {cnt('<tr')} / 期望 {pages + 1}"),
        ("比例 3:4 = 1", cnt("比例: 3:4") == 1, f"实际 {cnt('比例: 3:4')}"),
        ("比例 16:9 = 内页数", cnt("比例: 16:9") == pages - 1, f"实际 {cnt('比例: 16:9')} / 期望 {pages - 1}"),
        ("场景锚点 = 页数", cnt("场景锚点:") == pages, f"实际 {cnt('场景锚点:')} / 期望 {pages}"),
        ("构图要求 = 页数+1(含全局)", cnt("构图要求") == pages + 1, f"实际 {cnt('构图要求')} / 期望 {pages + 1}"),
        ("围栏 = 2(整篇一个代码块)", cnt(FENCE) == 2, f"实际 {cnt(FENCE)}"),
    ]

    bad = 0
    for name, ok, detail in checks:
        print(f"  {'✓' if ok else '✗'} {name}" + ("" if ok else f"  —— {detail}"))
        if not ok:
            bad += 1

    if bad:
        print(f"\n✗ {bad} 项不符 —— 先归一化渲染工件(<br>、转义引号、<br/>)再下结论,别急着重写正文")
        return 1
    print("\n✓ 全部通过(独立回读)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

