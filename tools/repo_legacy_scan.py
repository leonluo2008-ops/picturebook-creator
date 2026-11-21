#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全仓旧口径残留扫描（v13 起）

背景：v13 重构时只扫 SKILL.md 就宣称「术语残留 = 0」，结果 SOUL.md / 仓 AGENTS.md / README.md
仍写着 v11 口径（六视图、每页必须标注、~/huiben-v2 等）。本脚本把扫描范围扩到**整仓**，
并把「合法历史提及」与「真残留」分开判定。

合法历史提及（allowlist）：
- `CHANGELOG.md` / `RELEASE_NOTES_v*.md`：版本历史与新旧对比，必须保留旧词
- `tools/dangling-whitelist.txt`：本身就是历史例外清单
- `SKILL.md` / `README.md` 中作为「旧档漂移示例」出现的旧术语（由 --allow-context 控制）

用法:
  python3 tools/repo_legacy_scan.py [--root <仓根>]
退出码: 0=无真残留  1=发现疑似真残留  2=参数/路径错误
"""
import argparse
import io
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
except Exception:
    pass

LEGACY = [
    "六视图", "2行3列", "六个视角", "语境重复页", "定稿参考", "audit_ledger",
    "每页必须标注", "huiben-v2", "硬上限 15 词", "超过10个英文词",
    "短句串联",  # 2026-11-21 G4 翻案：词族页英文列改为词表，此口径已废
]
SKIP_DIRS = {".git", "__pycache__", ".venv", "projects", "作品", "node_modules"}
HISTORY_FILES = {"CHANGELOG.md"}
HISTORY_PREFIX = "RELEASE_NOTES_v"
SELF_FILES = {"dangling-whitelist.txt", "repo_legacy_scan.py"}  # 本脚本含搜索词表，需自排除
# 允许「作为旧口径示例/凭据路径」出现的位置（文件: 行内必须同时含这些词才算合法）
CONTEXT_OK = {
    "SKILL.md": ["旧档", "作废", "漂移", "不再", "已改", "hermes", "HERMES"],
    "README.md": ["历史", "存档", "已移出", "hermes"],
    "AGENTS.md": ["hermes", "HERMES"],
}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    args = ap.parse_args()
    root = os.path.abspath(args.root)
    if not os.path.isdir(root):
        print("根目录不存在：%s" % root)
        return 2

    files = []
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if d not in SKIP_DIRS]
        for fn in fns:
            if fn.lower().endswith((".md", ".py", ".json", ".txt", ".yml", ".yaml")):
                files.append(os.path.join(dp, fn))

    real, allowed = [], []
    for f in sorted(files):
        rel = os.path.relpath(f, root).replace("\\", "/")
        base = os.path.basename(f)
        try:
            lines = io.open(f, encoding="utf-8-sig", errors="replace").read().splitlines()
        except Exception:
            continue
        for i, ln in enumerate(lines, 1):
            for k in LEGACY:
                if k not in ln:
                    continue
                # 判定是否属于合法历史提及
                ok = (base in HISTORY_FILES) or base.startswith(HISTORY_PREFIX) or (base in SELF_FILES)
                if not ok:
                    ctxs = CONTEXT_OK.get(base) or CONTEXT_OK.get(rel)
                    if ctxs and any(c in ln for c in ctxs):
                        ok = True
                (allowed if ok else real).append((rel, i, k, ln.strip()[:90]))

    print("扫描 %d 个文本文件（排除 %s）" % (len(files), "/".join(sorted(SKIP_DIRS))))
    print("\n-- 合法历史提及 %d 处 --" % len(allowed))
    for rel, i, k, ln in allowed[:20]:
        print("  %s:%d [%s] %s" % (rel, i, k, ln))
    if len(allowed) > 20:
        print("  …（共 %d 处，仅列前 20）" % len(allowed))

    if real:
        print("\n[疑似真残留] %d 处" % len(real))
        for rel, i, k, ln in real:
            print("  ✗ %s:%d [%s] %s" % (rel, i, k, ln))
        return 1

    print("\n全仓旧口径扫描：通过（无真残留，旧词仅出现在历史/示例语境）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
