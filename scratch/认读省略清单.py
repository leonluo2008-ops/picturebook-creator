import re
for book, f, kw in [('B689','projects/B689/l4_v3.txt','post office'),('B693','projects/B693/l4_v3.txt','toy store')]:
    t = open(f, encoding='utf-8').read()
    blocks = re.split(r'(?=页序: )', t)
    kept, omitted = [], []
    for b in blocks:
        m = re.search(r'页序: (.+)', b)
        if not m: continue
        name = m.group(1).strip()
        eng_m = re.search(r'入画英文: (\[.+?\])', b)
        eng = eng_m.group(1) if eng_m else ''
        if kw.lower() in eng.lower() or kw in eng:
            kept.append(name)
        else:
            omitted.append(name)
    kept_str = ', '.join(kept)
    omit_str = ', '.join(omitted)
    print(f'{book} 认读页(保留): {kept_str}')
    print(f'{book} 省略页(通过): {omit_str}')
    print()
