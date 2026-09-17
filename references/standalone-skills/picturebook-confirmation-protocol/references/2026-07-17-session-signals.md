# 2026-07-17 会话信号记录

## 本次会话触发的关键用户信号

### 信号 1：流程跳步（最高优先级）
- 用户原话："请严格按照skill规范来"
- 触发场景：lily of the valley 绘本，agent 一次性输出 L1+L2+L3+L4
- 修复：见 SKILL.md ⚠️ 流程跳步铁律 + 本 skill 协议

### 信号 2："确认" 词歧义（最高频）
- 触发次数：5+ 次（Shell/Dragonfly/Swan/Crow/Woodpecker/Caterpillar/Seagull/Magpie）
- 用户每次回"确认"实际是 step-confirm，不是 A/B/C/D 选择
- 修复协议：见本 skill 主文件"陷阱 1"

### 信号 3：主线 A/B/C/D 必问场景
- 触发目标词：dragonfly（颜色/飞翔/水域/叫声）、caterpillar（颜色/爬行/食性/变身）、seagull（飞翔/羽毛/生态/叫声）、magpie（羽毛/长尾/叫声/文化）、swan（姿态/羽毛/水域/食性）、crow（颜色/飞翔/食性/文化）、white crane（姿态/修长/湿地/食性）、pigeon（羽毛/飞翔/城市/叫声）、woodpecker（敲击/羽毛/生态/舌头）
- 不触发：cat/dog/tiger 等特征唯一动物
- 用户实测选择：D（dragonfly 颜色鲜艳）/ A（caterpillar 致敬原作）/ C（seagull/white crane/pigeon/woodpecker 生态）/ C（swan 水上滑行）/ D（magpie 中国文化）/ C（crow 坚持原词）

### 信号 4：风格中途切换
- 触发：woodpecker 用户从 Eric Carle 拼贴风切到蜡笔手绘童趣风
- 正确处理：先确认切换，再重做 L2（场景锚点描述差异大），L3 不改，L4 全量重写

### 信号 5：目标词安全预检
- 触发：crow 乌鸦
- 风险：黑色调沉重+不祥寓意
- 4 选项模式：A=换词/B=换词/C=加正面包装/D=坚持原词
- 用户实测选 D（坚持原词，旁白避开不祥意象）

### 信号 6：修改指令分类型
- 6 种类型：改中文/换语境/位置互换/整句删除/改核心词变体/整本方向调整
- 实测触发：
  - 改中文：swan 第 5 句改"天鹅的脖子长长的"
  - 换语境：apricot blossom 第 9 句
  - 改核心词：apricot blossom 多次核心词标准化
  - 删整句：shell 第 10 句删除导致 L4 减 1 张图

---

## 一次性完成的批量绘本（本会话 12 本）

| # | 目标词 | 主线选择 | 风格 | 状态 |
|---|--------|---------|------|------|
| 1 | apricot blossom | - | Eric Carle S06 | L1→L4 完成 + 加页 1 次 |
| 2 | lily of the valley | - | Eric Carle S06 | L1→L4 完成（用户跳步纠正） |
| 3 | shell | - | Eric Carle S06 | L1→L4 完成（用户去第 10 句） |
| 4 | ladybug | 动物主角路径 B | Eric Carle S06 | L1→L4 完成 |
| 5 | dragonfly | D=颜色鲜艳 | Eric Carle S06 | L1→L4 完成 |
| 6 | seagull | C=海边生态 | Eric Carle S06 | L1→L4 完成 |
| 7 | magpie | D=中国文化 | Eric Carle S06 | L1→L4 完成 |
| 8 | caterpillar | A=致敬原作 | Eric Carle S06 | L1→L4 完成 + 用户重做升级 |
| 9 | white crane | C=湿地生态 | Eric Carle S06 | L1→L4 完成 |
| 10 | swan | B=水上滑行 | Eric Carle S06 | L1→L4 完成 |
| 11 | crow | C=坚持原词 | Eric Carle S06 | L1→L4 完成 |
| 12 | pigeon | C=城市生态 | Eric Carle S06 | L1→L4 完成 |
| 13 | woodpecker | C=森林生态 + 蜡笔手绘童趣风 | 蜡笔手绘童趣风 | L1→L2 完成 |

---

## 后续 agent 自检清单

每次新会话开始，跑一遍：
- [ ] 当前是 L1/L2/L3/L4 哪一步？
- [ ] 上一步用户是否已确认？
- [ ] 当前问题是"确认型"还是"选择题"？
- [ ] 用户回"确认"——是确认还是跳过了选择题？
- [ ] 是否有中途风格切换？
- [ ] 目标词是否在高风险清单（crow/shark/wolf/dark/black）？
- [ ] 是否有主线方向选择？
- [ ] 修改指令是 6 种里的哪一种？