# -*- coding: utf-8 -*-
"""SKILL.md 静态检查器（复检基础设施）。

检查项：
A. 交叉引用 `见「X」`：按分隔符拆段，任一段命中标题即通过（语义是否指对仍需人工）
B. 文件引用：references/ tools/ scripts/ 路径存在性（支持通配/前缀）
C. 旧口径/已闭合串残留：含历次审计的终检串（六个视角、2行3列、29 本 243 页、189/189 等）
D. 数字口径：a/b 形式登记 + 「N 本 M 页」分母自洽检查（N×9 应等于 M，故事模式除外）
E. 占位符：TODO/FIXME/待补/TBD，及非示例语境的 XXX
F. 「步骤」类标题编号连续性

限制（诚实声明）：不查语义矛盾、不查跨文件一致性、不查「同一约束两档」；D 类只做算术自洽，不做证据溯源。

用法: python skill_lint.py <SKILL.md> [--out <报告路径>]
退出码: 0=无 A/B/C/E 类问题；1=有问题
"""
import io
import os
import re
import sys

LEGACY = {
    # 术语/旧口径
    "六视图": "已改为多视角参考图（默认三视角）",
    "多视图定妆提示词": "统一为「多视角参考图（默认三视角）」",
    "定稿参考": "已改为「制作基准」（库 schema）",
    "角色/场景/物件": "库内实际选项是 角色 / 风格参考",
    "audit_ledger": "已由 scripts/l4_presence_check.py 替代",
    "按顺序写": "块序已改为存在性硬、顺序软",
    # 历次审计的终检串（闭合后应为 0）
    "六个视角": "定妆模板已改三视角",
    "2行3列": "定妆模板已改三视角",
    "所有六个视角": "定妆模板已改三视角",
    "硬上限 15 词": "词数已统一为领读硬上限 10",
    "中文改动不进 L4": "已改为表格行 + L4 行同步",
    "189/189": "已改为可复现口径（45 文件 426 行 381 含中文）",
    "下列七类信息": "已改为「六类 + 每条构图要求」",
    "29 本 243 页": "分母错：应为 27 本领读模式共 243 页",
    "超过10个英文词": "词数口径已改为硬上限 10（领读）",
}


def main():
    path = sys.argv[1]
    out = None
    if "--out" in sys.argv:
        out = sys.argv[sys.argv.index("--out") + 1]
    root = os.path.dirname(os.path.abspath(path))
    text = io.open(path, encoding="utf-8").read()
    lines = text.splitlines()

    L = ["# SKILL.md 静态检查报告", "", "文件：`%s`" % path,
         "体积：%d 字节 / %d 行" % (len(text.encode("utf-8")), len(lines)), ""]

    # 标题集合
    heads = []
    for i, ln in enumerate(lines, 1):
        m = re.match(r"^(#{1,6})\s+(.*)$", ln)
        if m:
            heads.append((i, len(m.group(1)), m.group(2).strip()))
    head_text = "\n".join(h[2] for h in heads)

    problems = 0

    # A 交叉引用
    L.append("## A. 交叉引用 `见「…」`")
    refs = []
    for i, ln in enumerate(lines, 1):
        for m in re.finditer(r"见[「『]([^」』]{2,40})[」』]", ln):
            refs.append((i, m.group(1)))
    bad_refs = []
    for i, name in refs:
        # 复合引用（如「步骤L1→参考图资产图库」）按分隔符拆开，任一段能对上标题即算命中
        parts = [re.sub(r"[（(].*?[)）]", "", p).strip()
                 for p in re.split(r"[→>/,，、]", name)]
        parts = [p for p in parts if len(p) >= 2]
        if not any(p in head_text for p in parts):
            bad_refs.append((i, name))
    L.append("- 引用总数：%d；找不到对应标题：%d" % (len(refs), len(bad_refs)))
    for i, name in bad_refs:
        L.append("  - L%d: 见「%s」→ 全文标题里没有" % (i, name))
    problems += len(bad_refs)
    L.append("")

    # B 文件引用
    L.append("## B. 文件引用")
    files = sorted(set(re.findall(r"(?<![\w/])((?:references|scripts|tools)/[A-Za-z0-9_\-./%*]+)", text)))
    bad_files = []
    glob_ok = []
    for f in files:
        if "*" in f:
            glob_ok.append(f)
            continue
        p = os.path.join(root, f.replace("/", os.sep))
        if os.path.exists(p):
            continue
        # 前缀式通配写法（如 `scripts/notion_` 对应 scripts/notion_*.py）也算存在
        d = os.path.dirname(p)
        base = os.path.basename(f)
        if os.path.isdir(d) and base and any(n.startswith(base) for n in os.listdir(d)):
            glob_ok.append(f + "*")
            continue
        bad_files.append(f)
    L.append("- 引用文件：%d（其中通配/前缀 %d）；不存在：%d" % (len(files), len(glob_ok), len(bad_files)))
    for f in bad_files:
        L.append("  - `%s` 不存在" % f)
    problems += len(bad_files)
    L.append("")

    # C 旧口径
    L.append("## C. 旧口径残留")
    for k, why in LEGACY.items():
        n = len(re.findall(re.escape(k), text))
        flag = "" if n == 0 else "  <<< 需核对（%s）" % why
        L.append("- `%s`：%d 次%s" % (k, n, flag))
        problems += n
    L.append("")

    # D 数字口径登记
    L.append("## D. 比例/计数口径登记（人工比对用）")
    ratios = sorted(set(re.findall(r"\b\d{1,4}/\d{1,4}\b", text)))
    L.append("- 出现的 a/b 形式：%s" % ("、".join(ratios) if ratios else "无"))
    counts = {}
    for r in ratios:
        n = len(re.findall(re.escape(r), text))
        counts[r] = n
    L.append("- 各自出现次数：%s" % ("、".join("%s×%d" % (k, v) for k, v in counts.items()) or "无"))
    # 分母自洽：出现「N 本 … M 页」且 N*9 != M 时告警（故事模式另计，故只报不判死）
    denom_bad = []
    for m in re.finditer(r"(\d{1,3})\s*本[^\n]{0,20}?(\d{2,4})\s*页", text):
        b, pg = int(m.group(1)), int(m.group(2))
        if b * 9 != pg and b not in (2, 29):
            denom_bad.append((m.group(0).strip(), b, pg))
    L.append("- 「N 本 M 页」分母自洽：%s" % ("无异常" if not denom_bad else "发现 %d 处疑点" % len(denom_bad)))
    for s, b, pg in denom_bad:
        L.append("  - `%s`：%d 本 × 9 页 = %d ≠ %d 页" % (s, b, b * 9, pg))
    problems += len(denom_bad)
    L.append("")

    # E 占位符
    L.append("## E. 占位符残留")
    # TODO/FIXME/待补/TBD 一律算问题；XXX 只在「非示例」语境算（如「英文标题 XXX 作为封面主文字」是反例）
    ph = []
    for m in re.finditer(r"TODO|FIXME|待补|TBD", text):
        ph.append((m.start(), m.group(0)))
    for m in re.finditer(r"XXX", text):
        ctx = text[max(0, m.start() - 12):m.end() + 12]
        if "反例" in ctx or "会被" in ctx or "英文标题" in ctx or "裸写" in ctx:
            continue
        ph.append((m.start(), "XXX"))
    L.append("- 命中：%d %s" % (len(ph), sorted(set(x[1] for x in ph)) if ph else ""))
    problems += len(ph)
    L.append("")

    # F 标题编号断档
    L.append("## F. 标题编号连续性（仅查「### 步骤」与「## v」类）")
    steps = [(i, t) for i, lv, t in heads if re.match(r"^(步骤|Step)", t)]
    nums = []
    for i, t in steps:
        m = re.search(r"(\d+)", t)
        if m:
            nums.append((i, int(m.group(1)), t))
    gaps = []
    prev = None
    for i, n, t in nums:
        if prev is not None and n > prev + 1 and n - prev < 10:
            gaps.append((prev, n, t))
        prev = n
    L.append("- 步骤类标题：%d 个；编号跳跃：%d" % (len(nums), len(gaps)))
    for a, b, t in gaps:
        L.append("  - 从 %d 跳到 %d（L%d %s）" % (a, b, next(x[0] for x in nums if x[1] == b and x[2] == t), t))
    L.append("")

    L.append("## 结论")
    L.append("- A/B/C/E 类问题合计：**%d**" % problems)
    L.append("- 判定：%s" % ("PASS" if problems == 0 else "需处理"))

    report = "\n".join(L)
    if out:
        io.open(out, "w", encoding="utf-8").write(report)
        print("报告写出: %s" % out)
    print(report)
    return 0 if problems == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
