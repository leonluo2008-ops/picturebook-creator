# Darwin实测案例：页面数不够时扩展语境页的规则

## Session: 2026-05-29（下午）

---

## 问题：8+页时词族凑数导致质量差

### 现场回放

用户反馈：领读绘本需要8页内页，但自然句式叠加（6级骨架）只能产生5-6个语境页，不够时skill硬塞词族扩展页凑数（c-AR, f-AR, j-AR, st-AR），用户觉得非常糟糕。

**错误做法示例：**

| 页码 | 内容 | 问题 |
|------|------|------|
| P5 | A blue car. | 正常语境页 |
| P6 | A fast car. | 正常语境页 |
| P7 | c-AR, f-AR, j-AR, st-AR | 硬塞词族，质量差 |

### 根因分析

skill只有「6级句式骨架叠加规则」，没有「当页面数不够时如何扩展语境页」的规则。

### 修复内容（已推送）

**新增「语境页扩展规则」（L2步骤）：**

| 扩展维度 | 说明 | 示例 |
|----------|------|------|
| 换颜色/属性 | 同句式，换目标事物的颜色或属性 | A red car. → A blue car. → A yellow car. |
| 换场景 | 同句式，换所处的环境或地点 | The car on the road. → The car in the rain. → The car at night. |
| 换主语 | 同一个动作，换成不同的角色发出 | A cute cat walks. → I see a cat. → The dog looks at the cat. |
| 换动作 | 同一个主语，换成不同但合理的动作 | A car runs. → A car stops. → A car turns. |
| 换句式模板 | 同一个场景，用不同句型重新描述 | "A blue car." → "Look at the blue car." |

**扩展优先级：**
1. 换颜色/属性（最自然）
2. 换场景（节奏保持）
3. 换主语/换动作（引入互动感）
4. 换句式模板（最后用）

**词族扩展页重新定位：**
- 原来是「默认必加」
- 现在是「可选加分项，只有≥3个实用词族且教学价值明确才加」
- 不再是凑页数的工具

**car 8页语境页示例：**

| 页码 | 句式 | 扩展维度 |
|------|------|----------|
| P1 | A red car. | 颜色（起点） |
| P2 | A red car runs. | 颜色→动词 |
| P3 | A blue car. | 换颜色 |
| P4 | A blue car runs. | 换颜色+动词 |
| P5 | The car in the rain. | 换场景 |
| P6 | The car at night. | 换场景 |
| P7 | I see a car. | 换主语 |
| P8 | The car stops. | 换动作 |

---

## Git记录

- commit `a04d262` on hermes-main
- 修复文件：SKILL.md（L2步骤新增语境页扩展规则章节）