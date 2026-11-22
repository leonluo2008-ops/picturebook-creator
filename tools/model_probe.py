#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""model_probe.py —— 委派路由核对（executor.md §3 的一条命令）。

读 ~/.dsh/sessions/**/session.v4.jsonl.zstd 会话档里最近 N 个子会话的
subagent/descriptor（agentProvider / agentModel），与期望值比对。
不读子代理的任何自述（报告 MODEL: 行只算声明）。

用法：
  python tools/model_probe.py --newest 3                      # 列最近 3 个子会话
  python tools/model_probe.py --newest 1 --expect "ollama-cloud" "deepseek-v4.1-flash:1017"
      # 最近 1 个子会话必须是该 provider/model：一致 EXIT=0，不符 EXIT=1

注意：
  · descriptor 在会话档头部 256KB 内，只解这部分，快。
  · 本机 Python 需 zstandard 库；缺库打印 SKIP 退出 2 —— SKIP ≠ 通过，须明示「路由未核」。
  · Windows 下路径含转义目录名，直接 walk 全树即可。
"""
from __future__ import annotations

import argparse
import datetime
import os
import sys

SESSIONS_ROOT = os.path.expanduser("~/.dsh/sessions")
HEAD_BYTES = 262144  # descriptor/header 都在文件头部


def newest_session_files(n: int) -> list[str]:
    out = []
    for root, _dirs, files in os.walk(SESSIONS_ROOT):
        for f in files:
            if f.endswith(".zstd"):
                p = os.path.join(root, f)
                out.append((os.path.getmtime(p), p))
    out.sort()
    return [p for _mt, p in out[-n:]]


def read_descriptor(path: str):
    """返回 (agentProvider, agentModel) 或 None（非子会话/解析失败）。

    descriptor 不一定在文件头部（系统提示可能占前几百 KB），按 256KB→2MB→全文 递进读。
    """
    try:
        import zstandard
    except ImportError:
        return "SKIP", None
    try:
        dctx = zstandard.ZstdDecompressor()
        with open(path, "rb") as fh:
            reader = dctx.stream_reader(fh)
            for limit in (262144, 2 * 1024 * 1024, None):
                head = reader.read(limit).decode("utf-8", "replace")
                for line in head.splitlines():
                    if '"subagent/descriptor"' not in line:
                        continue
                    j = json.loads(line)
                    d = j.get("data") or {}
                    return d.get("agentProvider"), d.get("agentModel")
                if limit is None:
                    break
    except Exception:
        return None, None
    return None, None  # 是会话档但没有 descriptor = 主会话，不算子会话


import json  # noqa: E402  (放函数后只为文档可读)

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--newest", type=int, default=3, help="看最近 N 个会话档（默认 3）")
    ap.add_argument("--expect", nargs=2, metavar=("PROVIDER", "MODEL"),
                    help="期望值：最近 --newest 个里必须存在该 provider/model 的子会话（--newest 1 即精确核对）")
    args = ap.parse_args()

    files = newest_session_files(args.newest)
    if not files:
        print(f"✗ {SESSIONS_ROOT} 下没找到会话档")
        return 2

    rows = []
    skip = False
    for p in files:
        prov, model = read_descriptor(p)
        if prov == "SKIP":
            skip = True
            rows.append((p, "SKIP", "缺 zstandard 库，无法解会话档"))
            continue
        if prov is None:
            continue  # 主会话，跳过
        rows.append((p, prov, model))

    now = datetime.datetime.now()
    print("最近子会话（按修改时间，%s 附近）：" % now.strftime("%Y-%m-%d"))
    hit = False
    for p, prov, model in rows:
        t = datetime.datetime.fromtimestamp(os.path.getmtime(p)).strftime("%H:%M:%S")
        print(f"  [{t}] {os.path.basename(os.path.dirname(p))[:16]}…  provider={prov}  model={model}")
        if args.expect and prov == args.expect[0] and model == args.expect[1]:
            hit = True

    if skip:
        print("\nSKIP：缺 zstandard 库（pip install zstandard），路由未核——SKIP ≠ 通过")
        return 2
    if args.expect:
        if hit:
            print(f"\n✓ 路由核对通过：存在子会话 {args.expect[0]} / {args.expect[1]}")
            return 0
        print(f"\n✗ 路由不符：最近 {args.newest} 个会话里没有 {args.expect[0]} / {args.expect[1]}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
