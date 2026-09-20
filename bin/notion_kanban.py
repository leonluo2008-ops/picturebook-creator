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
STATUS_OPTS = [{'name': '待产', 'color': 'gray'}, {'name': '待预处理', 'color': 'pink'}, {'name': '待审核', 'color': 'purple'}, {'name': '已审核', 'color': 'orange'}, {'name': '已排产', 'color': 'blue'},
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
            # 存量选项原样回写(带id/color, 防「Cannot update color」400——09-20实测);
            # 新选项才用代码声明色; 线上自定义选项保持原样
            online_by_name = {o['name']: o for o in props['状态']['select'].get('options', [])}
            merged = [online_by_name.get(o['name'], o) for o in STATUS_OPTS]
            merged += [o for o in props['状态']['select'].get('options', [])
                       if o['name'] not in {x['name'] for x in STATUS_OPTS}]
            patch['状态'] = {'select': {'options': merged}}
    if 'Agent预处理中' not in props:
        patch['Agent预处理中'] = {'checkbox': {}}   # 预处理工单领取标记(审查SHOULD: checkbox列也要自动建)
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
    "② 状态联动（派生视图，不手拉）：用户置待预处理=下预处理工单，Agent领单创作push→待审核；批量push预处理产物→待审核；用户审核裁决手动置已审核→自动化转已排产；Agent勾Agent已领取→自动已领取（生产中）；Agent交付→已交付。\n"
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

def book_props(b, is_new=False):
    """属性构造(Notion唯一中控版): 只写 md 来源字段(排产号/核心词/链形/标题备选/简介备选)。
    月/词型/绑定形态/画风等元数据单源=Notion属性栏, push 永不回写防双账本;
    新建行状态=待审核(push语义=预处理完成), 更新行状态由调用方按转移矩阵处理。"""
    p = {'排产号': {'title': [{'text': {'content': b['id']}}]},
         '核心词': rt(b['word']), '链形': rt(b['chain'])}
    if is_new:
        p['状态'] = {'select': {'name': '待审核'}}
    for i, t in enumerate(b['titles'][:3]):
        p[f'标题备选{"①②③"[i]}'] = rt(t)
    for i, s in enumerate(b['intros'][:4]):
        p[f'简介备选{"①②③④"[i]}'] = rt(s)
    return p

def cmd_push(md_path):
    ensure_schema()
    # ── 创作模型闸门(fail-closed, 09-10红线): md【头部】须标「创作模型:」且为Gemini/GPT系 ──
    # 只扫首个H2之前(审查SHOULD: 全文扫描可被正文引用行绕过=fail-open)
    raw = Path(md_path).read_text(encoding='utf-8')
    mhead = re.search(r'^创作模型[:：]\s*(.+)$', raw.split('\n## ', 1)[0], re.M)
    if not mhead:
        sys.exit('头部缺「创作模型:」标注行 — 09-10红线要求三件套标注创作模型, 拒收')
    if not re.match(r'(?i)\s*(gemini|gpt)', mhead.group(1)):
        sys.exit(f'创作模型「{mhead.group(1).strip()}」非Gemini/GPT系 — 违反创作红线, 拒收')
    books = parse_books(md_path)
    if not books:
        sys.exit('解析到0册 — md不匹配H2契约「## B00X · 词（链形）· 开场型：型」, 拒收(fail-closed)')
    from narration_quality_check import title_check, batch_check
    tc = title_check({b['word']: b['titles'] for b in books})
    if tc:
        sys.exit('标题备选闸门拦截:\n- ' + '\n- '.join(tc) + '\n(每条备选必须显示核心词, 修正 md 后重推)')
    bc = batch_check({b['word']: (b['rows'][0][1], b['rows'][0][2]) for b in books if b['rows']})
    if bc:
        sys.exit('开场句查重拦截:\n- ' + '\n- '.join(bc))
    pages = {plain(p['properties'].get('排产号')): p for p in query_all(None)}
    for b in books:
        old = pages.get(b['id'])
        # ── 行级数据筛查(数据权限模型, 见SOP§数据权限): 已交付/弃用行 Agent 不可触 ──
        old_st = plain(old['properties'].get('状态')) if old else None
        if old_st == '已交付' and '--force' not in sys.argv:
            print(f"{b['id']} 跳过(已交付, 交付物最高保护; 确认重建加 --force)")
            continue
        if old_st == '弃用':
            print(f"{b['id']} 跳过(弃用行, Agent 无权复活)")
            continue
        props = book_props(b, is_new=not old)
        if old:
            pid = old['id']
            # 状态转移矩阵: 仅 待产→待审核 由 push 置; 其余状态不碰(状态权在用户/后续工段)
            # 元数据列(月/词型/绑定形态/画风)不在 props 里, 天然不碰=Notion单源
            if old_st in ('待产', '待预处理'):
                props['状态'] = {'select': {'name': '待审核'}}
            if old_st == '待预处理':
                props['Agent预处理中'] = {'checkbox': False}   # 领单勾随push清掉(审查SHOULD: 防勾永真污染)
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

def cmd_preprocess(mode='--list'):
    """预处理工单(消息驱动, 无cron): 状态=待预处理 即工单。
    --list: 列工单; --claim: 领单=原子勾「Agent预处理中」(防连发消息/双机重复创作)。
    领后创作(创作模型红线: Gemini/GPT系子agent)→push(自动翻待审核+清勾)。仅本机执行(无CAS, SOP约定)。"""
    ensure_schema()
    flt = {'property': '状态', 'select': {'equals': '待预处理'}}
    if mode == '--claim':
        flt = {'and': [flt, {'property': 'Agent预处理中', 'checkbox': {'equals': False}}]}
    rows = query_all(flt)
    if not rows:
        print('无预处理工单' + ('(或已被领取)' if mode == '--claim' else ''))
        return
    if mode == '--list':
        for pg in rows:
            pr = pg['properties']
            claim = '🔒已领' if pr.get('Agent预处理中', {}).get('checkbox') else '待领'
            print(f"工单 {plain(pr.get('排产号'))} | 词={plain(pr.get('核心词'))} | 链形={plain(pr.get('链形'))} | 画风={plain(pr.get('画风'))} | {claim} | {pg['url']}")
        return
    for pg in rows:   # --claim
        pr = pg['properties']
        r1 = api('PATCH', f"pages/{pg['id']}", {'properties': {'Agent预处理中': {'checkbox': True}}})
        if 'error' in r1: sys.exit(f"领单失败: {r1}")
        print(f"已领单 {plain(pr.get('排产号'))} | 词={plain(pr.get('核心词'))} | 链形={plain(pr.get('链形'))} | 画风={plain(pr.get('画风'))}")

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
    warn_pending = query_all({'and': [
        {'property': '状态', 'select': {'equals': '待产'}},
        {'property': '排产时间', 'date': {'on_or_before': today}},
        {'property': 'Agent已领取', 'checkbox': {'equals': False}}]})
    if warn_pending:
        ids = ','.join(plain(p['properties'].get('排产号')) for p in warn_pending)
        print(f'⚠️ {len(warn_pending)}行待产+已到期({ids}) → 预处理(push)落后于排产计划')
    # 已审核滞留诊断: 用户已裁决但排产时间未设/自动化未建 → 卡在已审核不进生产
    warn_reviewed = query_all({'and': [
        {'property': '状态', 'select': {'equals': '已审核'}},
        {'property': 'Agent已领取', 'checkbox': {'equals': False}}]})
    if warn_reviewed:
        ids = ','.join(plain(p['properties'].get('排产号')) for p in warn_reviewed)
        print(f'⚠️ {len(warn_reviewed)}行已审核滞留({ids}) → 设排产时间(自动化置已排产), 或检查⚡规则1')
    # 跳过预处理回流诊断(审查SHOULD): 空「标题备选①」+生产态=疑似手滑跳过预处理
    for st in ('已审核', '已排产'):
        bad = query_all({'and': [
            {'property': '状态', 'select': {'equals': st}},
            {'property': '标题备选①', 'rich_text': {'is_empty': True}}]})
        if bad:
            ids = ','.join(plain(p['properties'].get('排产号')) for p in bad)
            print(f'⚠️ {len(bad)}行{st}但备选列空({ids}) → 疑似跳过预处理, 请人工置回待预处理')
    # 待预处理滞留诊断(审查NIT分两态): 未勾=工单没人领; 已勾+排产时间已过=创作会话卡死
    warn_pre_idle = query_all({'and': [
        {'property': '状态', 'select': {'equals': '待预处理'}},
        {'property': 'Agent预处理中', 'checkbox': {'equals': False}}]})
    if warn_pre_idle:
        ids = ','.join(plain(p['properties'].get('排产号')) for p in warn_pre_idle)
        print(f'⏳ {len(warn_pre_idle)}行待预处理待领({ids}) → 给Agent发「处理待预处理工单」')
    warn_pre_stuck = query_all({'or': [
        {'and': [
            {'property': '状态', 'select': {'equals': '待预处理'}},
            {'property': 'Agent预处理中', 'checkbox': {'equals': True}},
            {'property': '排产时间', 'date': {'is_empty': True}}]},
        {'and': [
            {'property': '状态', 'select': {'equals': '待预处理'}},
            {'property': 'Agent预处理中', 'checkbox': {'equals': True}},
            {'property': '排产时间', 'date': {'on_or_before': today}}]}]})
    if warn_pre_stuck:
        ids = ','.join(plain(p['properties'].get('排产号')) for p in warn_pre_stuck)
        print(f'⚠️ {len(warn_pre_stuck)}行已领但滞留({ids}) → 创作会话中断, 重发「处理待预处理工单」或人工检查')
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

def validate_l4(doc):
    """L4 标准文档合规校验(l1-l4-strict-format-template.md + 铁律11/15)
    任一不过即拒收: deliver 只接受完整标准 L4, 不接受裸提示词"""
    errs = []
    if '生图模型：使用图片 5.0 Lite 模型' not in doc:
        errs.append('铁律15: 缺「生图模型：使用图片 5.0 Lite 模型」全局控制行')
    for seg in ('我会给你一段文字', '不要在图片中显示', '重要要求', '文字模板制', '视角变化规律'):
        if seg not in doc:
            errs.append(f'引导语段缺要素: {seg}')
    for fld in ('【全局设计约定】', '目标单词：', '目标年龄：', '文字风格：', '风格锚点：', '【主要场景锚点】'):
        if fld not in doc:
            errs.append(f'缺 {fld}')
    for k, n in (('旁白：', 9), ('比例：', 9), ('页面类型：', 9), ('生图提示词：', 9)):
        if doc.count(k) != n:
            errs.append(f'「{k}」应为9处(封面1+内页8), 实际{doc.count(k)}')
    if doc.count('3:4') != 1 or doc.count('16:9') != 8:
        errs.append(f'比例应为3:4×1+16:9×8, 实际3:4×{doc.count("3:4")} 16:9×{doc.count("16:9")}')
    if '页面类型：认知页' not in doc:
        errs.append('缺认知页(l4-page-count-checklist: 最常漏的一张)')
    if '页面类型：封面页' not in doc or '页面类型：总结语境收束页' not in doc:
        errs.append('缺封面页或收束页')
    if '每张图只允许出现这 2 个文字' not in doc:
        errs.append('缺末尾1行精简提示')
    import re as _re
    if _re.search(r'不对|应该是|更正|注意:这里|不要写', doc):
        errs.append('铁律11: 引导语含自我纠错措辞(不对/应该是/更正/注意:这里/不要写)')
    return errs

def cmd_deliver(book_id, prompts_path):
    doc = Path(prompts_path).read_text(encoding='utf-8').strip()
    errs = validate_l4(doc)
    if errs and '--force' not in sys.argv:
        sys.exit('L4文档不合标准:\n- ' + '\n- '.join(errs) + '\n(按 references/l1-l4-strict-format-template.md 重写, 确认覆盖加 --force)')
    pages = {plain(p['properties'].get('排产号')): p for p in query_all(None)}
    if book_id not in pages: sys.exit(f'找不到 {book_id}')
    pid = pages[book_id]['id']
    # ── deliver 准入闸门(数据权限模型): 只有领过料的行可交付 ──
    st = plain(pages[book_id]['properties'].get('状态'))
    if st == '已交付':
        sys.exit(f'{book_id} 已交付, 拒绝重复交付(如需重做: 先人工把状态置回待审核)')
    if st not in ('已排产', '已领取（生产中）'):
        sys.exit(f'{book_id} 状态={st}, 未经领取审核的行禁止交付(须先 poll 领取)')
    # Notion 单块 rich_text ≤2000字符: 按空行边界分块为连续 code 块
    chunks, cur = [], ''
    for para in doc.split('\n\n'):
        cand = (cur + '\n\n' + para) if cur else para
        if len(cand) > 1900 and cur:
            chunks.append(cur); cur = para
        else:
            cur = cand
        while len(cur) > 1900:              # 单段超长兜底: 硬切
            chunks.append(cur[:1900]); cur = cur[1900:]
    if cur: chunks.append(cur)
    children = [{'object': 'block', 'type': 'heading_2', 'heading_2': {'rich_text': [
        {'text': {'content': '生图提示词（定稿）'}}]}}]
    children += [{'object': 'block', 'type': 'code', 'code': {
        'language': 'plain text', 'rich_text': [{'text': {'content': c}}]}} for c in chunks]
    n = replace_body_append(pid, children)
    r = api('PATCH', f'pages/{pid}', {'properties': {'状态': {'select': {'name': '已交付'}}}})
    assert 'id' in r, str(r)[:200]
    print(f'{book_id} 交付完成: L4标准文档({len(doc)}字, 校验{"强制通过(--force)" if errs else "通过"})写入{n}块, 状态→已交付')

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
    elif cmd == 'push': cmd_push(sys.argv[2])
    elif cmd == 'import': cmd_import(sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else None)
    elif cmd == 'poll': cmd_poll(sys.argv[2] if len(sys.argv) > 2 else None)
    elif cmd == 'preprocess':
        cmd_preprocess(sys.argv[2] if len(sys.argv) > 2 else '--list')
    elif cmd == 'deliver': cmd_deliver(sys.argv[2], sys.argv[3])
    elif cmd == 'status': cmd_status()
    else: sys.exit('用法: migrate|push <md>|import <csv> [limit]|poll [date]|preprocess --list|--claim|deliver <排产号> <prompts>|status')
