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
targets=[r for r in rows if n.rich_text_of(r,'排产号')=='B267']
if not targets:
    print('MATCH',0)
    nums=sorted({n.rich_text_of(x,'排产号') for x in rows if n.rich_text_of(x,'排产号','').startswith('B')})
    print('NEAR',nums[-5:])
else:
    for r in targets:
        props=r['properties']
        def sel(name):
            s=props.get(name,{}).get('select')
            return s.get('name') if s else None
        st=sel('状态')
        print('MATCH',1)
        print('PAGE_ID',r['id'])
        print('核心词',n.rich_text_of(r,'核心词'))
        print('词型',n.rich_text_of(r,'词型') or props.get('词型'))
        print('状态',st)
        print('BODY_START')
        print(n.api('/v1/pages/'+r['id']+'/markdown').get('markdown',''))
        print('BODY_END')
