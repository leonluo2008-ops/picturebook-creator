import os, sys, json, collections, urllib.request
sys.stdout.reconfigure(encoding='utf-8')
sys.stdout.reconfigure(line_buffering=True)
urllib.request.install_opener(urllib.request.build_opener(urllib.request.ProxyHandler({})))
os.environ['LOCALAPPDATA'] = r'C:\Users\leon3\AppData\Local'
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
import notion_archive as n

# Only GET and read-only database queries; never invokes archive/create/update.
print('CONTROL', n._title_of_page(n.api('/v1/pages/'+n.DEFAULT_CONTROL_PAGE_ID)))
kids = n.api('/v1/blocks/'+n.DEFAULT_CONTROL_PAGE_ID+'/children?page_size=100')
print('CHILDREN', json.dumps([{'type':b['type'],'title':b.get(b['type'],{}).get('title','')} for b in kids['results']],ensure_ascii=False))
ds=n.resolve_data_source()
meta=n.api('/v1/data_sources/'+ds)
print('STATUS_OPTIONS',json.dumps(meta.get('properties',{}).get('状态',{}),ensure_ascii=False))
rows=[]; cur=None
while True:
    body={'page_size':100}
    if cur: body['start_cursor']=cur
    r=n.api('/v1/data_sources/'+ds+'/query','POST',body)
    rows+=r['results']
    if not r.get('has_more'): break
    cur=r['next_cursor']
def status(r):
    return ((r.get('properties',{}).get('状态',{}).get('select') or {}).get('name') or '空')
print('TOTAL',len(rows),'COUNTS',json.dumps(collections.Counter(map(status,rows)),ensure_ascii=False))
for state in ['已制作','待生图','修改中']:
    selected=sorted([r for r in rows if status(r)==state],key=lambda r:n.rich_text_of(r,'排产号'))
    print('ROWS',state,json.dumps([{'no':n.rich_text_of(r,'排产号'),'word':n.rich_text_of(r,'核心词'),'url':r.get('url')} for r in selected[-5:]],ensure_ascii=False))
    for row in selected[-2:]:
        md=n.api('/v1/pages/'+row['id']+'/markdown').get('markdown','')
        print('SAMPLE',n.rich_text_of(row,'排产号'),md[:1500])

