# 门禁脚本缺陷记录：UTF-8 BOM 导致解析失败（2026-11-21 发现并修复）

## 现象

用 PowerShell 5.1 的 `Set-Content -Encoding UTF8` 生成夹具（带 BOM `EF BB BF`）后，四个门禁脚本**全部报「没解析到页面记录」并 exit 1**：

```
python scripts/l4_structure_check.py <BOM文件> --word coin
→ 没解析到页面记录（应以「旁白: 」行开始）   exit=1
```

## 根因

`open(path, encoding="utf-8")` 读带 BOM 的文件时，首行变成 `"\ufeff旁白: …"`，
而脚本用 `^旁白[:：]` 做行首匹配 → 第一页永远匹配不上；只有一页的稿子就是「零页」。

实测证据：
```
首字节: efbbbf
utf-8 读首行: '\ufeff旁白: one two three f'
utf-8-sig 读首行: '旁白: one two three fo'
```

## 影响面（关键）

Windows 上 `Set-Content -Encoding UTF8`、记事本「UTF-8」保存、以及不少导出工具**默认都会写 BOM**。
也就是说：**用户/脚本用常见方式存出来的稿子，会被门禁误判为「没有页面」** —— 属误报型缺陷（不放过违规，但会卡住合规稿）。

涉及四个脚本（全部中招）：
- `scripts/l4_presence_check.py`（本次新增）
- `scripts/l4_structure_check.py`（本次新增）
- `tools/l4_case_check.py`（既有）
- `tools/grammar_check.py`（既有）

## 修复

四处 `encoding="utf-8"` → `encoding="utf-8-sig"`（`utf-8-sig` 读无 BOM 文件与 `utf-8` 等价，不会引入新行为）。

## 验证

| 用例 | 期望 | 实测 |
|---|---|---|
| 空文件 | exit 1 + 提示 | ✅ |
| 单页 + 缺页面类型 + 13 词（BOM） | exit 1，报缺类型与超词 | ✅ 报出比例/类型/缺块/超词 |
| 完整 1 页 10 词（BOM） | exit 0 | ✅ |
| `--page-words` 格式错 | exit 2 | ✅ |
| `--page-words 0=coin`（封面） | 正常解析不崩 | ✅ |
| V7 coin 四门禁 | 0/0/0/0 | ✅ |
| V7b pot 四门禁 | 0/0/0/0 | ✅ |

## 待办（不自行改）

- 现有 `tools/` 下其它脚本是否也有同样的 BOM 假设，需逐个排查（本轮只改了四个门禁）。
- 建议后续给门禁加一个自测入口（把这 5 个边界用例固化成脚本），本轮未做。
