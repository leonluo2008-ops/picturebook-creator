#!/usr/bin/env python3
"""选定值一致性检查器（2026-11-26 判例 B684 旧错配补）

标题 4 处：①台账属性「选定标题」 ②正文标题段（英文标题:/中文标题:）
          ③旁白表封面行中文列 ④L4 封面旁白行「旁白: 封面（中文 / 英文）」
简介 2 处：⑤台账属性「选定简介」 ⑥正文「选定简介：」段
中英文分别核对；<br />、换行等展示格式归一化后比对。
漏写、空白、错版逐项点明字段与位置；EXIT=0 全一致 / 1 有不一致 / 2 参数或取数失败。

用法:
  python scripts/notion_consistency_check.py --page-id <uuid>            # 线上互检+报告实际值
  python scripts/notion_consistency_check.py --page-id <uuid> \
      --expect-title-cn '布丁，Pudding' --expect-title 'Pudding' --expect-brief '……'  # 另对照本轮选定值
  也可作为模块: from notion_consistency_check import check_consistency
"""
import sys, re, io, json, os, argparse, urllib.request

# ───────────────────────── 归一化 ─────────────────────────
def _norm(s):
    if s is None:
        return ''
    s = s.replace('<br />', '\n').replace('<br/>', '\n').replace('<br>', '\n')
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def _split_title(attr_val):
    """属性「选定标题」= 英文标题 + 中文标题（<br /> 或换行分隔）。"""
    parts = [p for p in re.split(r'<br\s*/?>|\n', attr_val or '') if p.strip()]
    if len(parts) >= 2:
        return _norm(parts[0]), _norm(parts[1])
    return _norm(attr_val), ''

# ───────────────────────── 纯函数核心 ─────────────────────────
def check_consistency(attr_title_raw, attr_brief, body_text, table_rows, l4_text,
                      expect=None):
    """table_rows: [[c1,c2,c3],...] 封面行在首行；expect: {'title','title_cn','brief'} 本轮选定值（可选）。
    返回 (items, fails)。items=[(字段, 位置, 值)]；fails=[(字段, 位置, 期望, 实际)]。"""
    items, fails = [], []
    en_attr, cn_attr = _split_title(attr_title_raw)
    en_body = _norm((re.search(r'(?m)^英文标题[:：]\s*(.+)$', body_text) or [None, ''])[1])
    cn_body = _norm((re.search(r'(?m)^中文标题[:：]\s*(.+)$', body_text) or [None, ''])[1])
    brief_body = _norm((re.search(r'(?m)^选定简介[:：]\s*(.+)$', body_text) or [None, ''])[1])
    brief_attr = _norm(attr_brief)

    # 封面行：旁白表第一数据行（跳过表头），中文列=第 3 列
    cn_cover = ''
    for row in table_rows:
        cells = [c.strip() for c in row]
        if len(cells) >= 3 and cells[0] != '页码':
            cn_cover = _norm(cells[2])
            break
    # L4 封面旁白行
    m = re.search(r'(?m)^旁白:\s*封面（(.+?)\s*/\s*(.+?)）', l4_text or '')
    cn_l4 = _norm(m.group(1)) if m else ''
    en_l4 = _norm(m.group(2)) if m else ''

    title_spots = [('台账属性·选定标题', cn_attr, en_attr),
                   ('正文标题段', cn_body, en_body),
                   ('旁白表封面行', cn_cover, ''),
                   ('L4封面旁白行', cn_l4, en_l4)]

    for field, cn_v, en_v in title_spots:
        items.append(('标题·中文', field, cn_v))
        if not cn_v:
            fails.append(('标题·中文', field, '(本轮选定值或基准)', '(空/缺失)'))
    for field, cn_v, en_v in title_spots[:2] + [(title_spots[3][0], title_spots[3][2], '')]:
        pass  # 英文列只在属性/正文段/L4 三处承载，封面行英文列是英文标题本身
    en_spots = [('台账属性·选定标题', en_attr), ('正文标题段', en_body), ('L4封面旁白行', en_l4)]
    for field, v in en_spots:
        items.append(('标题·英文', field, v))
        if not v:
            fails.append(('标题·英文', field, '(基准)', '(空/缺失)'))

    base_cn = next((v for f, v in [(f, c) for f, c, e in title_spots] if v), None)
    base_en = next((v for f, v in en_spots if v), None)
    if base_cn:
        for field, cn_v, _ in title_spots:
            if cn_v and cn_v != base_cn:
                fails.append(('标题·中文', field, base_cn, cn_v))
    if base_en:
        for field, v in en_spots:
            if v and v != base_en:
                fails.append(('标题·英文', field, base_en, v))

    items.append(('简介', '台账属性·选定简介', brief_attr))
    items.append(('简介', '正文简介段', brief_body))
    if not brief_attr:
        fails.append(('简介', '台账属性·选定简介', '(基准)', '(空)'))
    if not brief_body:
        fails.append(('简介', '正文简介段', '(基准)', '(空/缺失)'))
    if brief_attr and brief_body and brief_attr != brief_body:
        fails.append(('简介', '正文简介段', brief_attr, brief_body))

    # 可选：与本轮选定值逐项对照
    if expect:
        exp_t = _norm(expect.get('title', ''))
        exp_c = _norm(expect.get('title_cn', ''))
        exp_b = _norm(expect.get('brief', ''))
        for field, cn_v, _ in title_spots:
            if exp_c and cn_v and cn_v != exp_c:
                fails.append(('标题·中文', field, exp_c, cn_v))
        for field, v in en_spots:
            if exp_t and v and v != exp_t:
                fails.append(('标题·英文', field, exp_t, v))
        if exp_b:
            for field, v in (('台账属性·选定简介', brief_attr), ('正文简介段', brief_body)):
                if v and v != exp_b:
                    fails.append(('简介', field, exp_b, v))
    return items, fails

# ───────────────────────── 线上取数（REST 直读） ─────────────────────────
def _load_env():
    env = {}
    path = os.path.expandvars(r'%LOCALAPPDATA%\hermes\.env')
    for line in io.open(path, encoding='utf-8-sig'):
        line = line.strip()
        if '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1)
            env[k] = v
    return env

def fetch_live(page_id, env=None):
    env = env or _load_env()
    H = {'Authorization': 'Bearer ' + env['NOTION_API_KEY'], 'Notion-Version': '2022-06-28'}
    def get(u):
        return json.load(urllib.request.urlopen(urllib.request.Request(u, headers=H)))
    d = get('https://api.notion.com/v1/pages/%s' % page_id)
    attr_title = ''.join(r['plain_text'] for r in d['properties']['选定标题']['rich_text'])
    attr_brief = ''.join(r['plain_text'] for r in d['properties']['选定简介']['rich_text'])
    body, rows, l4 = [], [], []
    def walk(pid):
        b = get('https://api.notion.com/v1/blocks/%s/children' % pid)
        for blk in b['results']:
            t = blk['type']
            if t == 'table':
                rr = get('https://api.notion.com/v1/blocks/%s/children' % blk['id'])
                for r in rr['results']:
                    rows.append([''.join(x['plain_text'] for x in c) for c in r['table_row']['cells']])
            elif 'rich_text' in blk.get(t, {}):
                txt = ''.join(r['plain_text'] for r in blk[t]['rich_text'])
                body.append(txt)
                if t == 'code':
                    l4.append(txt)
            elif t == 'paragraph' and blk.get('has_children'):
                walk(blk['id'])
    walk(page_id)
    return attr_title, attr_brief, '\n'.join(body), rows, '\n'.join(l4)

# ───────────────────────── CLI ─────────────────────────
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--page-id', required=True)
    ap.add_argument('--expect-title', help='本轮选定英文标题（可选，逐项对照）')
    ap.add_argument('--expect-title-cn', help='本轮选定中文标题')
    ap.add_argument('--expect-brief', help='本轮选定简介')
    a = ap.parse_args()
    try:
        attr_title, attr_brief, body, rows, l4 = fetch_live(a.page_id)
    except Exception as e:
        print('✗ 线上取数失败: %s' % e)
        sys.exit(2)
    expect = None
    if a.expect_title or a.expect_title_cn or a.expect_brief:
        expect = {'title': a.expect_title or '', 'title_cn': a.expect_title_cn or '', 'brief': a.expect_brief or ''}
    items, fails = check_consistency(attr_title, attr_brief, body, rows, l4, expect)
    print('== 各位置实际值 ==')
    for field, pos, v in items:
        print('  [%s] %s = %r' % (field, pos, v))
    if fails:
        print('\n== 不一致（字段 / 位置 / 期望 / 实际）==')
        for f, p, w, g in fails:
            print('  ✗ [%s] %s：期望 %r，实际 %r' % (f, p, w, g))
        sys.exit(1)
    print('\n✓ 标题 4 处 + 简介 2 处全部一致（含本轮选定值对照）' if expect else '\n✓ 标题 4 处 + 简介 2 处互相一致')
    sys.exit(0)

if __name__ == '__main__':
    main()
