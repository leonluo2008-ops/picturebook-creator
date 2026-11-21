import os,sys,json,urllib.request
sys.stdout.reconfigure(encoding='utf-8',line_buffering=True)
os.environ['LOCALAPPDATA']=r'C:\Users\leon3\AppData\Local'
urllib.request.install_opener(urllib.request.build_opener(urllib.request.ProxyHandler({})))
sys.path.insert(0,os.path.join(os.path.dirname(__file__),'..','scripts'))
import notion_archive as n
ds=n.resolve_data_source(); rows=[];cur=None
while True:
    body={'page_size':100}
    if cur:body['start_cursor']=cur
    r=n.api('/v1/data_sources/'+ds+'/query','POST',body);rows+=r['results']
    if not r.get('has_more'):break
    cur=r['next_cursor']
targets=[r for r in rows if n.rich_text_of(r,'排产号')=='B328']
for r in targets:
    print('TARGET',json.dumps(r,ensure_ascii=False))
    print('BODY',n.api('/v1/pages/'+r['id']+'/markdown').get('markdown',''))
done=[r for r in rows if ((r['properties'].get('状态',{}).get('select') or {}).get('name')=='已制作')]
for r in sorted(done,key=lambda r:n.rich_text_of(r,'排产号'),reverse=True):
    if n.rich_text_of(r,'排产号') in ['B209','B327'] or n.rich_text_of(r,'核心词')=='glue':
        print('SERIES',n.rich_text_of(r,'排产号'),n.rich_text_of(r,'核心词'))
        md=n.api('/v1/pages/'+r['id']+'/markdown').get('markdown','')
        start=md.find('【全局设计约定】')
        print(md[start:start+1200])

