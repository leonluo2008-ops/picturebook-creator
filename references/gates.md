# 门禁与自检（命令 / 参数 / 退出码）

> L4 三道门禁**缺一不过**；**标题判据是 L3 出口门禁**（2026-11-22 所有者裁定升格：EXIT=0 才端给所有者）；结构自检仍是自检，不进缺一不过。
> 所有命令在仓库根目录执行；Windows 控制台先 `$env:PYTHONUTF8=1`（见 §5）。

## §1 一览

| # | 命令 | 查什么 | 退出码 |
|---|---|---|---|
| 1 | `tools/grammar_check.py` | 旁白表：中英大小写、标点、**目标词双语同现** | 0 过 / 1 违规（**读不到文件也是 1**）/ 2 解析到 0 行或参数错 |
| 2 | `tools/l4_case_check.py` | L4 画面词形态 + 旁白行双语 | 0 过 / 1 违规（**读不到文件、解析到 0 页也是 1**）/ 2 仅 argparse 参数错 |
| 3 | `scripts/l4_presence_check.py` | L4：逐页**在不在**（场景段是否出现目标词） | 0 过 / 1 漏页 / 2 参数错（**读不到文件也是 2**）|
| 自检 A | `scripts/l4_structure_check.py` | L4 结构：块存在性、词数、构图三要素、比例、页型、`Pn` 前缀、内页数、目标词次数、中文句长 | 0 / 1 / 2（读不到文件、第 0 页不是封面 → 2）|
| **L3 出口** | `tools/title_intro_check.py --gloss <释义> --pos <词型>` | 标题七判据（E1–E5 + G1/G2/P1）+ 简介可机判项 | 0 / 1 / 2（读不到文件、标题或简介任一侧 0 条 → 2）|

## §2 三道门禁

### 第 1 道：旁白表

```bash
python tools/grammar_check.py <旁白表文件.md> --word <核心词>
python tools/grammar_check.py <旁白表文件.md> --word glue --word blue   # 词族伙伴词重复传
python tools/grammar_check.py <旁白表文件.md> --word <核心词> --family-page P7  # 词族页换页号时
```

输入格式：`| 页码 | 英文 | 中文 |` 的 markdown 表。

- **硬闸（EXIT=1 必修）**：英文列含目标词的行（**含屈折形**，覆盖范围见下框）。中文列必须同现该词（封面行豁免）——词在中文里消失等于这页没教。词形口径由 `tools/wordforms.py` 统一提供，五个脚本共用，不得各写一套。

  > **词形覆盖到哪儿、漏了怎么办**（2026-11-21 定）：`tools/wordforms.py` 覆盖本 skill 四类核心词的常见屈折形——名词 `s/es/ies/ves`、不规则复数（feet/children/scarves…）与复合词（snowman→snowmen）；动词 `s/es/ing/ed`（含 e 去尾、CVC 双写、y→ied）与常见不规则（went/ran/saw…）；形容词 `er/est`（含 y→ier、双写）与不规则（better/best）。
  > **英语屈折形是开放集合，生成器不可能穷尽**。遇到生僻不规则词（如 `dice`、`kine`、专有名词），按工具分别处理：
  > · **第 1、2 道**（grammar / l4_case）：**重复 `--word`** 把词形一起传（`--word die --word dice`）；
  > · **第 3 道**（presence）：重复 `--word` 是「**每页都必须出现**」的 AND 语义，传多个词形会把合规页判红——请改用 `--page-words <页号>=词形` 逐页指定该页实际词形；
  > · **自检 structure**：只接受一个 `--word`，这类词请人工核它的目标词计数。

- **软提醒（不阻断）**：中英句末标点数量不一一对应只打印提示。中英句界不一一对应是常态（英文两句、中文一句流水反而更顺口），为凑数量往中文里塞句号是错的——断句节奏由 L3.5 出声朗读裁决。
- 中文列大小写按 CY/T 154—2017 第 7 节：展示行/封面行跟随英文形态，普通句夹用一律小写。

通过输出形如：`解析 N 行旁白, 核对目标词 ['x']` + `语法审计全过——大小写/标点/目标词同现均合规`。**解析到 0 行旁白时 exit 2**（没校验到东西不等于通过）；读不到文件时 exit 1。

### 第 2 道：L4 画面文字形态

```bash
python tools/l4_case_check.py <L4文件.txt> --word <核心词>
python tools/l4_case_check.py <L4文件.txt> --word floor --word door   # 词族伙伴词
```

- 查的是**形态**：画面上每个英文词的大小写必须与当页旁白文稿一致；文稿小写、画面写成全大写即判红。
- 同时查 **`旁白:` 行双语**：纯英文行判红（`旁白行必须是「英文 / 中文」双语(G8 裁定, 纯英文不合规)`）。
- **它不查存在**：整页压根没写目标词，它照样 EXIT=0。所以必须有第 3 道。

### 第 3 道：L4 逐页「在不在」

```bash
python scripts/l4_presence_check.py <L4文件.txt> --word <核心词> --expect-pages <页数>
python scripts/l4_presence_check.py <L4文件.txt> --word pot --expect-pages 9 --page-words 7=hot,dot,cot
```

- **`--expect-pages` 必须传**（含封面）：不传时只校验「解析到的页」，遇到 `- 旁白:`、`**旁白:**` 这类非标准写法会**静默丢页**仍报全过（v2.0 已全量剥离 `\ufeff`，BOM 不再丢页；但 **`l4_case_check` 不剥 BOM**，中段 `\ufeff` 会让它少解析一页却仍报「全过」——第 2 道没有页数断言，页数要人工核）。领读默认 9 页＝封面 + 8 内页，页数不同按实际传。
- **词族拓展页**教学载体是词族词，不要求核心词入画——用 `--page-words <页号>=词1,词2` 逐页指定本页词集（页号 0＝封面，1＝第一个内页）。**不传 `--page-words` ＝ 该页完全不校验**：脚本跳过该页、打印「跳过 N 页」并 **EXIT=0**，不是「按核心词判缺」。所以必须传才有校验。
- 匹配已加词界 `(?<![a-z])word(?![a-z])`，不再出现 `soa` 命中 `soap`。
- **它只做字面匹配、不读封面书名**：封面这页仍需人工按书名核对。
- `--page-words` 空词集 / 越界页码 / 重复页号 → exit 2（不静默改判）。

## §3 参数归属（最容易传错的地方）

| 参数 | 属于 | 说明 |
|---|---|---|
| `--word` | **五道都要**（`title_intro_check` 的 `--word` 只在 `--file` 模式必填） | `grammar_check` / `l4_case_check` / `l4_presence_check` 可重复传（`action=append`）；**自检 `l4_structure_check.py` 只接受一个** `--word`，重复传静默取最后一个 |
| `--expect-pages` | 门禁只要求 **presence**；`l4_structure_check.py` 也有（自检用） | grammar / l4_case 没有这个参数，传了 argparse 直接 exit 2 |
| `--page-words` | **只属 presence** | 格式 `页码=词1,词2` |
| `--family-words` | **只属 structure** | 逗号分隔，如 `--family-words hot,dot,cot` |
| `--family-page` | 只属 grammar_check | 词族页页号，默认 `P7` |
| `--max-words` | 只属 structure | 默认 10；只允许 ≤10，超出会被 clamp 并告警 |

- **伙伴词只能重复写 `--word`**：写成空格分隔报 `unrecognized arguments`。写成逗号串 `--word glue,blue` 的结果**按工具分**：`grammar_check` / `l4_case_check` 把它当成一个词、**照样 EXIT=0**（机审扫不到任何东西，零校验）；`l4_presence_check` 有 `WORD_OK` 单词语法校验，直接 **exit 2**；`l4_structure_check` 也把它当一个词，会按「目标词全书」大面积判红（**exit 1**），别拿它当参数验证。
- 退出码契约：`0` 过、`1` 有违规、`2` 输入或参数错误。**按工具分**：`grammar_check` / `l4_case_check` 读不到文件返回 **1**；它们自身产生 2 只有两种情况——argparse 参数错误，或 `grammar_check` 解析到 0 行旁白（见 §2）；`l4_presence_check` / `l4_structure_check` / `title_intro_check` 读不到文件返回 **2**。**看到 2 不要当 1 修**，先看参数与文件路径。

## §4 L3 出口门禁 + 结构自检

```bash
python scripts/l4_structure_check.py <L4文件.txt> --word <核心词> --expect-pages <页数> [--family-words hot,dot,cot] [--legacy]
python tools/title_intro_check.py --file <标题简介文件.md> --word <核心词> --gloss <台账中文释义> --pos <台账词型>
```

- `--legacy`：跳过段落骨架断言（仅用于 2026-11-23 前归档的旧书）。

- `l4_structure_check.py`：块存在性（「六类 + 构图要求」里可机检的 4 项：目标词图形化 / 角色一致性 / 场景一致性 / 构图要求）/ 每页词数 / 构图三要素 / 比例 / 页面类型 / `Pn` 前缀 / 内页数 / 目标词全书次数 / 中文句长。构图三要素在整段提示词里查，第 3 要素按「背景…(边缘|填充|铺边)」同句判定。**封面页型不是「认知页」→ 记一条 issue、exit 1**；**第 0 页识别不出封面 → exit 2**（此时加 `--no-cover` 跳过封面专属断言）。**它会把按旧口径产出的稿判红，属预期。**
- `title_intro_check.py`：标题七条（E1–E5 原有五条 + G1 释义逐字在场 / G2 白名单零干扰 / P1 词型非动作类时禁动词屈折与祈使尾）与简介（目标词恰 1 次、首句不以场景词开头、无禁词、单句 ≤30 字）。**必须传 `--gloss` 才跑 G1/G2，不传会打印「未执行」提示**——此时不能据此说标题合规。语义地基无法机检。
- 另有 `--corpus <corpus.json>` 模式用于统计存量语料，不是写稿检查。

## §5 Windows 环境

- **先设 `$env:PYTHONUTF8=1`**：默认控制台下脚本里的 `✗` 会抛 `UnicodeEncodeError`，修复清单丢失、只剩堆栈。〔证据〕
- 脚本参数里的文件路径用 Windows 原生格式（`C:/Users/...`）；git-bash 风格 `/c/Users/...` 直接 **FileNotFoundError**（脚本用 `open()` 直读，不经 `Path` 归一，所以不认这种路径）。
- **五道本地检查脚本**（grammar / l4_case / presence / structure / title_intro）零依赖、只读本地文件，不联网，不需要 `NOTION_API_KEY`；`notion_verify.py` / `notion_archive.py` 这类 Notion 脚本没有 key 会直接退出（见 §6）。

## §6 归档与交付的判据

- 归档后**独立回读**：`python scripts/notion_verify.py --word <核心词> --pages <页数>`（多行命中时 `--page-id <id>`）；EXIT=1 即有不符合项。判据与坑见 `notion-ops.md` §4。
- 交付：页数齐全、页序正确、尺寸与体积达标、ZIP 成员齐全、Notion「交付文件」已挂且状态回读为 `已生图`，见 `standard-delivery.md`。
