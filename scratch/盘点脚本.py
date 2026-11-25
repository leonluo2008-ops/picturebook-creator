import os
books = ['B572','B573','B574','B627','B668','B669','B670','B671','B672','B673','B674','B675','B676','B677','B678','B679','B685','B686','B687','B688','B689','B690','B691','B692','B693','B694','B695','B696','B698','B699','B700','B701','B702','B703','B704','B705','B706','B707']
out = []
for b in books:
    p = f'projects/{b}/l4.txt'
    if not os.path.exists(p):
        out.append(b + '\tNO_L4')
        continue
    t = open(p, encoding='utf-8').read()
    tt = open(f'projects/{b}/title_intro.md', encoding='utf-8').read() if os.path.exists(f'projects/{b}/title_intro.md') else ''
    roles = []
    if '团团' in t: roles.append('团团熊')
    if '雪球' in t: roles.append('雪球兔')
    for extra in ['小女孩','熊爷爷','蓝蓝','刺猬','獾','大狗消防','猫头鹰','梅花鹿','浣熊','长颈鹿']:
        if extra in t: roles.append(extra)
    intro_roles = 'Y' if any(x in tt for x in ['团团','雪球','小女孩','爷爷']) else 'N'
    out.append(f'{b}\t{"|".join(roles)}\t简介含角色:{intro_roles}')
open(r'scratch/角色盘点.txt','w',encoding='utf-8').write('\n'.join(out))
print('\n'.join(out))
