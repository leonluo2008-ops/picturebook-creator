import subprocess
books = [('pajamas','B572'),('zipper','B573'),('glasses','B574'),('chopsticks','B627'),('belt','B668'),('sleeve','B669'),('collar','B670'),('ribbon','B671'),('hairpin','B672'),('hairband','B673'),('fence','B674'),('tent','B675'),('ladder','B676'),('hair dryer','B677'),('remote control','B678'),('rice cooker','B679'),('spring roll','B685'),('meatball','B686'),('soy milk','B687'),('donut','B688'),('post office','B689'),('fire station','B690'),('police station','B691'),('flower shop','B692'),('toy store','B693'),('frisbee','B694'),('carousel','B695'),('jump rope','B696'),('braid','B698'),('croissant','B699'),('peanut butter','B700'),('ketchup','B701'),('morning glory','B702'),('clownfish','B703'),('tissue box','B704'),('dish soap','B705'),('watering can','B706'),('treehouse','B707')]
out = []
for w, b in books:
    r = subprocess.run(['python','scripts/notion_archive.py','--word',w,'--locate'], capture_output=True, text=True, encoding='utf-8')
    st = '?'
    for l in r.stdout.splitlines():
        if '状态=' in l:
            st = l.split('状态=')[1].strip()
            break
    out.append(b + '\t' + w + '\t' + st)
open(r'scratch/台账状态盘点.txt','w',encoding='utf-8').write('\n'.join(out))
from collections import Counter
c = Counter(l.split('\t')[2] for l in out)
print(dict(c))
for l in out:
    if not l.endswith('待生图'):
        print('异常:', l)
