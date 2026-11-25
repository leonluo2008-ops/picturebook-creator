#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从本地确认稿提取选定标题/简介，生成补档 manifest（scratch/backfill_manifest.json）。"""
import io, re, glob, json, os

out = {}
for p in sorted(glob.glob('projects/*/title_intro*.md')):
    parts = re.split(r'[\\/]', p)
    b = parts[1]
    t = io.open(p, encoding='utf-8-sig').read()  # BOM 容错（B684 实证：BOM 行首吞 ^ 锚）
    tm = re.search(r'(?m)^选定标题[:：]\s*(.+)$', t)
    if not tm:
        continue
    pieces = [x.strip() for x in tm.group(1).split('/')]
    if len(pieces) >= 2:
        cn, en = pieces[0], pieces[1]
    else:
        cn = en = pieces[0]
    seg = re.search(r'##\s*二、简介(.*?)(?=\n##|\Z)', t, re.S)
    quotes = re.findall(r'(?m)^>\s*(.+)$', seg.group(1)) if seg else []
    pref = re.search(r'首选[：:]\s*候选\s*(\d)', t)
    idx = int(pref.group(1)) - 1 if pref else 0
    brief = quotes[idx].strip() if quotes else ''
    # 清掉简介行内粘连的批注尾巴（如「（首选）」「（首选候选1）」）
    brief = re.sub(r'（[^）]*首选[^）]*）\s*$', '', brief).strip()
    assert not re.search(r'[\u4e00-\u9fff]（[^）]*）$', brief), f'{b} 简介仍带批注: {brief}'
    out[b] = {'file': p.replace('\\', '/'), 'title_en': en, 'title_cn': cn,
              'brief': brief, 'n_candidates': len(quotes),
              'pref': idx + 1 if pref else None}
io.open('scratch/backfill_manifest.json', 'w', encoding='utf-8').write(
    json.dumps(out, ensure_ascii=False, indent=1))
print('本数:', len(out))
print('缺简介选定:', [b for b, v in out.items() if not v['brief']])
for b in ['B685', 'B627', 'B711', 'B713', 'B714']:
    print(b, out.get(b, '<无本地稿>'))
