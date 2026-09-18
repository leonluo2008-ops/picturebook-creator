# 英语分级词库 · 使用说明

> 用途：把分级阅读词汇逐词做成领读绘本的**生产总表**。每词一册（8-12 句旁白，全套规则约束），本目录是排产清单与状态台账。

## 数据文件

| 文件 | 内容 | 词数 | 来源 |
|---|---|---|---|
| `dolch.csv` | Dolch 220 服务词（preprimer/primer/g1/g2/g3）+ 95 名词（noun） | 315 | kuraplan.com 分级清单 + readwritethink.org（IRA/NCTE）完整 PDF |
| `fry_1-300.csv` | Fry 前 300 高频词（带频率排名 fry_rank） | 300 | sightwords.com（含勘误：第5百 am→bread） |

- 列：`word,level,cn`（fry 表为 `word,fry_rank,cn`）；`cn` 为教学参考释义
- 两表重叠 193 词（sight words 本质同源）；**去重后总词量 = 422**
- 源差异注：Dolch g1 的 going/giving 两源不一，本库取 going（kuraplan 版）

## 与分级读物体系的对标（调研结论）

- Dolch Pre-Primer + Primer ≈ 红火箭 Early Level / 海尼曼 GK / RAZ aa-C / 牛津树 1-3 的词汇域
- Fry 1-100 ≈ 美国幼儿园-K1 核心高频；1-300 覆盖儿童读物品约 2/3 词汇
- 我们的目标读者 3-6 岁 → **主战线 = Dolch preprimer+primer+noun（187 词，全部具象可绘本化）+ Fry 高频补充**

## 排产建议（待拍板）

1. **第一批（名词册 × 95）**：Dolch nouns 全部具象（apple/dog/rain/sun…），画面可指认，是我们已验证最强词型
2. **第二批（动作/形容词册 × ~50）**：jump/run/big/little/play/eat/sleep… 具象动词与形容词
3. **第三批（功能词册 × ~42）**：the/a/and/is… 纯功能词**不适合单册成书**，建议采用「载体册」策略——每册以一个具象词为核心、功能词作支持词浸泡（如《the park》教 the），或在书名/短语中自然绑定（good night 模式）
4. 难词处理：upon/shall（Dolch 官方也承认过时）、Indian/Santa Claus（文化词，可用可换）→ 标记 skip 或替换

## 每册生产要求

全套已定版规则约束（见 references/narration-quality-anchor.md）：
五站链（功能检查表）· 禁介绍站 · 三许可（内容词≤10）· 绑定形态唯一性 · 中文核心词同现率（盲听强化）· 中英对齐 · 问后必有真答案 · 结束感·落幕句 · 链形每书自定禁跨书复用（批量生产时用检测器+链形查重防模板化）

## 状态

- [ ] 词库建立（dolch 315 + fry 300，已核数）
- [ ] 排产清单确认（用户拍板批次顺序）
- [ ] 第一册生产
