# 旁白质量修复计划（2026-09-18 · 标准流程版）

> 依据：用户拍板 ①旁白糟糕，以小羊上山调研为准修复 ②要风格不要模板 ③启发优先、少而精、该删的删 ④按标准流程办事。
> 本仓标准更新流程（update-todo skill 定义）：实测 → 沉淀到清单 → **用户批准** → patch 写入对应章节。
> 状态标记：[DONE] 已完成并提交 / [REVIEW] 子 agent 审查中 / [PENDING-APPROVAL] 待用户批准 / [CONFLICT] 未决矛盾。

## 已完成（2 commits on fix/narration-quality）

| Commit | 内容 |
|---|---|
| e4d1365 | v5.6.0 旁白质感锚定：narration-quality-anchor.md（小羊上山四条质感标准+反模板化总纲+启发优先原则）+ vividness 上位声明/§十一质感四问/§八B骨架型叠词豁免/字数裁决补行 + story-description 范例形状警告+病灶速查补行 + SKILL.md v5.6.0 置顶块 + L2 推进链注 + 诊断脚本 bin/narration_quality_check.py（标杆回归通过） |
| 906e82b | 历史档案归档：9 文件（darwin 案例×6/批次摘要×2/会话信号×1）→ docs/archive/；vividness 裁决表收编自持；scene-place 悬空引用修复；启发优先原则落锚文件 |

## 审查中 [REVIEW]

- deleg_b84d1d0c：对 e4d1365 的对抗性 code_review（攻击面：反模板化的自指矛盾/存量规则冲突/脚本逻辑/覆盖缺口）。结果回来后：致命→必修，严重→逐条回应修订，中等→记录酌情。

## 待用户批准 [PENDING-APPROVAL]

### D1. SKILL.md 顶部四代版本块（v5.6.0/v5.5.0/v5.5.1/v5.0.0 堆叠）收敛
现状：置顶区 58 行，4 个历史版本块并存，正文与 references 大量重复（v5.5.0 块 19 行 vs vividness 文件 190 行）。按「启发优先/该删的删」原则建议收敛为：**单一「现行铁律索引」块**（每个铁律域 1-2 行指针+一句话核心）+ 版本沿革移到文末小节。
- 收益：主文件信噪比提升，LLM 首屏即见全貌；重复内容单一事实源化
- 风险：极低（内容全部在 references 自持，置顶块本就是指针+摘要）

### D2. update-todo 积压规则（P28-P66）的处置 —— ✅ 已解决（2026-09-18 用户判定过期）
用户确认 update-todo 已过期（最后更新 07-21，后被 18 个提交演进取代：P61→末句备选制定版、v11 积压 7 条卫星已承接）。已整体归档 `docs/archive/picturebook-creator-update-todo/`（commit dc4cda6），全仓引用修复。「向主 SKILL.md 搬运积压」方案作废。

### D3. 过检样例库（启发优先的另一半）
现状：现有范例散落在 22 个批次模式文件（fruit/animal/career...各含大量 ❌ 禁令对照）。按「少而精」原则，建议新建 `references/exemplars.md`——每类目精选 1 本「定稿旁白全文」（只放好样本，不放禁令），作为 L3 创作时的小样本激发源；批次文件降级为「反混淆字典+素材库」查询用。
- 该项工作量较大（需从会话史/批次文件中挑选真实过检旁白），可分批做，先从最高频类目（fruit/animal）开始。

## 未决矛盾 [CONFLICT]

### C1. 感叹号三档规则（P23 v2 vs v3）
- v2（2026-07-17）：封面+认知页都不带 `!`
- v3（同日更晚，7 本实测）：「v2 改错了方向」→ 应回退 v1「封面不带、认知页带、内页不带」
- update-todo 自己标注「⚠️ P23 v2 需要二次审视」；主 SKILL.md/references 现行文本以哪版为准未闭环
- 建议：以 v3 实测口径定版（7 本 > 2 本证据量），patch 修正所有相关文件行——**待用户确认后执行**

### C2. P57 悬空计划
「quantity-comparative-batch-pattern.md 未落地无此文件」——若后续做 more/fewer 类词需先建该文件。仅记录，不阻塞。

## 执行顺序（批准后）

1. code_review 结果处理（REVIEW→修复或放行）
2. D1 置顶块收敛（半小时级，单一 commit）
3. C1 感叹号定版 patch
4. D2 卫星索引节 + update-todo 标记
5. D3 样例库分批（可选，按需）
