# -*- coding: utf-8 -*-
"""v14 复核闭合（第二批）：数字同步、版本声明、README 结构树、test-prompts、裸裁定。

用法: python apply_moduleV14_close2.py <repo> [--check]
"""
import io
import os
import sys

REPO = r"E:\OneDrive\工作文件夹\儿童绘本\codex-workspace\picturebook-creator"
WS = r"E:\OneDrive\工作文件夹\儿童绘本\codex-workspace"

EDITS = [
    # 数字同步
    ("CHANGELOG.md", "E1", "1922 行 → 142 行", "1922 行 → 144 行"),
    ("CHANGELOG.md", "E2", "76 条反例收敛为 18 条反模式", "76 条反例收敛为 20 条反模式"),
    ("CHANGELOG.md", "E3-历史死链说明",
     "> 这不是迭代，是重建：",
     "> 历史条目里引用的 `docs/nodes/V5-audit/*`、`docs/nodes/V10-规则层收口.md`、`docs/盘点-29本-规则族-*`、`scripts/audit_ledger.py` 已于 2026-11-21 清仓删除，git 历史可查。\n\n> 这不是迭代，是重建："),
    ("docs/项目适配包.md", "F1", "（**142 行 / 11,244 B / version 14.0.0**，2026-11-21 实测）",
     "（**144 行 / 12,209 B / version 14.0.0**，2026-11-21 实测）"),
    ("docs/项目适配包.md", "F5", "| 实测节点产物 | `./nodes/V7*-v13/`（5 本，见 §9） |",
     "| 合规样例（文本层） | `./nodes/样例-coin/`（结构/标题简介/旁白/L4 四份，五道检查全 0） |"),
    ("docs/项目适配包.md", "F6-五本行",
     "| 5 本实测产物（**仅作词型覆盖与文本层证据**） | `./nodes/V7*-v13/`；⚠️ **G8 不合规样本**（coin/pot/whisper 内页旁白纯英文、pot/long 词族页写句子），**不得作验收依据**；V12 会按新口径改写 |",
     "| 合规样例（文本层，1 本） | `./nodes/样例-coin/`；五道检查全 0，可作新稿写法参照。其余 4 本实测产物在清仓中删除（git 历史可查） |"),

    # 版本声明
    ("AGENTS.md", "G1", "当前版本 `13.1.0`", "当前版本 `14.0.0`"),
    ("AGENTS.md", "G2", "**当前版本：13.1.0**", "**当前版本：14.0.0**"),

    # README 目录树
    ("README.md", "R5-结构树",
     """picturebook-creator/
├── SKILL.md              # 主技能文件（完整工作流+规则，唯一事实来源）
├── SOUL.md               # 角色定义
├── AGENTS.md             # 智能体身份与触发词
├── README.md             # 本文件
├── CHANGELOG.md          # 版本说明（含 v10.0.0 重置说明）
├── test-prompts.json     # 测试用例
├── scripts/
│   ├── notion_archive.py       # L5 归档脚本（零依赖 CLI：定位行→写正文→回读校验）
│   ├── l4_presence_check.py    # 门禁 v2.0：逐页「在不在」（--page-words 可指定词族页词集）
│   └── l4_structure_check.py   # 自检 v2.1：块存在性 / 每页词数 / 构图三要素 / 内页数 / 目标词次数
├── tools/                # 校验脚本
│   ├── l4_case_check.py        # 门禁：画面文字形态（大小写与旁白一致）
│   └── grammar_check.py        # 门禁：语法 / 标点 / 目标词同现
└── references/
    └── style-library.md  # 风格备选库（17 种预设风格 S01–S17；SKILL 参考表 9 个文件之一）""",
     """picturebook-creator/
├── SKILL.md              # 主技能文件：frontmatter + 五节（薄，只读这里就能开工）
├── SOUL.md               # 身份与铁律
├── AGENTS.md             # 仓内规则（分支 / 边界 / 约束）
├── README.md             # 本文件
├── CHANGELOG.md          # 版本说明
├── test-prompts.json     # 触发词回归用例
├── references/           # 9 个专题细则，按 SKILL「参考」节按需加载
│   ├── flow.md                 # L1–L3.5 五步动作、输出模板、确认词表、口语门禁
│   ├── rules.md                # 规则总集（9 主题）+ 裁定清单 + 待验证假设
│   ├── l4-spec.md              # L4 输出形态、代码块结构、六类信息、封面
│   ├── gates.md                # 门禁与自检命令、参数归属、退出码
│   ├── notion-ops.md           # L5 归档、改写/重整、取数、状态机
│   ├── cover-design.md         # 封面视觉与提示词
│   ├── style-library.md        # 17 种风格（S01–S17）
│   ├── standard-delivery.md    # 成图验收后的交付打包
│   └── cloud-start.md          # 云端启动与仓维护
├── scripts/              # 5 个：notion_archive / notion_verify / l4_presence_check / l4_structure_check / asset_ref
├── tools/                # 5 个：grammar_check / l4_case_check / title_intro_check / repo_legacy_scan / cloud_check
│   ├── skill-audit/            # 静态检查（skill_lint）
│   └── notion-readonly/        # 只读取证脚本
└── docs/                 # 工作记录：适配包（canonical）/ 需求 / 计划书 / 证据 / 样例"""),

    # W3 映射表过期陈述
    ("docs/W3-重构映射表.md", "R7-过期陈述",
     "2. **`version: 14.0.0` 的三处同档**：本轮只改了 frontmatter。`README.md`「当前版本」与 `CHANGELOG.md` 顶部仍是 13.x——按 `cloud-start.md` 自订纪律，发布前必须同档，属 **W6 版本节点**的活。",
     "2. **`version: 14.0.0` 的三处同档**：本轮只改了 frontmatter；README / CHANGELOG / 适配包 / cloud-start 已由 `c51d8bd` 统一到 14.0.0，**此项已闭合**。"),
]

# 去裸〔裁定〕（rules.md §0 现在声明「无标注＝实践约定」）
TAG_STRIP = [
    ("SKILL.md", "插图有歧义（两种读法）：", "〔裁定〕"),
    ("SKILL.md", "画风过于写实或成人化：", "〔裁定〕"),
]


def patch(root, rel, rid, old, new):
    p = os.path.join(root, rel.replace("/", os.sep))
    t = io.open(p, encoding="utf-8").read()
    n = t.count(old)
    print("%-14s %-34s 命中 %d %s" % (rid, rel, n, "" if n == 1 else "<<<"))
    if n == 1:
        io.open(p, "w", encoding="utf-8", newline="").write(t.replace(old, new))
    return n == 1


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else REPO
    check = "--check" in sys.argv
    bad = []
    for rel, rid, old, new in EDITS:
        if check:
            p = os.path.join(root, rel.replace("/", os.sep))
            t = io.open(p, encoding="utf-8").read()
            n = t.count(old)
            print("%-14s %-34s 命中 %d %s" % (rid, rel, n, "" if n == 1 else "<<<"))
            if n != 1:
                bad.append(rid)
        else:
            if not patch(root, rel, rid, old, new):
                bad.append(rid)
    # 工作区注入层
    p = os.path.join(WS, "AGENTS.md")
    t = io.open(p, encoding="utf-8").read()
    n = t.count("当前版本 `13.1.0`")
    print("%-14s %-34s 命中 %d" % ("G3-工作区AGENTS", "AGENTS.md", n))
    if n >= 1:
        t = t.replace("当前版本 `13.1.0`", "当前版本 `14.0.0`")
        if not check:
            io.open(p, "w", encoding="utf-8", newline="").write(t)
    print("\n%s：未命中 %d" % ("[check]" if check else "[完成]", len(bad)))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
