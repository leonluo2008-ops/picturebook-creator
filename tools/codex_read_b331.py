import os,sys,urllib.request
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
target=[x for x in rows if n.rich_text_of(x,'排产号')=='B331'][0]
md=n.api('/v1/pages/'+target['id']+'/markdown').get('markdown','')
start=md.find('【全局设计约定】')
print(md[start:start+1800])
