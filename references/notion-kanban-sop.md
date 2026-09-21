# Notion 排产中控台 SOP（picturebook-creator · 2026-09-19 定版）

> **定位**：Notion《绘本排产中控台》= 排产与内容确认的唯一事实源；本仓 = 创作规则与工具链唯一事实源。两边用「排产号」关联。
> **工具**：`bin/notion_kanban.py`（import/push/poll/deliver/migrate/status）。凭证走 `~/.hermes/.env` 的 NOTION_API_KEY，Id 硬编码只在脚本 CONFIG 区。

## 一、台账 DB 结构（18 属性）

排产号(title) / 核心词 / 月 / 词型 / 绑定形态 / 链形 / 画风（7 基础 rich_text/title）+ 标题备选①②③ / 简介备选①②③④（7 候选 rich_text）+ 状态(select) / 排产时间(date) / Agent已领取(checkbox) / 备注（4 流控列）。

**信息唯一性**：候选全文进属性列（标题备选①②③ / 简介备选①②③④），用户改写【选定标题】【选定简介】两格=确认；**正文永不存放标题/简介**（防双账本失同步）。

**状态机（派生视图，不手拉）**：待产(素材库原始行) →(用户手动置=**下预处理工单**)→ **待预处理** →(Agent领单创作push,自动置)→ **待审核** →(用户审核裁决,**手动置**)→ **已审核** →(页面自动化规则1)→ 已排产 →(Agent勾选领取)→ 已领取（生产中）→(Agent交付)→ 已交付；弃用旁路（待预处理→弃用/退回待产=人工撤销工单，均合法）。

**工段边界 = 状态边界**：素材预处理工段（L1-L3）的完成标志就是状态翻「待审核」——你在台账里一眼扫出哪些册 Agent 已备好料等你审（紫标），哪些还没做（灰标）。人工审核动作 = 审读三件套后**手动置「已审核」**（orange，裁决态），自动化随即转已排产。

## ⚖️ 数据权限模型（2026-09-19 定版，Agent 命令逐条强制执行）

**列级权限**（谁有权写哪列）：

| 列 | 唯一写入者 | 说明 |
|---|---|---|
| 选定标题 / 选定简介 / 排产时间 / 备注 | **仅用户** | Agent 代码永不写（push/import 均 pop 保护） |
| Agent已领取 | 仅 poll 领取 | 勾选=领取动作的一部分，单次原子 PATCH |
| 状态 | 按转移矩阵（下） | 每个转移绑定唯一触发者 |

**状态转移矩阵**（每个箭头=唯一触发者，不在表内的转移=禁止）：

| 转移 | 触发者 | 触发动作 |
|---|---|---|
| 待产→待审核 | Agent | push（批量排产模式：素材预处理完成的标志，直推通道保留） |
| 待产→待预处理 | 用户 | 手动置（=下预处理工单，逐册模式） |
| 待预处理→待审核 | Agent | preprocess 领单→L1-L3 创作→push（自动翻状态+清「Agent预处理中」勾） |
| 待预处理→待产/弃用 | 用户 | 手动撤销工单（Agent 无此转移权） |
| 待审核→已审核 | 用户（审核裁决） | 手动置（Agent 无此转移权） |
| 已审核→已排产 | 用户置已审核即触发 | Notion 自动化规则1 |
| 已排产→已领取（生产中） | Agent 勾选领取 | ⚡规则2 置状态；poll 领取时也直写同值（原子勾选+置状态），双保险幂等不打架 |
| 已领取（生产中）→已交付 | Agent | deliver（提示词写入后） |
| 任意→弃用 | 仅人工 | 手动置（Agent 无权置，也无权从弃用改出） |

**行级筛查（push 遇到非待产行怎么办）**：

| 行现状 | push 行为 |
|---|---|
| 待产 | 全面更新 + 翻待审核 |
| 待审核 | 刷新素材（幂等，状态不动） |
| 已审核 / 已排产 / 已领取（生产中） | 只刷素材，状态不碰 |
| **已交付** | **整行跳过**（交付物最高保护；`--force` 才放行） |
| 弃用 | 跳过（Agent 无权复活） |

**deliver 准入**：仅 `已排产` / `已领取（生产中）` 可交付；已交付拒绝重复交付；待产/待审核未领料禁止交付。
**poll 退回**：领取时发现选定标题为空 → 退回待审核并显式告警（选定标题=人工审核完成的标志，未选定不进生产）。

## 二、Notion 页面自动化规则（用户在页面配一次）

数据库 ⚡ → New automation：
1. 触发「状态 设为 已审核」→ 动作设状态=已排产（已审核=用户审核裁决的手动状态）
2. 触发「Agent已领取 checked」→ 动作设状态=已领取（生产中）

（自动化规则只能页面建，API 建不了；poll 自带兜底：待审核+到期、已审核滞留、待产+到期、跳过预处理回流（生产态但备选列空）、待预处理待领/已领滞留，都会分别提示根因。）

## 三、全流程命令

```bash
# 0. 生成台账(仅首次/新批次): 产出CSV后导入, CSV即弃
python3 bin/gen_schedule.py ...
# 1. 导入台账(属性行, 断点续传: 已存在排产号自动跳过, 0.35s/行限速)——导入后CSV即弃, 产物不入仓
python3 bin/notion_kanban.py import <排产台账.csv>
# 2a. 预处理工单模式(逐册): 用户在Notion置「待预处理」=下工单 → 列单→领单(勾Agent预处理中防重)→主Agent直创(禁GPT/Gemini, 09-21拍板)→push(自动翻待审核+清勾)
python3 bin/notion_kanban.py preprocess --list
python3 bin/notion_kanban.py preprocess --claim
# 2b. 批量排产模式: 三件套md → 六段页面 + 备选列回填 + **状态待产→待审核(Agent置位,=预处理完成标志)**
#     md头部须有「创作模型: <主Agent模型名>」行(溯源必填; 禁标GPT/Gemini——09-21用户拍板废09-10旧红线); 双机约定: preprocess仅本机执行
#    push 只写 md 来源字段(核心词/链形/备选/旁白); 月/词型/绑定形态/画风等元数据单源=Notion属性栏, 无CSV参数
#    push 写路径闸门(全绿才落库): title_check+batch_check+binding_check+style_check+ending_check — 违规整批 exit=1
#    重推安全: 未交付页可安全重推(先append后归档); 已交付页(含生图提示词节)拒绝重建, 确认覆盖加 --force
python3 bin/notion_kanban.py push <三件套.md>
# 3. 每日领料: 筛[已排产+排产时间≤今日+未勾] → 自动勾选+置生产中+打印工单
python3 bin/notion_kanban.py poll [YYYY-MM-DD]
# 4. L4完成后交付: **完整L4标准文档**(plaintext引导语4段+【全局设计约定】+【主要场景锚点】+
#    每页4字段旁白/比例/页面类型/生图提示词×9 + 末尾1行) → 「生图提示词(定稿)」节 + 状态置已交付
#    deliver内置校验(铁律11/15+页数/比例/认知页等), 不合标准的裸提示词直接拒收
python3 bin/notion_kanban.py deliver B00X b00x_l4.txt
# 任意时刻: 台账状态计数
python3 bin/notion_kanban.py status
```

**单册页面六段结构**（push 生成，人与 Agent 共读）：H1 信息行 → 📖使用规则callout → 双语旁白table(序号|英文|中文) → L4工单 → 生图提示词(定稿=完整L4标准文档,交付后) → ✍️修改意见callout。

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
