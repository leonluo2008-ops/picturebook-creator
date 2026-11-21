# -*- coding: utf-8 -*-
"""模块 A 收尾：清掉残留的「六视图 / 定稿参考」写法。"""
import io
import sys

REPLACEMENTS = [
    ("A6-步骤4引导语",
     "请上传角色的原始参考图,我将为你生成可在即梦使用的六视图定妆提示词。",
     "请上传角色的原始参考图,我将为你生成可在即梦使用的多视图定妆提示词。", 1),
    ("A7-步骤4生成说明",
     "收到参考图后,生成**六视图定妆提示词**(在一张图上生成六个视角),输出为代码块:",
     "收到参考图后,生成**多视图定妆提示词**(默认在一张图上排正面/四分之三侧/背面三个视角;角色有抓握、攀爬、坐蹲等特殊动作时可扩成姿态表),输出为代码块:", 1),
    ("A8-步骤4输出标签",
     "[角色名] 六视图定妆照提示词:",
     "[角色名] 多视图定妆照提示词:", 1),
    ("A9-使用定位正文",
     "(灵感参考=提气质与配色重画,定稿参考=严格按图)",
     "(灵感参考=提气质与配色重画,制作基准=严格按图)", 1),
    ("A10-词表警示措辞",
     "**取值以库 schema 为准,别照记忆写「定稿参考」**",
     "**取值以库 schema 为准,别照记忆写别的词**", 1),
]


def main():
    path = sys.argv[1]
    check_only = "--check" in sys.argv
    text = io.open(path, encoding="utf-8").read()
    rows = []
    for rid, old, new, expect in REPLACEMENTS:
        n = text.count(old)
        rows.append((rid, n, expect))
        if n == expect:
            text = text.replace(old, new)
    bad = [r for r in rows if r[1] != r[2]]
    for rid, n, expect in rows:
        print("%-22s 命中 %d（预期 %d）%s" % (rid, n, expect, "" if n == expect else "  <<< 不匹配"))
    if bad:
        print("[中止] 未按预期命中，未写盘。")
        return 2
    if check_only:
        print("[check] 全部命中（未写盘）")
        return 0
    io.open(path, "w", encoding="utf-8", newline="").write(text)
    print("[完成] 已改写 %d 处" % len(REPLACEMENTS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
