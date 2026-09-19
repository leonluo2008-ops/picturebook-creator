#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""notion_kanban.py — 绘本排产中控台(Notion)工具链
四命令: import/push/poll/deliver (+migrate/status)
事实源: 排产台账DB(见CONFIG) | 凭证: ~/.hermes/.env NOTION_API_KEY
"""
import sys, csv, json, time, re, datetime, urllib.request, urllib.error, urllib.parse
from pathlib import Path

# ---- CONFIG (铁律1: 唯一硬编码区) ----
DB_ID = '3e0a3f92-69aa-81a6-a5b5-e2bb7962e207'
DS_ID = '3e0a3f92-69aa-8181-b457-000bcba7fc09'
PARENT = '3e0a3f92-69aa-81b4-8385-c2a5309d0824'
ENV_PATH = Path.home() / '.hermes' / '.env'
REPO = Path(__file__).resolve().parent.parent

KEY = [l.split('=', 1)[1].strip() for l in ENV_PATH.read_text().splitlines()
       if l.startswith('NOTION_API_KEY=')][0]

def api(method, path, payload=None, ver='2022-06-28'):
    req = urllib.request.Request('https://api.notion.com/v1/' + path, method=method,
        headers={'Authorization': 'Bearer ' + KEY, 'Notion-Version': ver,
                 'Content-Type': 'application/json'},
        data=json.dumps(payload).encode() if payload is not None else None)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            if e.code == 429 and attempt < 2:
                time.sleep(2 ** (attempt + 1)); continue
            return {'error': e.code, 'body': body[:300]}
        except urllib.error.URLError:
            if attempt < 2: time.sleep(2); continue
            raise
    return {'error': 'retry-exhausted'}

def rt(v): return {'rich_text': [{'text': {'content': v}}]} if v else {'rich_text': []}

def query_all(filter_):
    out, cursor = [], None
    while True:
        p = {'page_size': 100}
        if filter_: p['filter'] = filter_
        if cursor: p['start_cursor'] = cursor
        r = api('POST', f'data_sources/{DS_ID}/query', p, ver='2026-03-11')
        if 'error' in r: sys.exit(f'query失败: {r}')
        out += r['results']; cursor = r.get('next_cursor')
        if not cursor: return out

def plain(prop):
    if not prop: return ''
    t = prop.get('type')
    if t == 'title': return ''.join(x['plain_text'] for x in prop['title'])
    if t == 'rich_text': return ''.join(x['plain_text'] for x in prop['rich_text'])
    if t == 'select': return prop['select']['name'] if prop['select'] else ''
    if t == 'date': return (prop['date'] or {}).get('start', '')
    if t == 'checkbox': return prop['checkbox']
    return ''

# ---- schema ----
RICH_NEW = ['月', '词型', '绑定形态', '链形', '画风',
            '标题备选①', '标题备选②', '标题备选③',
            '简介备选①', '简介备选②', '简介备选③', '简介备选④']
STATUS_OPTS = [{'name': '待产', 'color': 'gray'}, {'name': '待审核', 'color': 'purple'}, {'name': '已排产', 'color': 'blue'},
               {'name': '已领取（生产中）', 'color': 'yellow'}, {'name': '已交付', 'color': 'green'},
               {'name': '弃用', 'color': 'red'}]
VALID_STATES = tuple(o['name'] for o in STATUS_OPTS)   # 状态白名单单源(审查NIT)

def ensure_schema():
    ds = api('GET', f'data_sources/{DS_ID}', ver='2026-03-11')
    props = ds['properties']
    patch = {}
    for name in RICH_NEW:
        if name not in props: patch[name] = {'rich_text': {}}
    if props.get('状态', {}).get('type') == 'select':
        have = {o['name'] for o in props['状态']['select'].get('options', [])}
        missing = [o for o in STATUS_OPTS if o['name'] not in have]
        if missing:                      # 只补缺, 不删用户自定义选项(审查NIT修复)
            patch['状态'] = {'select': {'options': STATUS_OPTS + [
                o for o in props['状态']['select'].get('options', []) if o['name'] not in {x['name'] for x in STATUS_OPTS}]}}
    for col in ('状态', '排产时间', 'Agent已领取'):
        if col not in props:
            print(f'⚠️ 缺关键列「{col}」— 请先跑 migrate 或手工补建')
    if patch:
        r = api('PATCH', f'databases/{DB_ID}', {'properties': patch})
        if 'error' in r: sys.exit(f'schema补建失败: {r}')

def migrate():
    """选定标题/选定简介: select→rich_text (300册下拉爆炸修正)
    Notion铁律: 属性类型转换被带值阻塞 → 临时列拷值→null删旧→改名(删属性=null, 文档原文"Properties set to null will be removed")
    """
    ds = api('GET', f'data_sources/{DS_ID}', ver='2026-03-11')
    p = ds['properties']
    for col in ('选定标题', '选定简介'):
        assert p.get(col, {}).get('type') == 'select', f'{col} 已是 {p.get(col, {}).get("type")}, 无需迁移'
    # 1) 临时列
    r = api('PATCH', f'databases/{DB_ID}',
            {'properties': {'选定标题r': {'rich_text': {}}, '选定简介r': {'rich_text': {}}}})
    assert 'error' not in r, str(r)[:200]
    # 2) 拷值(select值→r列)
    pages = query_all(None)
    val = {}
    for pg in pages:
        pr = pg['properties']
        t = (pr.get('选定标题', {}).get('select') or {}).get('name', '')
        s = (pr.get('选定简介', {}).get('select') or {}).get('name', '')
        if t or s:
            body = {}
            if t: body['选定标题r'] = rt(t)
            if s: body['选定简介r'] = rt(s)
            r = api('PATCH', f"pages/{pg['id']}", {'properties': body})
            assert 'id' in r, str(r)[:200]
            val[plain(pr.get('排产号'))] = (t, s)
    # 3) null删旧select列(键=URL编码的属性id)
    del_body = {urllib.parse.quote(p[c]['id'], safe=''): None for c in ('选定标题', '选定简介')}
    r = api('PATCH', f'data_sources/{DS_ID}', {'properties': del_body}, ver='2026-03-11')
    if 'error' in r: sys.exit(f'删select失败: {r}')
    # 4) 改名
    r = api('PATCH', f'data_sources/{DS_ID}',
            {'properties': {'选定标题r': {'name': '选定标题'}, '选定简介r': {'name': '选定简介'}}},
            ver='2026-03-11')
    if 'error' in r: sys.exit(f'改名失败: {r}')
    back = api('GET', f'data_sources/{DS_ID}', ver='2026-03-11')['properties']
    for col in ('选定标题', '选定简介'):
        assert back[col]['type'] == 'rich_text', col
    print(f'迁移完成: {len(val)} 行值保留 {val if val else "(无已选值)"}; 两列均 rich_text')

# ---- md 解析 ----
H2_RE = re.compile(r'^## (B\d{3}) · (\S+)（(.+?)）· 开场型：(.+)$')

def parse_books(md_path):
    text = Path(md_path).read_text(encoding='utf-8')
    books, cur = [], None
    for line in text.splitlines():
        m = H2_RE.match(line.strip())
        if m:
            cur = {'id': m[1], 'word': m[2], 'chain': m[3].split('：')[0], 'chain_full': m[3],
                   'opener': m[4], 'titles': [], 'intros': [], 'rows': [], 'l4': ''}
            books.append(cur); continue
        if cur is None: continue
        s = line.strip()
        tm = re.match(r'^\d+\.\s(《.+?》)', s)
        if tm and len(cur['titles']) < 3 and not cur['rows']:
            cur['titles'].append(tm[1]); continue
        if s.startswith('**简介备选') or s.startswith('**标题备选') or s.startswith('**双语旁白**'):
            continue
        im = s.rsplit('（方向', 1)
        if re.match(r'^\d+\.\s', s) and len(im) == 2 and cur['titles'] and len(cur['intros']) < 4 \
           and not s.startswith('《'):
            cur['intros'].append(re.sub(r'^\d+\.\s*', '', im[0]).strip()); continue
        rm = re.match(r'^\|\s*(\d+)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|$', s)
        if rm and rm[1] != '序号':
            if s.count('|') != 4:
                sys.exit(f'{cur["id"]} 旁白第{rm[1]}句含单元格内竖线, 数据损坏风险: {s[:50]}')
            cur['rows'].append((rm[1], rm[2], rm[3])); continue
        if s.startswith('**L4 工单**：'):
            cur['l4'] = s.replace('**L4 工单**：', '').strip()
    return books

GUIDE = ("📖 本页使用规则（人与 Agent 共读）\n"
    "① 标题/简介唯一事实源=属性栏【选定标题/选定简介】；候选全文在【标题备选①②③/简介备选①②③④】；正文不存放标题简介（防双账本失同步）。\n"
    "② 状态联动（派生视图，不手拉）：Agent push 预处理产物→待审核；用户点选定标题/选定简介+设排产时间→自动已排产；Agent勾Agent已领取→自动已领取（生产中）；Agent交付→已交付。\n"
    "③ Agent 领料协议：筛选【状态=已排产 且 排产时间≤当日 且 Agent已领取未勾】→领取=勾选Agent已领取→读本页旁白表格+L4工单→产出L4生图提示词。\n"
    "④ 交付物=L4生图提示词（封面1+内页8，纯代码块），写入正文【生图提示词（定稿）】节，同时置状态已交付；用户手动执行生图。\n"
    "⑤ 修改意见写页尾✍️。")

def page_children(b):
    tbl = {'type': 'table', 'table': {'table_width': 3, 'has_column_header': True,
        'has_row_header': False, 'children': [
            {'type': 'table_row', 'table_row': {'cells': [
                [{'type': 'text', 'text': {'content': '序号'}}],
                [{'type': 'text', 'text': {'content': '英文'}}],
                [{'type': 'text', 'text': {'content': '中文'}}]]}}]}}
    tbl['table']['children'] += [
        {'type': 'table_row', 'table_row': {'cells': [
            [{'type': 'text', 'text': {'content': n}}],
            [{'type': 'text', 'text': {'content': e}}],
            [{'type': 'text', 'text': {'content': c}}]]}} for n, e, c in b['rows']]
    return [
        {'object': 'block', 'type': 'heading_1', 'heading_1': {'rich_text': [
            {'text': {'content': f"{b['id']} · {b['word']} · {b['chain']} · 开场型:{b['opener']}"}}]}},
        {'object': 'block', 'type': 'callout', 'callout': {'icon': {'type': 'emoji', 'emoji': '📖'},
            'color': 'blue_background', 'rich_text': [{'text': {'content': GUIDE}}]}},
        {'object': 'block', 'type': 'heading_2', 'heading_2': {'rich_text': [
            {'text': {'content': '双语旁白（定稿）'}}]}},
        tbl,
        {'object': 'block', 'type': 'heading_2', 'heading_2': {'rich_text': [
            {'text': {'content': 'L4 工单（生图执行规格）'}}]}},
        {'object': 'block', 'type': 'paragraph', 'paragraph': {'rich_text': [
            {'text': {'content': b['l4'] or '（待补）'}}]}},
        {'object': 'block', 'type': 'heading_2', 'heading_2': {'rich_text': [
            {'text': {'content': '✍️ 修改意见（旁白/工单）'}}]}},
        {'object': 'block', 'type': 'callout', 'callout': {'icon': {'type': 'emoji', 'emoji': '🖊'},
            'color': 'gray_background', 'rich_text': [{'text': {'content': '（无）'}}]}},
    ]

def replace_body(page_id, children):
    old = api('GET', f'blocks/{page_id}/children', ver='2026-03-11')
    if 'error' in old: sys.exit(f'读children失败: {old}')
    # 守卫: 已含交付物标题块(heading_2 且文本精确=「生图提示词（定稿）」)的页面拒绝无意识重建
    # (不能用子串匹配: 每页 GUIDE 使用规则里引用了这七个字, 会误伤所有页面)
    for b in old['results']:
        t = b.get('type', '')
        txt = ''.join(x['plain_text'] for x in b.get(t, {}).get('rich_text', []))
        if t == 'heading_2' and txt.strip() == '生图提示词（定稿）' and '--force' not in sys.argv:
            sys.exit(f'页面含「生图提示词（定稿）」交付物标题块。push 会销毁它; 确认重建加 --force')
    # 先保住用户写在页尾的✍️修改意见(重推不销毁, 审查SHOULD修复), 拼到新块末尾
    old_yijian = []
    for b in old['results']:
        t = b.get('type', '')
        txt = ''.join(x['plain_text'] for x in b.get(t, {}).get('rich_text', []))
        if t == 'callout' and '修改意见' in txt and '本页使用规则' not in txt:
            old_yijian.append(txt)
    if old_yijian and not any('修改意见' in json.dumps(c, ensure_ascii=False) for c in children):
        children = children + [{'object': 'block', 'type': 'callout', 'callout': {
            'rich_text': [{'text': {'content': '\n\n'.join(old_yijian)}}],
            'icon': {'type': 'emoji', 'emoji': '✍️'}}}]
        print(f'  (保留旧✍️修改意见{len(old_yijian)}条)')
    # 先 append 新块, 成功后才归档旧块 (append 失败页面不空)
    r = api('PATCH', f'blocks/{page_id}/children', {'children': children})
    if 'error' in r: sys.exit(f'append失败(旧块未动, 页面无损): {r}')
    for b in old['results']:
        api('PATCH', f"blocks/{b['id']}", {'archived': True})
        time.sleep(0.2)
    return len(r['results'])

def book_props(b, csvrow):
    p = {'排产号': {'title': [{'text': {'content': b['id']}}]},
         '核心词': rt(b['word']), '链形': rt(b['chain']), '画风': rt(csvrow.get('画风建议', '')),
         '月': rt(csvrow.get('月', '')), '词型': rt(csvrow.get('词型分类', '')),
         '绑定形态': rt(csvrow.get('绑定形态', '')),
         '状态': {'select': {'name': csvrow.get('状态', '待产')
                             if csvrow.get('状态', '待产') in VALID_STATES
                             else '待产'}}}
    for i, t in enumerate(b['titles'][:3]):
        p[f'标题备选{"①②③"[i]}'] = rt(t)
    for i, s in enumerate(b['intros'][:4]):
        p[f'简介备选{"①②③④"[i]}'] = rt(s)
    return p

def cmd_push(md_path, csv_path=None):
    ensure_schema()
    csvrows = {}
    csv_file = Path(csv_path) if csv_path else REPO / 'data/production/排产台账-3个月300册.csv'
    with open(csv_file, encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            csvrows[row['排产号']] = row
    books = parse_books(md_path)
    pages = {plain(p['properties'].get('排产号')): p for p in query_all(None)}
    for b in books:
        row = csvrows.get(b['id'], {})
        if not row:
            print(f"⚠️ {b['id']} 不在 {csv_file.name}: 月/词型/画风等列留空")
        old = pages.get(b['id'])
        # ── 行级数据筛查(数据权限模型, 见SOP§数据权限): 已交付/弃用行 Agent 不可触 ──
        old_st = plain(old['properties'].get('状态')) if old else None
        if old_st == '已交付' and '--force' not in sys.argv:
            print(f"{b['id']} 跳过(已交付, 交付物最高保护; 确认重建加 --force)")
            continue
        if old_st == '弃用':
            print(f"{b['id']} 跳过(弃用行, Agent 无权复活)")
            continue
        props = book_props(b, row)
        if old:
            pid = old['id']
            # 状态转移矩阵: 仅 待产→待审核 由 push 置; 其余状态 pop 不碰(状态权在用户/后续工段)
            if old_st == '待产':
                props['状态'] = {'select': {'name': '待审核'}}
            else:
                props.pop('状态', None)
            for col in ('选定标题', '选定简介', '排产时间', 'Agent已领取', '备注'):
                props.pop(col, None)
            r = api('PATCH', f'pages/{pid}', {'properties': props})
            if 'error' in r: sys.exit(f"{b['id']} 属性失败: {r}")
            n = replace_body(pid, page_children(b))
            print(f"{b['id']} 更新: 属性OK, 正文{n}块, URL={old['url']}")
        else:
            # 新建行: push语义=素材已预处理 → 首推即待审核(CSV显式给其它状态除外)
            if props['状态']['select']['name'] == '待产':
                props['状态'] = {'select': {'name': '待审核'}}
            r = api('POST', 'pages', {'parent': {'data_source_id': DS_ID},
                                      'properties': props, 'children': page_children(b)},
                    ver='2026-03-11')
            if 'error' in r: sys.exit(f"{b['id']} 新建失败: {r}")
            print(f"{b['id']} 新建: OK(待审核), URL={r['url']}")

def cmd_import(csv_path, limit=None):
    ensure_schema()
    with open(csv_path, encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))
    have = {plain(p['properties'].get('排产号')) for p in query_all(None)}
    done = skip = 0
    for row in rows:
        if limit and done >= limit: break
        bid = row['排产号']
        if bid in have: skip += 1; continue
        props = {'排产号': {'title': [{'text': {'content': bid}}]},
                 '核心词': rt(row['核心词']), '月': rt(row['月']), '词型': rt(row['词型分类']),
                 '绑定形态': rt(row['绑定形态']), '链形': rt(row['链形建议']),
                 '画风': rt(row['画风建议'])}
        if row.get('标题草案'): props['标题备选①'] = rt(row['标题草案'])
        st = row.get('状态', '待产')
        if st in VALID_STATES:
            props['状态'] = {'select': {'name': st}}
        r = api('POST', 'pages', {'parent': {'data_source_id': DS_ID}, 'properties': props},
                ver='2026-03-11')
        if 'error' in r: sys.exit(f'{bid} 失败: {r}')
        done += 1
        if done % 25 == 0: print(f'…{done} 已导入')
        time.sleep(0.35)
    print(f'导入完成: 新增{done} 跳过(已存在){skip} / 总{len(rows)}行')

def cmd_poll(today=None):
    today = today or datetime.date.today().isoformat()
    flt = {'and': [
        {'property': '状态', 'select': {'equals': '已排产'}},
        {'property': '排产时间', 'date': {'on_or_before': today}},
        {'property': 'Agent已领取', 'checkbox': {'equals': False}}]}
    hits = query_all(flt)
    # 兜底诊断(审查BLOCKER修复): 到期未进生产的两类根因分查
    warn_review = query_all({'and': [
        {'property': '状态', 'select': {'equals': '待审核'}},
        {'property': '排产时间', 'date': {'on_or_before': today}},
        {'property': 'Agent已领取', 'checkbox': {'equals': False}}]})
    if warn_review:
        ids = ','.join(plain(p['properties'].get('排产号')) for p in warn_review)
        print(f'⚠️ {len(warn_review)}行待审核+已到期({ids}) → 自动化规则1未配置/未生效(条件须=待审核), 请查页面⚡')
    warn_raw = query_all({'and': [
        {'property': '状态', 'select': {'equals': '待产'}},
        {'property': '排产时间', 'date': {'on_or_before': today}},
        {'property': 'Agent已领取', 'checkbox': {'equals': False}}]})
    if warn_raw:
        ids = ','.join(plain(p['properties'].get('排产号')) for p in warn_raw)
        print(f'⚠️ {len(warn_raw)}行待产+已到期({ids}) → 预处理(push)落后于排产计划')
    for pg in hits:
        pr = pg['properties']
        # 领取动作: 勾checkbox+置生产中 = 单次原子PATCH (竞态审查修复)
        r1 = api('PATCH', f"pages/{pg['id']}", {'properties': {
            'Agent已领取': {'checkbox': True},
            '状态': {'select': {'name': '已领取（生产中）'}}}})
        if 'error' in r1: sys.exit(f"领取失败: {r1}")
        print(f"工单 {plain(pr.get('排产号'))} | 词={plain(pr.get('核心词'))} | "
              f"标题={plain(pr.get('选定标题')) or '(未选!)'} | 简介={plain(pr.get('选定简介')) or '(未选!)'} | {pg['url']}")
    # 审查SHOULD: 未选定标题的行不进生产(选定标题=人工审核完成的标志)
    for pg in hits:
        pr = pg['properties']
        if not plain(pr.get('选定标题')):
            r2 = api('PATCH', f"pages/{pg['id']}", {'properties': {
                'Agent已领取': {'checkbox': False},
                '状态': {'select': {'name': '待审核'}}}})
            if 'id' in r2:
                print(f"退回: {plain(pr.get('排产号'))} 未选定标题 → 退回待审核(需人工选定后才可投产)")
    # 自愈通道: 历史竞态/中断造成的[已勾但状态=已排产]行, 纠正状态
    stuck = query_all({'and': [
        {'property': '状态', 'select': {'equals': '已排产'}},
        {'property': 'Agent已领取', 'checkbox': {'equals': True}}]})
    for pg in stuck:
        r = api('PATCH', f"pages/{pg['id']}", {'properties': {'状态': {'select': {'name': '已领取（生产中）'}}}})
        if 'id' in r:
            print(f"自愈: {plain(pg['properties'].get('排产号'))} 已勾未置生产中 → 已纠正")
    print(f'poll完成: 领取{len(hits)}单 (截止{today})')

def cmd_deliver(book_id, prompts_path):
    prompts = [l.strip() for l in Path(prompts_path).read_text(encoding='utf-8').splitlines() if l.strip()]
    pages = {plain(p['properties'].get('排产号')): p for p in query_all(None)}
    if book_id not in pages: sys.exit(f'找不到 {book_id}')
    pid = pages[book_id]['id']
    # ── deliver 准入闸门(数据权限模型): 只有领过料的行可交付 ──
    st = plain(pages[book_id]['properties'].get('状态'))
    if st == '已交付':
        sys.exit(f'{book_id} 已交付, 拒绝重复交付(如需重做: 先人工把状态置回待审核)')
    if st not in ('已排产', '已领取（生产中）'):
        sys.exit(f'{book_id} 状态={st}, 未经领取审核的行禁止交付(须先 poll 领取)')
    if len(prompts) != 9 and '--force' not in sys.argv:
        sys.exit(f'提示词{len(prompts)}条≠9(封面1+内页8), 确认无误加 --force')
    children = [{'object': 'block', 'type': 'heading_2', 'heading_2': {'rich_text': [
        {'text': {'content': '生图提示词（定稿）'}}]}}]
    labels = ['封面'] + [f'内页{i}' for i in range(1, len(prompts))]
    for lab, ptext in zip(labels, prompts):
        children.append({'object': 'block', 'type': 'heading_3', 'heading_3': {'rich_text': [
            {'text': {'content': lab}}]}})
        children.append({'object': 'block', 'type': 'code', 'code': {
            'language': 'plain text', 'rich_text': [{'text': {'content': ptext}}]}})
    n = replace_body_append(pid, children)
    r = api('PATCH', f'pages/{pid}', {'properties': {'状态': {'select': {'name': '已交付'}}}})
    assert 'id' in r, str(r)[:200]
    print(f'{book_id} 交付完成: 提示词{len(prompts)}条写入({n}块), 状态→已交付')

def replace_body_append(page_id, children):
    r = api('PATCH', f'blocks/{page_id}/children', {'children': children})
    if 'error' in r: sys.exit(f'append失败: {r}')
    return len(r['results'])

def cmd_status():
    pages = query_all(None)
    cnt = {}
    for p in pages:
        s = plain(p['properties'].get('状态')) or '(无状态)'
        cnt[s] = cnt.get(s, 0) + 1
    print(f'台账共{len(pages)}行: ' + ' | '.join(f'{k}={v}' for k, v in sorted(cnt.items())))

if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'status'
    if cmd == 'migrate': migrate()
    elif cmd == 'push': cmd_push(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
    elif cmd == 'import': cmd_import(sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else None)
    elif cmd == 'poll': cmd_poll(sys.argv[2] if len(sys.argv) > 2 else None)
    elif cmd == 'deliver': cmd_deliver(sys.argv[2], sys.argv[3])
    elif cmd == 'status': cmd_status()
    else: sys.exit('用法: migrate|push <md>|import <csv> [limit]|poll [date]|deliver <排产号> <prompts>|status')
