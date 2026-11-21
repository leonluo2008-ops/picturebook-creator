# ⚠️ 历史一次性补丁（2026-11-21 搬迁前布局）：docs/ 与 tools/ 已移入 picturebook-creator 仓内。
#    本脚本内的相对路径按搬迁前（工作区根）写；如需重放，把 JOBS 里的 `docs/` 改为仓内 `docs/` 的对应路径。
# -*- coding: utf-8 -*-
"""V10 收尾 · 所有者裁定「首音族 不要」落地。

原话：「首音族 不要」（2026-11-21）。
裁定：词族拓展页**只用同尾族**（共同词尾，字形与发音一致）；首音族（r- 开头）不采用。
B639 robot 的存量形态按存量违规处理，不回填。

落点：
1. SKILL「词族拓展页执行细则」第 6 条：两种都可用 → 只用同尾族
2. L2 术语表「词族类型」行同步
3. l4_structure_check：新增「共同词尾 ≥2 字符」机检（首音族会被判红）
4. repo_legacy_scan：把「首音族」加入旧口径词表（残留在活文件里即红）
5. 需求文档追加载定记录 R8

用法: python apply_moduleV10_r8.py <workspace_root> [--check]
"""
import io
import os
import sys

ROOT = r"E:\OneDrive\工作文件夹\儿童绘本\codex-workspace"

EDITS = [
    # 1. SKILL 细则第 6 条
    ("picturebook-creator/SKILL.md", "R8a-SKILL首音族撤销",
     "6. **词族类型**：同尾族（rime，如 pot/hot/dot/cot）与**首音族**（initial sound，如 r-: robot / rabbit / rocket / rain）都可用；**同一本书只用一种，不得混用**。输出 L2 结构表前先逐项核对这一条，不通过不得输出。",
     "6. **词族类型：只用同尾族**（rime，共同词尾，如 pot/hot/dot/cot）。**首音族不采用**（2026-11-21 所有者裁定「首音族不要」）——词族页英文列里每个词必须共享同一词尾（**≥2 字符，字形与发音都一致**）。输出 L2 结构表前先逐项核对，不通过不得输出。"),

    # 2. L2 术语表
    ("docs/项目适配包.md", "R8b-L2术语表",
     "| 词族类型 | 同尾族（pot/hot/dot/cot）或**首音族**（r-: robot/rabbit/rocket/rain）；**同一本书只用一种** |",
     "| 词族类型 | **只用同尾族**（共同词尾 ≥2 字符、字形与发音一致，如 pot/hot/dot/cot）；首音族（r- 开头如 robot/rabbit/rocket/rain）**不采用**（2026-11-21 所有者裁定「首音族不要」） |"),

    # 3. l4_structure_check：同尾族机检
    ("picturebook-creator/scripts/l4_structure_check.py", "R8c-同尾族机检",
     """                    n_fam = len([x for x in re.split(r"[,，]", en_seg.rstrip(".")) if x.strip()])
                    if n_fam < 2 or n_fam > 4:
                        issues.append("[%s] 词族页词数 %d 个，应为 2–4 个（G6：常规 2–3、最多 4）"
                                      % (no, n_fam))""",
     """                    toks = [x.strip().lower() for x in re.split(r"[,，]", en_seg.rstrip(".")) if x.strip()]
                    n_fam = len(toks)
                    if n_fam < 2 or n_fam > 4:
                        issues.append("[%s] 词族页词数 %d 个，应为 2–4 个（G6：常规 2–3、最多 4）"
                                      % (no, n_fam))
                    # R8（2026-11-21 所有者裁定「首音族不要」）：词族词必须共享同一词尾 ≥2 字符
                    if n_fam >= 2:
                        _suf = toks[0]
                        for _t in toks[1:]:
                            _i = 0
                            while _i < min(len(_suf), len(_t)) and _suf[-1 - _i] == _t[-1 - _i]:
                                _i += 1
                            _suf = _suf[len(_suf) - _i:] if _i else ""
                        if len(_suf) < 2:
                            issues.append("[%s] 词族页不是同尾族（共同词尾 %r，需 ≥2 字符）：%s"
                                          "——首音族不采用（2026-11-21 裁定）" % (no, _suf, en_seg[:40]))"""),

    # 4. 扫描器词表
    ("picturebook-creator/tools/repo_legacy_scan.py", "R8d-扫描词表",
     '    "短句串联",  # 2026-11-21 G4 翻案：词族页英文列改为词表，此口径已废',
     '    "短句串联",  # 2026-11-21 G4 翻案：词族页英文列改为词表，此口径已废\n'
     '    "首音族",    # 2026-11-21 所有者裁定「首音族不要」：只准同尾族'),
]


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else ROOT
    check_only = "--check" in sys.argv
    bad = []
    for rel, rid, old, new in EDITS:
        p = os.path.join(root, rel.replace("/", os.sep))
        t = io.open(p, encoding="utf-8").read()
        n = t.count(old)
        print("%-26s %-44s 命中 %d %s" % (rid, rel, n, "" if n == 1 else "<<< 需查"))
        if n == 1 and not check_only:
            io.open(p, "w", encoding="utf-8", newline="").write(t.replace(old, new))
        if n != 1:
            bad.append(rid)

    # 5. 需求文档追加 R8
    if not check_only:
        p = os.path.join(root, "docs", "需求-v13-重构-20261121.md")
        t = io.open(p, encoding="utf-8").read()
        if "### R8 首音族" not in t:
            t = t.rstrip() + """

### R8 首音族（2026-11-21 补裁）

- **用户原话**：「首音族 不要」
- **裁定**：词族拓展页**只用同尾族**（共同词尾 ≥2 字符、字形与发音一致）；首音族（r- 开头，如 robot/rabbit/rocket/rain）**不采用**。
- **影响**：`SKILL.md` 词族细则第 6 条、L2 术语表、`l4_structure_check.py` 均改为只认同尾族并加机检；存量 B639（robot）用的是首音族，按存量违规处理、不回填。
- **订正**：此前 agent 以「未批注按推荐执行」为由承认了首音族，**等于放宽所有者早前的「词族双条件」终版裁决**，且未向所有者披露该冲突——本条按所有者明示裁定纠正。
"""
            io.open(p, "w", encoding="utf-8", newline="").write(t)
            print("需求文档已追加 R8")

    print("\n%s：成功 %d / 未命中 %d" % ("[check 未写盘]" if check_only else "[完成]", len(EDITS) - len(bad), len(bad)))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
