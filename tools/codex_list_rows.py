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
itemized=[]
for x in rows:
    props=x['properties']
    def sel(name):
        s=props.get(name,{}).get('select')
        return s.get('name') if s else ''
    sno=n.rich_text_of(x,'排产号'); w=n.rich_text_of(x,'核心词'); wt=n.rich_text_of(x,'词型') or ''
    remark=n.rich_text_of(x,'备注') or ''
    if sno.startswith('B') and (wt=='动作动词' or '词群' in remark):
        itemized.append((sno,w,wt,sel('状态'),remark))
for sno,w,wt,st,rm in sorted(itemized,reverse=True)[:40]:
    print(sno,'|',w,'|',wt,'|',st,'|',rm[:80])
