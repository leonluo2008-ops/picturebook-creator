---
name: flower-series-batch-pattern
description: |
  花卉领读绘本批量模式参考（2026-07-10/11 17+ 本实测）。覆盖花朵（rose/tulip/peony/violet/orchid/lily/carnation/daisy/lilac/hydrangea/iris/lotus/camellia/lavender/gardenia/aster/jasmine）的独有特征、结尾类型轮换表、反混淆清单、科学准确性铁律、主角多样性管理、文化定位扩展。
  触发词：花卉、花、花朵、flower、rose、tulip、peony、violet、orchid、lily、carnation、daisy/lilac/hydrangea/iris/lotus/camellia/lavender/gardenia/aster/jasmine/sunflower/narcissus/magnolia/chrysanthemum/批量花朵、连续做花、绘本花朵。
license: Apache-2-2
metadata:
  hermes:
    tags: [picturebook-creator, flower-series, batch-pattern, ending-types, science-accuracy]
    parent_skill: picturebook-creator
---

# 花卉领读系列批量模式 — picturebook-creator 的下钻参考

> 这个 skill 是 `picturebook-creator` 的子参考，专门沉淀花卉主题领读绘本的批量创作经验。
> 完整 9 本花卉实测数据 + 多个新教训沉淀于此，未来花朵制作前**必读**。

## 为什么有这个 skill

2026-07-10 + 07-11 单日 17+ 本花卉连测（rose/tulip/peony/violet/orchid/lily/carnation/daisy/lilac + hydrangea/iris/lotus/camellia/lavender/gardenia/aster/jasmine），触发了多个 picturebook-creator 主 SKILL.md 没覆盖的问题：

1. **"模板化"标签在花卉类更易触发**（peony 实测）— 4 维度天然共享（颜色+形态+触感+嗅觉），多本书后必撞
2. **花卉结尾类型更多元**（17 本已用 17+ 种），未来必须避开已用类型
3. **花卉比水果/蔬菜更易混入错误生长习性**（orchid 长树上被用户当场纠正）— 主流形态 vs 野生形态一定要选主流
4. **花卉文化定位丰富**（母亲节/情人节/花语），可差异化结尾同时教文化
5. **P3+P7+P8 三色变体是花卉类最高频"模板化"陷阱** — 连续 3 页都是"A [adj] flower"色变体必被用户嫌
6. **"换语境/重写组织语言/末句换语境"是花卉高频修正指令** — 用户偏简洁、自然、原句整体替换

## 使用方式

读完 picturebook-creator 主 SKILL.md 后，**花卉类 L3 编写前必须再读本 skill** 的：
1. `## 系列信息` 表（确认本花是否已做，避免重复）
2. `## ⚠️ 花卉结尾类型轮换表`（必扫避开已用）
3. `## ⚠️ 花卉科学准确性铁律`（避免 orchid 类错误）
4. `## ⚠️ 花卉反混淆清单`（L4 生图提示词必带排除性描述）

## 关键执行规则

### 1. 默认 2 维度，避免"模板化"
- L3 默认输出 **2 维度为主**（颜色 + 形态）
- ≥ 3 维度同时出现大概率触发"模板化"
- 例外：嗅觉可保留 1 句（花香是花卉独有感知点）

### 1.5. ⚠️ P3+P7+P8 三色变体是花卉类最高频模板化陷阱（2026-07-11 多本实测）

> 用户在 peony/lily/carnation/gardenia 等 5+ 本中连续触发此陷阱。
>
> **反模式**：P3 "A pink [flower]" + P7 "A white [flower]" + P8 "A purple [flower]" — 三页都是"A [color] [flower]"色变体
>
> **优化方案**（任选其一）：
> 1. 把 P7 或 P8 换成"动作维度"（如 watering、counting、sending 等动态）
> 2. 把 P8 改成"该花独特用途"（如 jasmine tea、lavender sachet、carnation for mom）
> 3. 把三色变体集中到一页，避免分散在三页（P3 一句带过、P4/P5 做其他维度）
>
> **判别准则**：如果 L3 看起来可以套任何花只换颜色词 = 模板化。

### 2. 结尾类型必须查表避开
每本花的 L3 输出前，**先查本 skill 的"花卉结尾类型轮换表"**，避开 17+ 种已用类型，从"候选结尾类型"列表选新类型。

### 3. 科学准确性优先于句式优美
- orchid = 盆栽（非"长在树上"）— 用户当场纠正
- lily = 茎立花圃（非喇叭花圃）
- jasmine = 5 瓣星形小花 3 朵一簇（非大花单朵）
- gardenia = 多层螺旋大花（非规整层叠，类似 camellia 但旋涡状）
- 其他见"花卉科学准确性铁律"完整对照表

### 4. 反混淆描述写进 L4 提示词
所有花卉 L4 生图提示词的【全局设计约定】必须包含"花卉外观约定"字段，列出该花的独有特征 + 与最相似花的区别。

### 5. 主角多样性管理
本花卉系列已用 **17+ 主角**（小刺猬/小瓢虫/小蝴蝶/小蜗牛/小鹦鹉/小鹿/小女孩/小蜜蜂/小蜻蜓/小青蛙/小鸟/小夜莺/小金鱼/**小白兔**(azalea)/**小松鼠**(chrysanthemum)/**小猫头鹰**(zinnia)/**小乌龟**(gerbera)），新花应从剩余候选选。

### 6. ⚠️ "换语境/重写/换末句"指令执行规则（2026-07-11 花卉实测高频模式）

> 花卉连测中用户反复发短指令：
> - "第 X 句换语境" → **英文 + 中文都要换**，整句替换为新语境
> - "第 X 句重写组织语言" → **整句重组**，保持目标词出现
> - "最后一句换语境" → **末句必须重写**，避开已用结尾类型
> - "把 P3 换成这是 XX" → **改中文（保留英文不动）**，强化认字功能
> - "旁白有些模板化了，请你从颜色形态特征来写" → **重写整篇旁白**，改用颜色+形态 2 维度主导，跳出连续静态特征描述
>
> **执行原则**：直接执行不反问；改完重出完整表格让用户确认；不质疑、不解释。

### 7. ⚠️ ⚠️"从颜色形态来写"维度重写铁律（2026-07-11 lavender 实测明示）

> **用户原话**（lavender 会话）："旁白有些模板化了，请你从颜色形态特征来写"
>
> **触发场景**：用户对花卉旁白直接明示"模板化" + 给出维度要求 → 旁白已陷入连续静态特征描述（颜色/形态/触感/嗅觉/sense 多页堆叠），需要**整体重写为以"颜色+形态"为主导的简化版**
>
> **错误响应模式**（禁止）：
> 1. ❌ 反问"你想要哪种语境？" → 用户已明示
> 2. ❌ 改 1-2 句就交付 → 需整篇重写
> 3. ❌ 把中文改下交付 → 用户要"换语境" = 英文+中文都改
> 4. ❌ 输出未自检的版本 → 必须附自检表（双语同现/标点对应/形态/数量/避撞型）
>
> **正确响应模式**：
> 1. ✅ 立即重写整篇旁白 → 用颜色 + 形态两维度重新组织
> 2. ✅ 附带自检表 → 确认双语同现 + 标点 + 末尾绑定 + 目标词≥8 + 维度分布
> 3. ✅ 末句改结尾型 → 避开已用结尾清单（参考 `references/flower-series-data.md` 21 本轮换表）
> 4. ✅ 同时考虑新增维度（如阳光/切口/季节/其他用途）以避开静态堆叠
> 5. ✅ 输出"按 v[N] 旁白修订"段，记录修改内容

## 触发本 skill 的场景

收到"目标单词: X, 目标年龄: 3-6, 画面风格: S06 Eric Carle 拼贴风"格式输入，其中：
- 单词是花卉（中文释义包含"花/菊/兰/梅/莲/牡丹/玫瑰/百合/菀/茉莉/茶/鸢/薰/绣/荷"等）
- 单词是英文花卉学名：

| 已做花卉（必扫避开已用结尾） | 未做花卉（候选清单） |
|--------------------------|---------------------|
| rose/tulip/peony/violet/orchid/lily/carnation/daisy/lilac/hydrangea/iris/lotus/camellia/lavender/gardenia/aster/jasmine/azalea/chrysanthemum/zinnia/gerbera/**water lily**/**dahlia**/**marigold**/**calendula**/**hyacinth**（27 本 2026-07-16）| sunflower/daffodil/**narcissus**（水仙）/magnolia/heliconia/bird of paradise/foxglove/bluebell/anemone/hyacinth（注：已做，剔除）/aster（注：同名词族重复慎选）/sunflower（注：同 sunflower 多本易混）|

> **2026-07-16 单日新增 3 本**：calendula（金盏花·橙黄少层+药用）/hyacinth（风信子·紫柱状+春天开·认知页无感叹号特例）/narcissus（水仙·L3 已确认旁白，本会话结束前未完成 L4）。本表新增 calendula + hyacinth 已做，narcissus 从候选移出。详细 27 本完整数据（主角/独有特征/文化定位/结尾类型）见 `references/flower-series-data.md`。

### ⚠️ 花卉系列无动物原则（2026-07-12 用户指令·Dahlia 起强制）

用户在 **Dahlia 第一版** 明确否决了所有动物出镜（包括上一轮用过的小狐狸），要求"**从花的特征、颜色等来写**"。

**执行规则**：
- 所有后续花卉绘本 L1 默认不推荐动物主角
- 纯以花本身为绝对主角
- L2 设计直接走"花的独有特征维度"（形态/颜色/动态/细节/场景/用途/集合/拟人）
- 如需破例必须用户明确指令

**关联影响**：
- 主角轮换表（rule 5）暂不强制（新本不再需要主角）
- 反拟人型结尾风险上升（rule 7 强化）
- 末句必须避开"花瓣挥手打招呼"型（用户已否决）→ 改为"用途型"或"时序场景型"

### ⚠️ 拟人型结尾风险（Dahlia 第二版被否教训）

**触发场景**：Dahlia 第一次用"拟人型·花朵挥瓣打招呼"被用户否决（用户原话"上一版的旁白我不满意"），触发连续换语境指令。

**结尾型优先级调整**：
- ✅ 用途型（最高，独有用途 = 100% 差异化）— **calendula 泡茶**
- ✅ 时序场景型（次高，避开已有时序）— **dahlia 夕阳**
- ✅ 对比型（中等）
- ✅ 数字数型（中低）
- ⚠️ 拟人型（最低，慎用）— **Dahlia "花瓣挥手"被否**

**花卉独有用途型结尾候选库**（用途型比拟人型安全）：
- calendula → "Calendula for tea!"（泡茶）
- rose → "Rose for perfume!"（香水）
- daisy → "I count daisy petals!"（数花瓣）
- sunflower → "Sunflower seeds!"（葵花籽）
- lavender → "Lavender sachet!"（香包）
- jasmine → "Jasmine tea!"（茉莉花茶）

**判别准则**：本花有独有用途 → 优先用途型结尾；无独有用途 → 走时序场景型。

### ⚠️ Calendula vs Marigold 翻译陷阱（2026-07-12 Calendula 实测）

**问题**：calendula 和 marigold 在中文里都被译为"金盏花"或"万寿菊"，但其实是**不同物种**——AI 生图极易混淆。

**核心区别**（必带 L4 全局约定）：

| 维度 | calendula 金盏花 | marigold 万寿菊 |
|------|----------------|----------------|
| 花瓣 | 平整/略锯齿，**少层**（单层/双层）| 密集皱褶，**多层**波浪层叠 |
| 花头 | 中等小（5-10cm）| 较大（10-15cm）|
| 颜色 | 黄橙双色（+少量奶油白/桃粉）| 多色（黄/橙/红/金棕）|
| 用途 | 药用/可食用（tea/oil/护肤）| 仅观赏 |
| 花心 | 橙黄管状小花密集成圆盘 | 圆形突起（部分被皱褶包住）|

**L4 全局约定必带段**（防止即梦把 calendula 画成 marigold）：
```
⚠️ 这是 calendula 金盏花，不是 marigold 万寿菊；calendula = 花瓣平整少层 + 花朵相对小 + 黄色/橙色 + 药用可食用；marigold = 花瓣密集皱褶层叠 + 花朵较大 + 多色 + 仅观赏。
```

**反混淆承载页面分配**：
- vs marigold：P2 形态（花瓣平整）+ P3 大小（5-10cm）+ P8 用途（泡茶杯）
- vs chrysanthemum：P2 形态 + P3 大小
- vs sunflower：P3 大小 + P6 颜色（黄橙非纯黄）
- vs dahlia：P2 形态（平整 vs 尖瓣）+ P3 大小（5-10cm vs 30cm）

### ⚠️ Dahlia 维度结构参考（2026-07-12 实测优化版）

Dahlia 在本会话经过 2 版迭代定稿，无动物 + 8 页 7 维度结构值得后续花卉参考：

| 页 | 维度 | 旁白 |
|---|------|------|
| 封面 | 标题 + 主图 | Dahlia大丽花 |
| P1 | 认知 | DAHLIA! |
| P2 | 形态·红 | A red dahlia. |
| P3 | 大小对比 | A big dahlia.（用茶杯对比，**不用小手**避免重复） |
| P4 | 形状 | Dahlias like fireworks.（**烟花比喻**直接呈现尖瓣放射） |
| P5 | 动态·水珠 | Drops on the dahlia.（**雨后水珠**，无动物也能呈现动态） |
| P6 | 颜色·紫 | A purple dahlia. |
| P7 | 细节·花心 | A yellow center.（极近景仰视） |
| P8 | 时序场景 | Dahlias in the sunset.（**夕阳收束**，避开拟人型） |

**复用要点**：
- P3 对比物避免重复（dahlia 用茶杯替代小手）
- P5 动态用自然现象（水珠/风）替代动物互动
- 末句避开花瓣挥手拟人型 → 用时序场景（夕阳/早中晚/季节）
- 反混淆由专属页面承载（vs marigold → P2+P3+P8）

→ 加载本 skill + picturebook-creator，然后开始 L1→L2→L3→L4 流程。

## 详细参考

完整数据表 + 反混淆清单 + 结尾轮换表 + 主角轮换记录，请读本 skill 的：
- `SKILL.md` 主文件（本文件已含核心规则 + 系列信息表）
