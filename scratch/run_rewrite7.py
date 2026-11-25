#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""7 本重归：从旧档提取（B709/711/713）或本地源稿（B681-684），--rewrite 重归并属性回填。"""
import io, json, re, subprocess, sys, html
sys.path.insert(0, 'scripts')
import notion_archive as na

MANIFEST = json.load(io.open('scratch/backfill_manifest.json', encoding='utf-8'))

# 确认值（B709 属性/正文逐字；B711/B713 属性标题+正文简介）
CONFIRMED = {
 'B709': {'page_id': '3b4a3f92-69aa-837e-a83c-01c6dbed30a6', 'title_en': 'Pencil Sharpener', 'title_cn': '卷笔刀，Pencil Sharpener', 'brief': '线条越来越粗，铅笔画钝了。要让笔尖变尖，就得用卷笔刀，pencil sharpener。', 'status': '修改中'},
 'B711': {'page_id': '216a3f92-69aa-83db-836b-015af806a101', 'title_en': 'Clothesline', 'title_cn': '晾衣绳，Clothesline', 'brief': '小刺猬踮起脚爪，把衣服一件件夹上晾衣绳。快来看看，clothesline！', 'status': '修改中'},
 'B713': {'page_id': '36ea3f92-69aa-838b-b81c-0184b4f87af1', 'title_en': 'Camera', 'title_cn': '照相机，Camera', 'brief': '发现一个神奇的盒子，咔嚓一声拍下好朋友。这就是照相机，camera！', 'status': '修改中'},
 'B681': {'page_id': 'e1ba3f92-69aa-8240-a457-81ad214e9570', 'status': '待生图'},
 'B682': {'page_id': '795a3f92-69aa-831c-af15-0164ad57dd79', 'status': '待生图'},
 'B683': {'page_id': '5fba3f92-69aa-8256-a187-8140d53dd943', 'status': '待生图'},
 'B684': {'page_id': '5bda3f92-69aa-82cc-a889-01ea144853c1', 'status': '待生图'},
}


def extract_legacy(pid: str):
    """从旧档 md 提取旁白表（HTML→md 三列）与 L4（code 块，单块端点取全文）。"""
    md = na.api(f"/v1/pages/{pid}/markdown").get("markdown", "")
    tbl = re.search(r"<table.*?</table>", md, re.S)
    rows = []
    if tbl:
        for tr in re.findall(r"<tr>(.*?)</tr>", tbl.group(0), re.S):
            cells = [html.unescape(c).strip() for c in
                     re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
            if len(cells) >= 3 and cells[0] != "页码":
                rows.append(cells[:3])
    narr = "| 页码 | 英文 | 中文 |\n| --- | --- | --- |\n" + \
           "\n".join("| " + " | ".join(r) + " |" for r in rows)
    # code 块：从 md 围栏提取内容（取最长的那个 code 块 = L4 正文）
    blocks = re.findall(r"```[a-z]*\n(.*?)```", md, re.S)
    l4 = max(blocks, key=len) if blocks else ""
    l4 = l4.replace('\\"', '"')
    return narr, l4


for b, c in CONFIRMED.items():
    if b in MANIFEST and b.startswith('B68'):
        src = MANIFEST[b]
        narr_path = f"projects/{b}/narration.md"
        l4_path = f"projects/{b}/l4.txt"
        title_en, title_cn, brief = src['title_en'], src['title_cn'], src['brief']
    elif b in MANIFEST:
        src = MANIFEST[b]
        narr_path = f"projects/{b}/narration.md"
        l4_path = f"projects/{b}/l4.txt"
        title_en, title_cn, brief = src['title_en'], src['title_cn'], src['brief']
    else:
        # L4 已从会话内 fetch 的定稿版重建（scratch/extract_B7xx_l4.txt）——不再从旧档提取
        narr_path = f"scratch/extract_{b}_narration.md"
        l4_path = f"scratch/extract_{b}_l4.txt"
        _chk = io.open(l4_path, encoding='utf-8').read().strip()
        assert len(_chk) > 500, f"{b} L4 重建文件为空/过短，禁止重归"
        title_en, title_cn, brief = c['title_en'], c['title_cn'], c['brief']
    cmd = [sys.executable, 'scripts/notion_archive.py', '--page-id', c['page_id'],
           '--title', title_en, '--title-cn', title_cn, '--brief', brief,
           '--narration', narr_path, '--l4', l4_path,
           '--attr-title', '--attr-brief', '--rewrite', '--status', c['status'],
           '--note', '2026-11-25 链路修复重归：标题/简介/旁白/L4 按现行骨架重写，属性回填并独立回读']
    r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    tail = (r.stdout or '').strip().splitlines()
    print(f"{b}: exit={r.returncode}  {tail[-1] if tail else (r.stderr or '')[:100]}")
