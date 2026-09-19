# Notion 排产中控台 SOP（picturebook-creator · 2026-09-19 定版）

> **定位**：Notion《绘本排产中控台》= 排产与内容确认的唯一事实源；本仓 = 创作规则与工具链唯一事实源。两边用「排产号」关联。
> **工具**：`bin/notion_kanban.py`（import/push/poll/deliver/migrate/status）。凭证走 `~/.hermes/.env` 的 NOTION_API_KEY，Id 硬编码只在脚本 CONFIG 区。

## 一、台账 DB 结构（15 属性）

排产号(title) / 核心词 / 月 / 词型 / 绑定形态 / 链形 / 画风 / 标题备选①②③ / 简介备选①②③④（以上 rich_text）｜状态(select) / 排产时间(date) / Agent已领取(checkbox) / 备注。

**信息唯一性**：候选全文进属性列（标题备选①②③ / 简介备选①②③④），用户改写【选定标题】【选定简介】两格=确认；**正文永不存放标题/简介**（防双账本失同步）。

**状态机（派生视图，不手拉）**：待产 →(用户设排产时间,页面自动化)→ 已排产 →(Agent勾领取,自动化+poll兜底)→ 已领取（生产中）→(Agent交付)→ 已交付；弃用旁路。

## 二、Notion 页面自动化规则（用户在页面配一次）

数据库 ⚡ → New automation：
1. 触发「排产时间 edited」+条件 状态=待产 → 动作设状态=已排产
2. 触发「Agent已领取 checked」→ 动作设状态=已领取（生产中）

（自动化规则只能页面建，API 建不了；poll 自带兜底：到期但状态仍待产会提示。）

## 三、全流程命令

```bash
# 0. 生成台账(仅首次/新批次): 产出CSV后导入, CSV即弃
python3 bin/gen_schedule.py ...
# 1. 导入300册(属性行, 断点续传: 已存在排产号自动跳过, 0.35s/行限速)
python3 bin/notion_kanban.py import data/production/排产台账-3个月300册.csv
# 2. L1-L3完成后: 三件套md → 六段页面 + 备选列回填(重复执行安全, 幂等)
python3 bin/notion_kanban.py push data/production/测试批B001-B005-标题简介旁白.md
# 3. 每日领料: 筛[已排产+排产时间≤今日+未勾] → 自动勾选+置生产中+打印工单
python3 bin/notion_kanban.py poll [YYYY-MM-DD]
# 4. L4完成后交付: 提示词9行(封面1+内页8) → 页面「生图提示词(定稿)」节 + 状态置已交付
python3 bin/notion_kanban.py deliver B00X prompts.txt
# 任意时刻: 台账状态计数
python3 bin/notion_kanban.py status
```

**单册页面六段结构**（push 生成，人与 Agent 共读）：H1 信息行 → 📖使用规则callout → 双语旁白table(序号|英文|中文) → L4工单 → 生图提示词(定稿,交付后) → ✍️修改意见callout。

## 四、API 坑清单（实测踩实, 勿回退）

1. **属性类型转换被带值阻塞**：select 列有值时，rich_text 写入被 400 拒（换版本头无效）。迁移正确序 = 建临时列→拷值→删旧→改名（`migrate` 命令）。
2. **删属性 = 值传 null**（2026-03-11 版 Update a data source 文档原文 "Properties set to null will be removed"）。`{"removed":true}` 是错的（400 列举所有应有键）。键必须是 URL 编码的属性 id（中文名会被当 id 报 "Could not find property_item"）。
3. **2022 版 PATCH pages 对 rich_text 键的 schema 解释滞后**：迁移动作统一带 `Notion-Version: 2026-03-11` + data_sources 端点。
4. **新建页面 = POST /pages**（PATCH 无 id 是 Invalid request URL）；parent 用 `data_source_id` 或 `database_id` 皆可。
5. **query filter 的 select 条件键是 `equals`**，不是 `name`（2026 版 data_sources query）。
6. **表格块 >100 行拆批**：先建 table(含表头行)，子行按批 PATCH append 到该 table 块（`children` 端点）。8 句旁白单请求无压力。
7. **单请求 children ≤100 块**：单册页面约 27 块，安全；整批复制才需要分批。
8. **select 选项修剪**：PATCH databases 传新 options 全量数组即可删除多余选项（孤儿值行需手动改值）。
9. **限速**：全库写路径 0.35s/行；429 自动退避（api() 内置 3 次指数重试）。
