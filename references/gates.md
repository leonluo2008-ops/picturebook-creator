# 门禁与自检（命令 / 参数 / 退出码）

> 三道门禁**缺一不过**；另两道是自检工具（比门禁严，不进缺一不过，是否升级由所有者决定）。
> 所有命令在仓库根目录执行；Windows 控制台先 `$env:PYTHONUTF8=1`（见 §5）。

## §1 一览

| # | 命令 | 查什么 | 退出码 |
|---|---|---|---|
| 1 | `tools/grammar_check.py` | 旁白表：中英大小写、标点、**目标词双语同现** | 0 过 / 1 违规 |
| 2 | `tools/l4_case_check.py` | L4：画面文字**形态**（大小写、双语旁白行） | 0 过 / 1 违规 |
| 3 | `scripts/l4_presence_check.py` | L4：逐页**在不在**（场景段是否出现目标词） | 0 过 / 1 漏页 / 2 参数错 |
| 自检 A | `scripts/l4_structure_check.py` | L4 结构：块存在性、词数、构图三要素、比例、页型、`Pn` 前缀、内页数、目标词次数、中文句长 | 0 / 1 / 2 |
| 自检 B | `tools/title_intro_check.py` | 标题与简介的可机判项 | 0 / 1 / 2 |

## §2 三道门禁

### 第 1 道：旁白表

```bash
python tools/grammar_check.py <旁白表文件.md> --word <核心词>
python tools/grammar_check.py <旁白表文件.md> --word glue --word blue   # 词族伙伴词重复传
python tools/grammar_check.py <旁白表文件.md> --word <核心词> --family-page P7  # 词族页换页号时
```

输入格式：`| 页码 | 英文 | 中文 |` 的 markdown 表。

- **硬闸（EXIT=1 必修）**：英文列含目标词的行，中文列必须同现该词（封面行豁免）——词在中文里消失等于这页没教。
- **软提醒（不阻断）**：中英句末标点数量不一一对应只打印提示。中英句界不一一对应是常态（英文两句、中文一句流水反而更顺口），为凑数量往中文里塞句号是错的——断句节奏由 L3.5 出声朗读裁决。
- 中文列大小写按 CY/T 154—2017 第 7 节：展示行/封面行跟随英文形态，普通句夹用一律小写。

通过输出形如：`解析 N 行旁白, 核对目标词 ['x']` + `语法审计全过——大小写/标点/目标词同现均合规`。

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

- **`--expect-pages` 必须传**（含封面）：不传时只校验「解析到的页」，遇到 `- 旁白:`、`**旁白:**`、中段 BOM 这类写法会**静默丢页**仍报全过。领读默认 9 页＝封面 + 8 内页，页数不同按实际传。
- **词族拓展页**教学载体是词族词，不要求核心词入画——用 `--page-words <页号>=词1,词2` 逐页指定本页词集（页号 0＝封面，1＝第一个内页），否则会按核心词判缺。
- 匹配已加词界 `(?<![a-z])word(?![a-z])`，不再出现 `soa` 命中 `soap`。
- **它只做字面匹配、不读封面书名**：封面这页仍需人工按书名核对。
- `--page-words` 空词集 / 越界页码 / 重复页号 → exit 2（不静默改判）。

## §3 参数归属（最容易传错的地方）

| 参数 | 属于 | 说明 |
|---|---|---|
| `--word` | **四道都要**（可重复） | 目标核心词；伙伴词重复传 |
| `--expect-pages` | 门禁只要求 **presence**；`l4_structure_check.py` 也有（自检用） | grammar / l4_case 没有这个参数，传了 argparse 直接 exit 2 |
| `--page-words` | **只属 presence** | 格式 `页码=词1,词2` |
| `--family-words` | **只属 structure** | 逗号分隔，如 `--family-words hot,dot,cot` |
| `--family-page` | 只属 grammar_check | 词族页页号，默认 `P7` |
| `--max-words` | 只属 structure | 默认 10；只允许 ≤10，超出会被 clamp 并告警 |

- **伙伴词只能重复写 `--word`**：写成空格分隔报 `unrecognized arguments`；写成逗号串 `--word glue,blue` 会被当成一个词——机审扫不到任何东西却照样 EXIT=0，看着通过、实则零校验。
- 退出码契约：`0` 过、`1` 有违规、`2` 输入或参数错误。**看到 2 不要当 1 修**，先看参数。

## §4 两道自检（严于门禁，不进缺一不过）

```bash
python scripts/l4_structure_check.py <L4文件.txt> --word <核心词> --expect-pages <页数> [--family-words hot,dot,cot]
python tools/title_intro_check.py --file <标题简介文件.md> --word <核心词>
```

- `l4_structure_check.py`：块存在性（六类里的 3 类 + 目标词图形化）/ 每页词数 / 构图三要素 / 比例 / 页面类型 / `Pn` 前缀 / 内页数 / 目标词全书次数 / 中文句长。构图三要素在整段提示词里查，第 3 要素按「背景…(边缘|填充|铺边)」同句判定。封面必须是「认知页」且第 0 页识别为封面，否则 exit 2。**它会把按旧口径产出的稿判红，属预期。**
- `title_intro_check.py`：标题（中英两列含词、无括注、含词后 ≤12 字）与简介（目标词恰 1 次、首句不以场景词开头、无禁词、单句 ≤30 字）。语义地基无法机检。
- 另有 `--corpus <corpus.json>` 模式用于统计存量语料，不是写稿检查。

## §5 Windows 环境

- **先设 `$env:PYTHONUTF8=1`**：默认控制台下脚本里的 `✗` 会抛 `UnicodeEncodeError`，修复清单丢失、只剩堆栈。〔证据〕
- 脚本参数里的文件路径用 Windows 原生格式（`C:/Users/...`）；git-bash 风格 `/c/Users/...` 会被 `Path()` 拼成 `\\c\\...` 直接 FileNotFoundError。
- 脚本零依赖、只读本地文件，不联网，不需要 `NOTION_API_KEY`。

## §6 归档与交付的判据

- 归档后**独立回读**：`python scripts/notion_verify.py --word <核心词> --pages <页数>`（多行命中时 `--page-id <id>`）；EXIT=1 即有不符合项。判据与坑见 `notion-ops.md` §4。
- 交付：页数齐全、页序正确、尺寸与体积达标、ZIP 成员齐全、Notion「交付文件」已挂且状态回读为 `已生图`，见 `standard-delivery.md`。
