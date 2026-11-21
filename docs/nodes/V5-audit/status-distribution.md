# 台账状态分布 · 可复跑证据

- 采集时间：2026-11-21 13:30（Asia/Shanghai）
- 工具：`mcp__notion__notion-query-data-sources`（官方 Notion MCP，OAuth）
- 数据源：`collection://3e0a3f92-69aa-8181-b457-000bcba7fc09`（排产台账）
- 模式：SQL

## 查询

```sql
SELECT "状态" AS status, COUNT(*) AS n,
       SUM(CASE WHEN "交付文件" IS NULL OR "交付文件"='' OR "交付文件"='[]' THEN 1 ELSE 0 END) AS no_files
FROM "collection://3e0a3f92-69aa-8181-b457-000bcba7fc09"
GROUP BY "状态" ORDER BY n DESC
```

## 原始输出

```json
{"results":[
 {"status":"备选","n":264,"no_files":264},
 {"status":"弃用","n":161,"no_files":161},
 {"status":"已制作","n":128,"no_files":120},
 {"status":"待制作","n":72,"no_files":72},
 {"status":"已筛查","n":12,"no_files":12},
 {"status":"待生图","n":2,"no_files":2}
],"has_more":false}
```

## 口径

- 合计 264+161+128+72+12+2 = **639 行**，与「全库 639 行」一致。
- 「修改中」「已生图」两个 schema 选项**没有行**，故未出现在结果里（零样本，不是缺失）。
- `no_files` = 「交付文件」为空的行数。**已制作 128 本中 120 本无交付文件** → 判断交付状态看「交付文件」列，不看状态。
- 用途：支撑 SKILL.md 状态机小节里的分布数字（此前该数字在 docs 内无来源，被审计指出）。
