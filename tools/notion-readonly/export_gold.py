"""从 Notion 页面正文导出 L4 纯文本（只读源文件，写 temp），供 l4_case_check 使用。"""
import json
import re
import sys

SRC = r"C:\Users\leon3\AppData\Local\Temp\pb-notion\pages.json.B585.txt"
OUT = r"C:\Users\leon3\AppData\Local\Temp\pb-notion\B585-gold-L4.txt"

lines = open(SRC, encoding="utf-8").read().splitlines()
start = None
for i, ln in enumerate(lines):
    if ln.startswith("[code] "):
        start = i
        break
if start is None:
    print("未找到 [code] 块")
    sys.exit(1)

body = [lines[start][len("[code] "):]]
for ln in lines[start + 1:]:
    if ln.startswith("["):
        break
    body.append(ln)

text = "\n".join(body).strip() + "\n"
open(OUT, "w", encoding="utf-8").write(text)

pages = re.findall(r"^旁白[:：]", text, flags=re.M)
prompt = re.findall(r"^生图提示词[:：]", text, flags=re.M)
ratio = re.findall(r"^比例[:：]\s*(\S+)", text, flags=re.M)
ptype = re.findall(r"^页面类型[:：]\s*(\S+)", text, flags=re.M)
print("导出:", OUT)
print("字符数:", len(text))
print("页数(旁白行):", len(pages), " 生图提示词行:", len(prompt))
print("比例:", ratio)
print("页面类型:", ptype)
