import os,sys,urllib.request
sys.stdout.reconfigure(encoding='utf-8',line_buffering=True)
os.environ['LOCALAPPDATA']=r'C:\Users\leon3\AppData\Local'
urllib.request.install_opener(urllib.request.build_opener(urllib.request.ProxyHandler({})))
sys.path.insert(0,os.path.join(os.path.dirname(__file__),'..','scripts'))
from pathlib import Path
import notion_verify as v,socket
socket.getaddrinfo=v._orig_getaddrinfo
blocks=v.api('/v1/blocks/70afa013-50ea-4478-bd93-82fdf19eeebe/children?page_size=100')['results']
codes=[b for b in blocks if b['type']=='code']
actual=''.join(t.get('plain_text',t.get('text',{}).get('content','')) for t in codes[0]['code']['rich_text'])
source=Path(__file__).resolve().parents[1]/'绘本创作/作品/B267-clap/B267-clap_生图提示词.txt'
text=source.read_text(encoding='utf-8-sig')
print('len actual',len(actual),'len source',len(text),'equal',actual==text)
if actual!=text:
    for i,(a,b) in enumerate(zip(actual,text)):
        if a!=b:
            print('first diff at',i,repr(actual[max(0,i-10):i+10]),repr(text[max(0,i-10):i+10]));break
assert len(codes)==1 and actual==text
print('L4 content PASS: one code block, exact source match')

