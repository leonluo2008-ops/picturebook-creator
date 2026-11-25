import re

for book, f in [('B689', 'projects/B689/l4_v3.txt'), ('B693', 'projects/B693/l4_v3.txt')]:
    t = open(f, encoding='utf-8').read()
    pages = re.split(r'(?=页序: )', t)
    print(f'=== {book} ===')
    for p in pages:
        seq = re.search(r'页序: (.+)', p)
        if not seq:
            continue
        name = seq.group(1).strip()
        narr_m = re.search(r'旁白: (.+)', p)
        eng_m = re.search(r'入画英文: (.+)', p)
        prompt_m = re.search(r'生图提示词: (.{0,120})', p)
        if not narr_m or not eng_m:
            continue
        narr = narr_m.group(1).strip()
        eng = eng_m.group(1).strip()
        prompt = (prompt_m.group(1)[:100] + '...') if prompt_m else ''
        kw = 'post office' if book == 'B689' else 'toy store'
        has_word = kw in eng.lower().replace('"','').replace('[','').replace(']','').replace("'","")
        tag = '认读' if has_word else '省略'
        if book == 'B689' and name in ('P3', 'P1'):
            print(f'\n--- {book} {name} ({tag}页) ---')
            print(f'旁白: {narr}')
            print(f'入画英文: {eng}')
            print(f'提示词节选: {prompt}')
        if book == 'B693' and name in ('P5', 'P6'):
            print(f'\n--- {book} {name} ({tag}页) ---')
            print(f'旁白: {narr}')
            print(f'入画英文: {eng}')
            print(f'提示词节选: {prompt}')

print('\n=== 全书省略页入画英文核对 ===')
for book, f in [('B689', 'projects/B689/l4_v3.txt'), ('B693', 'projects/B693/l4_v3.txt')]:
    t = open(f, encoding='utf-8').read()
    pages = re.split(r'(?=页序: )', t)
    kw = 'post office' if book == 'B689' else 'toy store'
    for p in pages:
        seq = re.search(r'页序: (.+)', p)
        if not seq:
            continue
        name = seq.group(1).strip()
        eng_m = re.search(r'入画英文: (.+)', p)
        if not eng_m:
            continue
        eng = eng_m.group(1).strip()
        if eng == '[]':
            has_kw = kw.lower() in p.lower()
            print(f'{book} {name}: 入画英文=[] 画面含目标词字样={has_kw}')
