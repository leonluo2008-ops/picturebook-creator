# 证据 · 本地 L4 旁白行含中文统计（2026-11-21 复算）

> 用途：支撑 SKILL.md「旁白行多是『英文 / 中文』形态」这条判断的分子（`381/426`）。
> 复跑命令：见文末脚本片段。**这条曾被一路审计判为「假数字」，本文件是复核结论：数字成立，审计那路算错。**

## 统计口径

- 范围：`picturebook-creator/projects/**` 下 `L4*.txt` / `l4*.txt`（递归、去重）
- 分子：`旁白:` 行中**含任意汉字**的行数
- 分母：`旁白:` 行总数

## 结果

| 项 | 值 |
|---|---|
| L4 文件数 | **45** |
| `旁白:` 行总数 | **426** |
| 含中文 | **381** |
| 不含中文（纯英文行） | **45** |

## 不含中文的文件明细（正是这 45 行）

| 文件 | 含中文/总数 |
|---|---|
| `B287/L4-draft.txt` | 1/9 |
| `B288/L4-draft.txt` | 1/9 |
| `B289/L4-draft.txt` | 1/9 |
| `B290/L4-draft.txt` | 1/9 |
| `B291/L4-draft.txt` | 1/9 |
| `B294/L4-整本配色试生成.txt` | 5/10 |

合计不含中文 8+8+8+8+8+5 = **45 行**；381 + 45 = 426 ✓

## 为什么审计会得出 426/426

审计那路报「426/426 含中文、0 条纯英文」，并用 `426−45=381` 推测「把文件数当行数」。
本复核显示：**45 这个数字巧合地同时等于文件数与不含中文行数**，审计据此做的推断不成立。
其扫描很可能把「文件名/路径」或整文件中文当成了行内容（未逐行判定），故漏掉了上表 45 行。

## 复跑脚本

```python
import io, re, os, glob
proj = r"E:\OneDrive\工作文件夹\儿童绘本\codex-workspace\picturebook-creator\projects"
files = sorted(set(glob.glob(os.path.join(proj, "**", "L4*.txt"), recursive=True)
                   + glob.glob(os.path.join(proj, "**", "l4*.txt"), recursive=True)))
rows = cn = 0
for f in files:
    t = io.open(f, encoding="utf-8-sig").read()
    m = re.findall(r"(?m)^旁白[:：]\s*(.+)$", t)
    if not m: continue
    rows += len(m)
    cn += sum(1 for x in m if re.search(r"[\u4e00-\u9fff]", x))
print(len(files), rows, cn, rows - cn)
# 期望输出: 45 426 381 45
```

## 块序数字的复跑证据

同批复算还重跑了「29 本 → 领读 27 本 / 243 页」的块序统计，结果与 SKILL.md 一致：

| 项 | 值 |
|---|---|
| 含「角色一致性」 | 135/243 |
| 含「场景一致性」 | 144/243 |
| 含「构图要求」 | 243/243 |
| 完整链（角色→场景→构图） | 133/243 |

已把**逐本紧凑统计**（不含提示词原文，仅页数/页型/比例/词数/块标记计数）落盘为
`docs/nodes/V5-audit/corpus-stats.json`，用于离线复核这些分子（原 corpus.json 体积大且含全文，未入库）。
