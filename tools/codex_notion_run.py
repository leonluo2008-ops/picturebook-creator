"""Run the repository Notion CLI with process-local Windows configuration."""
import os,sys,runpy,urllib.request
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8',line_buffering=True)
os.environ['LOCALAPPDATA']=r'C:\Users\leon3\AppData\Local'
urllib.request.install_opener(urllib.request.build_opener(urllib.request.ProxyHandler({})))
target=sys.argv.pop(1)
if target=='verify-paint-content':
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
    import notion_verify as v,socket
    socket.getaddrinfo=v._orig_getaddrinfo
    blocks=v.api('/v1/blocks/02ce71d4-ffbc-49bc-a291-690cf213ffd8/children?page_size=100')['results']
    codes=[b for b in blocks if b['type']=='code']
    actual=''.join(t.get('plain_text',t.get('text',{}).get('content','')) for t in codes[0]['code']['rich_text'])
    source=(Path(__file__).resolve().parents[3]/'绘本创作/作品/B328-paint/B328-paint_生图提示词.txt').read_text(encoding='utf-8')
    assert len(codes)==1 and actual==source, 'Code content mismatch'
    assert actual.count('场景一致性:')==9 and actual.count('构图要求:')==9
    print('PASS: one code block, exact source match, 9 scene references and 9 page safety requirements')
    raise SystemExit(0)
if target=='archive-paint':
    target='notion_archive'
    root=Path(__file__).resolve().parents[3]
    project=root/'绘本创作'/'作品'/'B328-paint'
    sys.argv=[sys.argv[0],'--word','paint','--no-create','--title','Let’s “Paint”!','--title-cn','拿起画笔画一画，Paint','--brief','画笔刷过去，白纸上就多了一片蓝天。还想再画一笔吗，paint？','--narration',str(project/'B328-paint_旁白.md'),'--l4',str(project/'B328-paint_生图提示词.txt'),'--date','2026-10-30']
if target not in ('notion_archive','notion_verify'):
    raise SystemExit('Unsupported CLI')
path=Path(__file__).resolve().parents[1]/'scripts'/(target+'.py')
sys.path.insert(0,str(path.parent))
if target=='notion_verify':
    import notion_verify as verifier
    import socket
    socket.getaddrinfo=verifier._orig_getaddrinfo
    raise SystemExit(verifier.main())
runpy.run_path(str(path),run_name='__main__')
