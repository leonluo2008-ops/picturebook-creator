# -*- coding: utf-8 -*-
"""排产台账生成器（批量排产模式·五步流程第①步）
参数化改造自 2026-09-18 300册实测版（seed=42 输出与首版台账逐字节一致）。
用法:
  python3 bin/gen_schedule.py                          # 默认3个月×100册, 写 data/production/
  python3 bin/gen_schedule.py --months 2 --per-month 100 --out /tmp/plan.csv
"""
import argparse
import csv
import os
import random
import re
import glob
from collections import Counter

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ap = argparse.ArgumentParser(description='绘本批量排产台账生成器')
ap.add_argument('--vocab-dir', default=os.path.join(SKILL_DIR, 'data', 'vocab'))
ap.add_argument('--out', default=os.path.join(SKILL_DIR, 'data', 'production', '排产台账-3个月300册.csv'))
ap.add_argument('--months', type=int, default=3)
ap.add_argument('--per-month', type=int, default=100)
ap.add_argument('--seed', type=int, default=42)
args = ap.parse_args()

random.seed(args.seed)
TOTAL = args.months * args.per_month

rows = list(csv.DictReader(open(os.path.join(args.vocab_dir, 'dolch.csv'))))
fry = list(csv.DictReader(open(os.path.join(args.vocab_dir, 'fry_1-300.csv'))))
fry_map = {r['word'].lower(): int(r['fry_rank']) for r in fry}

VERBS = ['run','jump','play','eat','sleep','walk','ride','sing','wash','open','stop','read','write','draw','drink','pick','carry','cut','grow','hold','laugh','start','try','fall','fly','give','help','make','put','take','tell','use','work','call','buy','sit','pull','find','look','see','said','go','come','get','ask','live','want','wish','hear','talk','leave','turn','point','show','spell','study','follow','miss','need','change','move']
ADJS = ['big','little','funny','pretty','new','old','good','cold','hot','warm','clean','small','full','long','round','fast','better','best','kind','great','hard','close','same','real','young','high','last','late']
COLORS_NUMS = ['red','blue','yellow','black','brown','green','white','one','two','three','four','five','six','seven','eight','ten']
PREPS = ['up','down','in','on','under','over','out','off','around','through','near','above','below','between','into']
QUESTIONS = ['what','where','who','why','when','how','which']
PRONOUNS = ['i','you','we','me','my','he','she','they','us','our','him','her','them','his','their','your']


def classify(w, lvl):
    lw = w.lower()
    if lvl == 'noun':
        return '名词'
    if lw in PREPS:
        return '位置介词'
    if lw in QUESTIONS:
        return '疑问词'
    if lw in PRONOUNS:
        return '人称代词'
    if lw in COLORS_NUMS:
        return '颜色/数字'
    if lw in VERBS:
        return '动作动词'
    if lw in ADJS:
        return '形容词'
    if lw in fry_map:
        return 'Fry具象补充'
    return '功能词'


chains = ['问答链','动作空间链','量级递进链','过程链','仪式收束链','藏找游戏链','接力链','声音反转链',
          '自然循环链','空间寻找链','收集链','数数递进链','感官发现链','位置变换链','模仿扮演链','时间顺序链']
styles = ['拼贴风(Eric Carle式)','水彩风','蜡笔童趣风','剪纸风','粉彩风','简笔矢量风']

cat_map = {}
for r in rows:
    c = classify(r['word'], r['level'])
    cat_map[r['word'].lower()] = (c, r)
seen_fry = {r['word'].lower() for r in rows}
for r in fry:
    lw = r['word'].lower()
    if lw not in seen_fry:
        c = classify(r['word'], 'fry_only')
        cat_map[lw] = (c, {'word': r['word'], 'level': 'fry', 'cn': r['cn']})

stats = Counter(c for c, _ in cat_map.values())
print('=== 422词分类统计 ===')
for k, v in stats.most_common():
    print(f'  {k}: {v}')


def books_of(cats):
    return [(lw, c, r) for lw, (c, r) in cat_map.items() if c in cats]


m1 = books_of(['名词'])
m2 = books_of(['动作动词', '形容词', '颜色/数字', '位置介词', '疑问词', '人称代词'])
m3a = books_of(['Fry具象补充'])
print(f'名词月: {len(m1)} | 词族月: {len(m2)} | Fry补充: {len(m3a)} | 合计一轮: {len(m1)+len(m2)+len(m3a)}')


def sort_key(item):
    lw, c, r = item
    return (fry_map.get(lw, 999), lw)


m1.sort(key=sort_key)
m2.sort(key=sort_key)
m3a.sort(key=sort_key)

remaining = TOTAL - len(m1) - len(m2) - len(m3a)
first_round_words = [lw for lw, _, _ in m1 + m2 + m3a]
round2_pool = sorted(first_round_words, key=lambda lw: fry_map.get(lw, 999))[:max(remaining, 0)]
print(f'二轮册: {len(round2_pool)} (总{TOTAL})')


def bind_form(lw, rnd):
    if rnd == 1:
        return lw
    c = cat_map[lw][0]
    if c in ('动作动词',):
        return lw + 'ing'
    if c == '名词':
        return 'the ' + lw
    return lw


def title_cn(cn):
    return cn.split('（')[0].strip() or cn


plan = []
idx = 0
r1_chain = {}


def emit(lw, c, r, rnd, month):
    global idx
    idx += 1
    if rnd == 2:
        chain = chains[(idx * 7) % 16]
        if chain == r1_chain.get(lw):
            chain = chains[(chains.index(chain) + 5) % 16]
    else:
        chain = chains[idx % 16]
        r1_chain[lw] = chain
    style = styles[idx % 6]
    plan.append((f'B{idx:03d}', f'M{month}', r['word'], c, bind_form(lw, rnd),
                 f"《{title_cn(r['cn'])} · {r['word'].capitalize() if c=='名词' else r['word']}》",
                 chain, style, rnd, '待产'))


m2v = [x for x in m2 if x[1] == '动作动词']
for lw, c, r in m1:
    emit(lw, c, r, 1, 1)
for lw, c, r in m2v[:5]:
    emit(lw, c, r, 1, 1)
m2_rest = [(lw, c, r) for lw, c, r in m2 if lw not in {x[0] for x in m2v[:5]}]
for lw, c, r in m2_rest[:100]:
    emit(lw, c, r, 1, 2)
m2_tail = m2_rest[100:]
for lw, c, r in m2_tail:
    emit(lw, c, r, 1, 3)
fry_take = args.per_month - len(m2_tail)
backlog = m3a[fry_take:]
for lw, c, r in m3a[:fry_take]:
    emit(lw, c, r, 1, 3)


def alt_title(cn_clean, word, cat):
    if cat == '名词':
        return f"《一个{cn_clean} · {word.capitalize()}》"
    if cat == '动作动词':
        if len(cn_clean) == 1:
            return f"《{cn_clean}呀{cn_clean} · {word}》"
        return f"《{cn_clean}啦 · {word}》"
    if cat == '形容词':
        if len(cn_clean) == 1:
            return f"《{cn_clean}{cn_clean}的 · {word}》"
        return f"《{cn_clean}极了 · {word}》"
    if cat == '颜色/数字':
        base = cn_clean.rstrip('色')
        if any(ch.isdigit() or ch in '一二三四五六七八十' for ch in cn_clean):
            return f"《{cn_clean}个 · {word}》"
        return f"《{base}{base}的 · {word}》"
    if cat == '位置介词':
        return f"《{cn_clean}哪儿呢 · {word}》"
    return f"《{cn_clean}呀{cn_clean} · {word}》"


lib_dirs = ['/home/luo/huiben-v2', '/home/luo/作品']
EXCLUDE = re.compile(r'readme|agents|heartbeat|user\.md|memory|soul|skill|\.git|node_modules', re.I)
PROD = re.compile(r'旁白|生图|定妆|提示词|_L[1-4]|封面', re.I)
TITLE_STOP = {'m', 'is', 'for', 'the', 'a', 'of', 'my', 'me', 'i', 'to', 'and', 'in', 'on'}
lib_hits = {}
for d in lib_dirs:
    for p in glob.glob(d + '/**/*', recursive=True):
        if not os.path.isfile(p) or EXCLUDE.search(p):
            continue
        is_prod = ('作品' in p) or bool(PROD.search(p)) or p.endswith(('.txt',))
        if not is_prod:
            continue
        tokens = set(t for t in re.split(r'[^a-z]+', os.path.basename(p).lower()) if t)
        for w in cat_map:
            if len(w) >= 3 and w in tokens and w not in TITLE_STOP:
                lib_hits.setdefault(w, p)


def scan_lib(word):
    return lib_hits.get(word.lower(), '')


os.makedirs(os.path.dirname(args.out), exist_ok=True)
with open(args.out, 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['排产号','月','核心词','词型分类','绑定形态','标题草案','备选标题草案','库内撞名','链形建议','画风建议','轮次','状态'])
    for row in plan:
        num, mo, word, cat, bind, ttl, chain, style, rnd, st = row
        clash = scan_lib(word)
        cn_clean = ttl.split('《')[1].split(' · ')[0] if '《' in ttl else word
        alt = alt_title(cn_clean, word, cat) if clash else ''
        w.writerow([num, mo, word, cat, bind, ttl, alt, clash, chain, style, rnd, st])

print('=== 排产完成 ===')
print('总册数:', len(plan))
print('月度分布:', dict(Counter(p[1] for p in plan)))
print('词型分布:', dict(Counter(p[3] for p in plan)))
bad = [p for p in plan if p[8] == 2 and any(q[2] == p[2] and q[6] == p[6] and q[8] == 1 for q in plan)]
print('二轮链形冲突:', len(bad))
func = sorted(lw for lw, (c, _) in cat_map.items() if c == '功能词')
print('功能词(不单独成册):', len(func))
