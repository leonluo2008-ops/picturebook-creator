#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量补档 runner：对制作清单缺标题/简介的书逐本调 notion_archive.py --patch（串行、逐本验）。"""
import io, json, subprocess, sys

MANIFEST = json.load(io.open('scratch/backfill_manifest.json', encoding='utf-8'))

# page_id 映射（2026-11-25 台账 SQL 实测）
PAGES = {
 'B572':'cb648ef3-2994-4be6-99c0-64840117c053','B573':'3e9097f1-26b2-4f99-b3fb-8b23149dda62',
 'B574':'f15f57e1-9051-41ba-a02d-eee1ae709b37','B627':'d4516318-1935-428e-9364-f33bba1eeb9f',
 'B668':'a62a3f92-69aa-83d0-8fa9-016a70f0020e','B669':'26ca3f92-69aa-8363-bc24-812228a6f61b',
 'B670':'cfaa3f92-69aa-8369-b050-019161384c1d','B671':'6cba3f92-69aa-836d-91de-017cacfbaf0c',
 'B672':'62aa3f92-69aa-8326-a6a4-81dd0f6b41c0','B673':'5aaa3f92-69aa-8292-b561-010b88a96901',
 'B674':'fe5a3f92-69aa-83a2-a66d-01c262e193fc','B675':'3a7a3f92-69aa-836c-86bf-0194f2fbe6fd',
 'B676':'349a3f92-69aa-8262-bd6c-81d940abe398','B677':'702a3f92-69aa-83a9-b62e-8101f96a7063',
 'B678':'c4ba3f92-69aa-836f-9ef6-81d6a3da69f8','B679':'0c7a3f92-69aa-8218-861e-0169861cee6d',
 'B685':'5b5a3f92-69aa-8304-a703-81297f3600f1','B686':'694a3f92-69aa-8386-bf4b-01e9df0c94fb',
 'B687':'4f5a3f92-69aa-823d-86fd-8141a932ee46','B688':'e98a3f92-69aa-8253-b766-012ca1cd3540',
 'B689':'c07a3f92-69aa-82c2-a59a-816f4fc67d7a','B690':'c58a3f92-69aa-82b9-8333-01377932b6ea',
 'B691':'ccaa3f92-69aa-82eb-b7ad-8115376a6984','B692':'467a3f92-69aa-820e-b83c-8188f83083d7',
 'B693':'695a3f92-69aa-82c6-aaa6-019a17e70040','B694':'fa9a3f92-69aa-8298-86b7-81b2602c83f6',
 'B695':'faba3f92-69aa-823f-b645-014ef2efd366','B696':'50fa3f92-69aa-82b8-b47f-0146bc59c0b5',
 'B698':'066a3f92-69aa-83a3-b5ab-813911977942','B699':'b41a3f92-69aa-832d-9efb-813059c2e0b2',
 'B700':'eefa3f92-69aa-8208-8c0a-01c0dacb1b60','B701':'ddca3f92-69aa-82f3-9fa9-812e08dc5eb2',
 'B702':'94ca3f92-69aa-828f-bed7-01040e1c0c3b','B703':'b15a3f92-69aa-830f-8e61-813ad06e17cc',
 'B704':'d57a3f92-69aa-822e-96d2-81f19b9a7158','B705':'068a3f92-69aa-8367-8161-8182c4c36c62',
 'B706':'c91a3f92-69aa-8260-a258-0118a6ed0a0c','B707':'980a3f92-69aa-83a6-b3fd-81d612511d35',
}
# 正文段已齐、只缺属性（值从 Notion 正文逐字提取）
EXTRA = {
 'B708': {'page_id':'76da3f92-69aa-8260-b654-810c8be811f6','title_en':'Shoe Rack','title_cn':'鞋架，Shoe Rack','brief':'哇，所有的鞋子都回到了自己的位置！快看，它们排成了整齐的一排，鞋架，shoe rack！'},
 'B711': {'page_id':'216a3f92-69aa-83db-836b-015af806a101','title_en':'Clothesline','title_cn':'晾衣绳，Clothesline','brief':'小刺猬踮起脚爪，把衣服一件件夹上晾衣绳。快来看看，clothesline！'},
 'B713': {'page_id':'36ea3f92-69aa-838b-b81c-0184b4f87af1','title_en':'Camera','title_cn':'照相机，Camera','brief':'发现一个神奇的盒子，咔嚓一声拍下好朋友。这就是照相机，camera！'},
}

targets = sorted(set(PAGES) | set(EXTRA))
ok, fail = [], []
for b in targets:
    src = EXTRA.get(b) or MANIFEST.get(b)
    pid = src['page_id'] if 'page_id' in src else PAGES[b]
    cmd = [sys.executable, 'scripts/notion_archive.py', '--page-id', pid, '--patch',
           '--title', src['title_en'], '--title-cn', src['title_cn'], '--brief', src['brief'],
           '--attr-title', '--attr-brief']
    r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    tail = (r.stdout or '').strip().splitlines()
    summary = tail[-1] if tail else (r.stderr or '').strip()[:80]
    print(f"{b}: exit={r.returncode}  {summary}")
    (ok if r.returncode == 0 else fail).append((b, r.returncode, summary))

print(f"\n== 完成 {len(ok)} 过 / {len(fail)} 败 ==")
for b, rc, s in fail:
    print(f"  FAIL {b} exit={rc}: {s}")
io.open('scratch/backfill_result.json', 'w', encoding='utf-8').write(
    json.dumps({'ok': [b for b, _, _ in ok], 'fail': [b for b, _, _ in fail]}, ensure_ascii=False))
