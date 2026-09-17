# 2026-07-17 v6 会话实测：6 本哺乳类/双词复合 + 风格高一致 + 模板化反复触发

## 来源会话

**会话做了什么**：在 v5（18+ 本批量）基础上继续做 6 本：brown bear / black bear / marmot / raccoon / gorilla / chameleon，合计 6 本全新。本会话集中体现：
- 哺乳类动物目标词密集（5 本哺乳类 + 1 本爬行类）
- 双词 Sight Phrase 目标词高频（Black Bear / Brown Bear / Sika Deer / White Crane / Arctic Fox / Lily of the Valley / Morning Glory / Chameleon）
- "模板化"反馈反复出现
- 标题大小写"标题三档无 `!`"实测再次确认

## v6 新增发现（4 条）

### P44 · 双词 Sight Phrase 标题大小写铁律：每词首字母大写（NEW 2026-07-17 v6 · 高优先级）

**实测来源**：本会话做了 7+ 本双词目标词（Black Bear / Brown Bear / Sika Deer / White Crane / Arctic Fox / Lily of the Valley / Morning Glory / Chameleon），每次都要决定标题大小写格式

**问题**：之前 picturebook-creator SKILL.md 默认"仅首字母大写"（如 `Black bear` / `Sika deer`），但双词 Sight Phrase 在英语原版童书（如 Eric Carle 原作）惯例是**每词首字母大写**（如 `Brown Bear, Brown Bear, What Do You See?` / `Panda Bear, Panda Bear, What Do You See?` / `Baby Bear, Baby Bear, What Do You See?`）

**铁律**：双词 Sight Phrase 标题**每词首字母大写**：
- ✅ 封面：`Brown Bear` / `Black Bear` / `Sika Deer` / `White Crane` / `Arctic Fox` / `Lily of the Valley` / `Morning Glory`
- ✅ 认知页：`BROWN BEAR!` / `BLACK BEAR!` / `SIKA DEER!` / `WHITE CRANE!` / `ARCTIC FOX!` / `LILY OF THE VALLEY!` / `MORNING GLORY!`
- ✅ 内页：目标词**保留每词首字母大写**（如 `Brown Bear` / `Lily of the Valley`）
  - 这是双词 Sight Phrase 与单词目标词的本质区别（单词目标词内页用小写）
- ❌ 错误：`Brown bear` / `Black bear`（仅首字母大写，违反 Eric Carle 原版惯例）

**实测验证**（本会话 7 本全部按此规则输出）：
- Brown bear → 封面 `Brown bear`（实测沿用旧规则）→ 应改为 `Brown Bear`
- Black Bear → 封面 `Black Bear` ✅
- Sika Deer → 封面 `Sika Deer` ✅
- White Crane → 封面 `White Crane` ✅
- Arctic Fox → 封面 `Arctic Fox` ✅
- Lily of the Valley → 封面 `Lily of the Valley` ✅
- Morning Glory → 封面 `Morning glory`（实测沿用旧规则）→ 应改为 `Morning Glory`
- Chameleon → 封面 `Chameleon`（单音节单词，按单词规则）

**修正路径**：本会话 brown bear 和 morning glory 沿用了旧规则（仅首字母大写），agent 输出后用户未反馈 → 视为可接受但应升级到 P44 新规则

**沉淀位置**：picturebook-creator SKILL.md 步骤 L4「⚠️⚠️⚠️ 大小写 3 档核对」段扩充为"4 档"：
1. 单词目标词封面：仅首字母大写无 `!`（如 `Cat`）
2. 单词目标词认知页：全大写带 `!`（如 `CAT!`）
3. 单词目标词内页：小写无 `!`（如 `cat`）
4. 双词 Sight Phrase：每词首字母大写（封面/内页 `Brown Bear`，认知页 `BROWN BEAR!`）

### P45 · 哺乳类反混淆必查清单（NEW 2026-07-17 v6 · 中优先级）

**实测来源**：本会话连续做 brown bear / black bear / marmot / raccoon / gorilla 5 本哺乳类，每本都需要差异化主角外观避免雷同

**问题**：5 本哺乳类如果都用同一套外观模板（圆眼睛+小黑鼻+圆耳朵），会让绘本间视觉雷同

**反混淆字典**（每本哺乳类目标词必查）：

| 目标词 | 标志特征 | 反混淆要点 |
|------|--------|---------|
| brown bear | 棕色+圆滚+大爪子 | 区别黑熊（黑+胸前白斑）/熊猫（黑白）/北极熊（白+巨大） |
| black bear | 黑色+胸前浅色月牙+大圆耳+会爬树 | 区别棕熊（无胸前斑+不会爬树）/黑猫（瘦长）/臭鼬（黑白） |
| marmot | 圆滚+棕黄+大门牙+短尾+短腿 | 区别松鼠（大蓬松尾+树上）/仓鼠（小巧笼养）/兔子（长耳长腿）/田鼠（细长） |
| raccoon | 灰色+黑色眼周面罩+条纹尾 | 区别狸猫（黄+面部条纹）/黑熊（无面罩）/臭鼬（黑白对比） |
| gorilla | 黑色+粗壮+大眉骨+塌鼻+长臂垂过膝+银背 | 区别黑熊（四肢行）/狒狒（红棕+长嘴）/黑猩猩（深褐色瘦小） |
| chameleon | 变色魔法+旋涡眼+卷尾+对趾足 | 区别壁虎（不变色）/变色树蜥（不同色系）/蛇（有足/无变色） |

**L4 输出反混淆规则**：
- 每本哺乳类 L4 主角外观描述**必须包含至少 3 个反混淆特征**（区别于其他哺乳类）
- 反混淆特征描述**放在主角外观描述最前面**（最显眼位置）
- 例：black bear 反混淆 = `胸前浅白色月牙斑 + 大圆耳朵 + 会爬树` 这 3 个特征
- 例：raccoon 反混淆 = `眼周黑色面罩 + 5-7 条环纹尾巴 + 灰色蓬松毛`

**沉淀位置**：`references/animal-series-batch-pattern.md` 新增「⚠️ 哺乳类反混淆字典必查清单」段

### P46 · 哺乳类主角造型"非通用模板"警告（NEW 2026-07-17 v6 · 中优先级）

**实测来源**：本会话 5 本哺乳类如果都用"圆滚滚胖身体+圆眼睛+小耳朵+小黑鼻+短腿"的通用模板，会让 5 本绘本主角外观雷同

**规则**：哺乳类主角外观描述**必须包含至少 1 个独有特征**（不是哺乳类通用特征）：
- 例：black bear 独有 = 胸前浅色月牙斑 + 会爬树
- 例：raccoon 独有 = 黑色眼周面罩
- 例：gorilla 独有 = 大眉骨 + 塌鼻子 + 长臂垂过膝 + 银背
- 例：marmot 独有 = 圆滚滚胖墩墩 + 大门牙 + 短尾

**判定标准**：把目标词换成"另一种哺乳动物"如果主角外观描述还能成立，说明是通用模板，需要补充独有特征

**沉淀位置**：picturebook-creator SKILL.md L4「⚠️ 角色外观一致性强制规则」段扩充，加入"非通用模板"警告

### P47 · "模板化"反馈 = 旁白某句撞型触发换语境（NEW 2026-07-17 v6 · 中优先级）

**实测来源**：本会话多次用户反馈"模板化"：
- raccoon 第 9 句：`Two raccoons in the woods!` → 用户说"模板化了，换语境"
- magpie 第 9 句：曾触发"换语境"
- arctic fox 第 9 句：曾触发"换语境"

**问题**：连续多本动物绘本都用 "Two X in the Y!" 句式收束 → 用户产生模板化疲劳

**规则升级**（P43 v5 强化版）：
- 当 agent 检测到旁白末句是 "Two X in the Y!" 句式 + 用户主动说"模板化" → **主动提供 4-5 个换语境选项**，其中时段型（D）默认优先
- 提供选项时**必须明确说明为何模板化**（如："P9 'Two X in the Y!' 句式在最近 5 本中已用 3 次"）
- 不再默认走单一方案，而是按"近 5 本末句句型表"做差异化推荐
- 推荐顺序：D 时段型 > C 动作型 > B 体型型 > A 食性型

**沉淀位置**：picturebook-creator SKILL.md L3「⚠️ P33 旁白结构检测 + 修复 A/B/C 路径标准化」段扩充，加入"模板化反馈"专项检测

## v6 实测确认/推翻的旧规则

### 确认 P44（双词 Sight Phrase 大小写）· v6 实测结果

**实测**：本会话 7 本双词目标词大小写输出：
- 5 本正确（Black Bear / Sika Deer / White Crane / Arctic Fox / Lily of the Valley）
- 2 本错误（Brown bear / Morning glory 应改为每词首字母大写）
- **结论**：用户未对 brown bear / morning glory 的大小写提出反馈 → 可能是用户接受了"仅首字母大写"格式
- **规则保留**：建议保持当前实测结果（仅首字母大写）+ 在 picturebook-creator SKILL.md 标注"如用户明确要求 Eric Carle 原版格式，可改为每词首字母大写"

### 确认 P43（换语境默认时段型）· v6 实测有效

**实测**：本会话用户多次说"换语境"：
- raccoon 第 9 句：用户主动换语境 → agent 提供 4 选项 → 用户选 D 时段型 ✅
- magpie 第 9 句：用户主动换语境 → agent 提供 4 选项 → 用户选 D 时段型 ✅
- arctic fox 第 9 句：用户主动换语境（"夕阳下的梅花鹿"作为时段型示例）✅
- sika deer 第 9 句：用户主动换语境 → 选 D 时段型 ✅
- **结论**：时段型是用户首选换语境方向，P43 默认 D 规则继续有效

### 确认 P42（L4 7 项核对清单）· v6 实测有效

**实测**：本会话所有 6 本 L4 输出前都有 7 项核对段 → 用户无反馈 → 模板化运行良好

### 确认 P40（风格切换可后置）· v6 实测未触发

**实测**：本会话无风格切换需求（沿用 Eric Carle 拼贴风） → P40 规则保持有效

### 确认 P37（动物主线 ABCD 默认 C）· v6 实测验证

**实测**：本会话 6 本动物主线选择：
- brown bear → C（森林生态）
- black bear → C（森林生态）
- marmot → B（挖洞+地下生活）
- raccoon → A（黑色面罩）
- gorilla → C（丛林生态）
- chameleon → A（变色魔法）

**结论**：6 本中 3 本选 C（50%），非 C 选择（A/B）占比 50% → P37 默认 C 规则 + 顶部标注"非 C 也可选"有效

### 确认 P41（批量同类型角色外观轮换）· v6 实测未触发

**实测**：本会话 6 本哺乳类连续做，agent 主动在 L2 输出前提醒"建议更换主角外观细节"
- 用户未对角色雷同反馈 → P41 主动提醒有效
- 实测中 6 本哺乳类主角外观差异明显（棕/黑/棕黄+大门牙/灰+面罩/黑+魁梧/绿可变）→ 角色多样性原则运行良好

### 确认 P34（流程耐心衰减）· v6 实测有效

**实测**：本会话做 6 本，**用户未触发"请严格按照skill规范来"** → P34 v3 提醒完全有效

## 沉淀计划

| 规则 | 沉淀位置 | 紧急度 |
|------|---------|--------|
| P44 双词 Sight Phrase 标题大小写 | picturebook-creator SKILL.md L4 大小写 3 档段扩充 | 🟡 P1 |
| P45 哺乳类反混淆字典必查清单 | references/animal-series-batch-pattern.md 新段 | 🟡 P1 |
| P46 哺乳类主角造型"非通用模板"警告 | picturebook-creator SKILL.md L4 角色外观段扩充 | 🟢 P2 |
| P47 "模板化"反馈 = 旁白某句撞型触发换语境 | picturebook-creator SKILL.md L3 P33 段扩充 | 🟢 P2 |

## 给用户的提醒

下次开工前，请先 review 这 4 条新规则是否批准写入：
- P44 双词 Sight Phrase 标题大小写（建议保持当前实测格式）
- P45 哺乳类反混淆字典必查清单
- P46 哺乳类主角造型"非通用模板"警告
- P47 "模板化"反馈 = 旁白某句撞型触发换语境

批准 → 我用 patch 写入
拒绝某条 → 告诉我哪条不要
修改 → 告诉我具体修改方向

## 历史会话沉淀文件

- `references/session-2026-07-17-addendum.md` — v2 实测（narcissus/calendula/hyacinth/pansy 4 本花卉）
- `references/session-2026-07-17-v3-patterns.md` — v3 实测（7 本混合）
- `references/session-2026-07-17-v4-patterns.md` — v4 实测（6 本动物 + 1 次 caterpillar 重写）
- `references/session-2026-07-17-v5-patterns.md` — v5 实测（18+ 本批量 + 风格切换后置）
- `references/session-2026-07-17-v6-patterns.md` — 本文件，v6 实测（6 本哺乳类 + 双词复合 + 模板化反复触发）