# 2026-07-17 会话信号记录 v1.1

## v1.1 新增信号（本会话触发）

### 信号 7：「换一种表达方式」第三类修改指令
- 触发：Black Bear 用户原话"第 3 句换一种表达方式，第 7 句换语境"
- 识别："换一种表达方式" = "换中文 + 但不给具体文本"，介于改中文和换语境之间
- 处理：只改中文，英文不变；agent 自行设计新中文（给 2-4 备选）
- v1.0 没识别这一类，导致 v1.1 patch

### 信号 8：「算了/不换了」终止信号
- 触发：Black Bear 用户原话"算了，不改第9句了"
- 之前：用户看了 A/B/C/D 选项后改主意 → 不再追问，立即跳过继续
- v1.0 协议没明确这种终止信号怎么处理，agent 会卡住等用户回复

### 信号 9：风格切换可发生在 L4 输出前
- 触发：Ostrich 用户在 L3 完全确认 + 选了"2/1"标题编号后，才发新消息切换风格
- v1.0 假设风格切换发生在 L3 之前，但实测可以发生在 L4 即将输出前
- 处理：重新输出 L4 时只改风格锚点（Eric Carle → 蜡笔手绘的笔触描述），旁白+结构全部保留

### 信号 10：旁白 9 行无结尾互动页是用户偏好
- 触发：Busy / Morning Glory / Pigeon / Chameleon（4+ 本）用户主动删除结尾互动页
- 每次都选 A（9 行 = 9 张图，无结尾互动页）
- v1.0 把结尾互动页作为铁律，v1.1 改为软规则（默认含，但用户主动删则接受）

---

## v1.0 已记录信号（继续有效）

### 信号 1：流程跳步（最高优先级）
- 用户原话："请严格按照skill规范来"
- 触发场景：lily of the valley 绘本，agent 一次性输出 L1+L2+L3+L4

### 信号 2："确认"词歧义（最高频）
- 触发次数：5+ 次（Shell/Dragonfly/Swan/Crow/Woodpecker/Caterpillar/Seagull/Magpie/Pigeon/Chameleon 等多次）

### 信号 3：主线 A/B/C/D 必问场景
- 全本 v1.1 新增：brown bear / black bear / marmot / raccoon / gorilla / sika deer / Arctic fox / chameleon / ostrich / cheetah

### 信号 4：风格中途切换
- 触发：woodpecker 用户从 Eric Carle 拼贴风切到蜡笔手绘童趣风
- v1.1 新增：ostrich 在 L4 输出前才切换

### 信号 5：目标词安全预检
- 触发：crow 乌鸦

### 信号 6：修改指令分类型（v1.1 升级为 3 类）
- 6 类 → v1.1 改为 3 类：改中文 / 换一种表达方式 / 换语境
- 新增"算了"终止信号

---

## 本次会话 30+ 本绘本批量产出

| # | 目标词 | 主线选择 | 风格 | 状态 |
|---|--------|---------|------|------|
| 1 | apricot blossom | - | Eric Carle S06 | L1→L4 + 加页 1 次 |
| 2 | lily of the valley | - | Eric Carle S06 | L1→L4 |
| 3 | shell | - | Eric Carle S06 | L1→L4 (用户去第10句) |
| 4 | ladybug | 动物路径 B | Eric Carle S06 | L1→L4 |
| 5 | dragonfly | D=颜色鲜艳 | Eric Carle S06 | L1→L4 |
| 6 | seagull | C=海边生态 | Eric Carle S06 | L1→L4 |
| 7 | magpie | D=中国文化 | Eric Carle S06 | L1→L4 |
| 8 | caterpillar | A=致敬原作 | Eric Carle S06 | L1→L4 + 重做升级 |
| 9 | white crane | C=湿地生态 | Eric Carle S06 | L1→L4 |
| 10 | swan | B=水上滑行 | Eric Carle S06 | L1→L4 |
| 11 | crow | C=坚持原词 | Eric Carle S06 | L1→L4 |
| 12 | pigeon | C=城市生态 | Eric Carle S06 | L1→L4 |
| 13 | woodpecker | C=森林生态 | 蜡笔手绘童趣风 | L1→L4 |
| 14 | busy | - | Eric Carle S06 | L1→L4 (用户去结尾页) |
| 15 | Morning Glory | - | Eric Carle S06 | L1→L4 (用户去结尾页) |
| 16 | brown bear | C=森林生态 | Eric Carle S06 | L1→L4 |
| 17 | cheetah | C=草原生态 | Eric Carle S06 | L1→L4 |
| 18 | pigeon (二次) | C=城市生态 | Eric Carle S06 | L1→L4 (用户去结尾页) |
| 19 | Black Bear | C=森林生态 | Eric Carle S06 | L1→L4 |
| 20 | marmot | B=挖洞+地下 | Eric Carle S06 | L1→L4 |
| 21 | raccoon | A=黑色面罩 | Eric Carle S06 | L1→L4 |
| 22 | gorilla | C=丛林生态 | Eric Carle S06 | L1→L4 |
| 23 | chameleon | A=变色魔法 | Eric Carle S06 | L1→L4 |
| 24 | ostrich | C=草原生态 | 蜡笔手绘童趣风 (L4前切换) | L1→L4 |
| 25 | Egret | C=湿地生态 | 蜡笔手绘童趣风 | L1→L2 |
| 26 | chameleon (二次) | A=变色魔法 | Eric Carle S06 | 用户给完整旁白表，跳 L1-L3 |

---

## v1.1 patch 决策记录

| 项 | v1.0 处理 | v1.1 处理 | 触发原因 |
|----|----------|----------|----------|
| 改中文 vs 换语境 | 二分 | 三分（加"换一种表达方式"） | Black Bear 用户混合用 |
| "算了/不换了" | 没明确 | 明确保留原句立即推进 | Black Bear "算了不改了" |
| 风格切换时机 | L1/L2/L3 前 | 任意步骤包括 L4 前 | Ostrich L4 前切换 |
| 旁白 9 行无结尾页 | 标"违反铁律" | 软规则+默认接受 | 4+ 用户选 A |
| "模板化了" 触发 | 仅"换语境"同义词 | 明确 100% 等同换语境 | 多本触发 |

---

## 后续 agent 自检清单（v1.1）

每次新会话开始，跑一遍：
- [ ] 当前是 L1/L2/L3/L4 哪一步？
- [ ] 上一步用户是否已确认？
- [ ] 当前问题是"确认型"还是"选择题"？
- [ ] 用户回"确认"——是确认还是跳过了选择题？（默认走 A + 标注）
- [ ] 是否有中途风格切换（含 L4 前切换）？
- [ ] 目标词是否在高风险清单（crow/shark/wolf/dark/black）？
- [ ] 是否有主线方向选择？
- [ ] 修改指令是 3 种里的哪一种？（改中文 / 换一种表达方式 / 换语境）
- [ ] 用户是否说了"模板化了"？=100% 等同换语境
- [ ] 用户是否回复"算了/不换了"？=保留原句立即推进
- [ ] 用户消息是否含完整旁白表格？→ 跳 L1-L3 直接 L4
- [ ] 旁白是否 9 行？→ 询问 A/B 后默认 A