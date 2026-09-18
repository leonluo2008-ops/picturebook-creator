#!/usr/bin/env python3
"""旁白质感念读诊断器 v1.0 (2026-09-18)

用途：对一本领读绘本的双语旁白做质感四条的机械可查部分自动预检。
注意：机械检查只是初筛；「节拍感/自然语感」的最终裁决永远是人大声读（自然语境终检）。

输入格式（xlsx 导出文本或直接粘表）：
  序号 | 英文 | 中文
  1 | MANY! | 很多 MANY!
  2 | Many balloons | 很多气球,many balloons

用法：
  python3 bin/narration_quality_check.py < 旁白.txt
  python3 bin/narration_quality_check.py --demo   # 内置示例演示
"""
import sys
import re

MAX_CN_CHARS = 12          # 硬上限（≤11字左右 + 1 容差）
SEGMENT_MAX = 7            # 双短句节拍：逗号分节后单节建议 ≤7 字
MIN_TARGET_HITS = 8        # 目标词全书出现下限（现行规则）


def parse_rows(text):
    """从粘贴文本提取 (序号, 英文, 中文)。容错：表格线/缺失序号。"""
    rows = []
    for line in text.splitlines():
        line = line.strip().strip('|')
        if not line or set(line) <= set('-: '):
            continue
        parts = [p.strip() for p in line.split('|')]
        if len(parts) < 3:
            continue
        if parts[0] in ('序号',):
            continue
        seq, en, cn = parts[0], parts[1], parts[2]
        m = re.match(r'^(\d+)$', seq)
        rows.append((int(m.group(1)) if m else len(rows) + 1, en, cn))
    return rows


def split_cn_english(cn):
    """中文行拆出 纯中文部分 与 英文词列表（按现行锚定格式，英文以逗号并列/句尾绑定）。"""
    # 英文片段 = 连续 latin 字母（含空格短语）
    en_parts = re.findall(r'[A-Za-z][A-Za-z\' ]*[a-zA-Z\']', cn)
    cn_only = re.sub(r"[A-Za-z][A-Za-z' ]*[a-zA-Z']", '', cn)
    cn_only = re.sub(r'[，。！？、,!?]+', '，', cn_only).strip('， ')
    return cn_only, [e.strip() for e in en_parts]


def check_book(rows, target_word=None):
    issues = []
    warns = []

    # —— 推进链素材：每句主语/内容首词 ——
    cn_texts = []
    for seq, en, cn in rows:
        cn_only, _ = split_cn_english(cn)
        cn_texts.append((seq, cn_only))

        # 中文长度（容差 12）
        n = len(re.findall(r'[\u4e00-\u9fff]', cn_only))
        if n > MAX_CN_CHARS:
            issues.append(f"row{seq}: 中文 {n} 字 > {MAX_CN_CHARS}（拆句或删修饰）")

        # 双短句节拍：按逗号分节，任一节 > SEGMENT_MAX 提示
        segs = [s for s in re.split(r'[，,]', cn_only) if s.strip()]
        if segs and any(len(re.findall(r'[\u4e00-\u9fff]', s)) > SEGMENT_MAX for s in segs):
            warns.append(f"row{seq}: 存在 >{SEGMENT_MAX} 字的单节，节拍感可能差（人工朗读确认）")

        # 叠词密度素材（§八B 全书 ≤3-4 处）
    # 目标词覆盖
    if target_word:
        tw = target_word.lower()
        hits = sum(1 for _, en, cn in rows if tw in en.lower() or tw in cn.lower())
        if hits < MIN_TARGET_HITS:
            warns.append(f"目标词 {target_word} 全书出现 {hits} 次 < {MIN_TARGET_HITS}（教学曝光不足）")

    # 全书叠词定语计数（粗扫「XX的」且 XX 为 AA 叠字）+ 骨架型豁免判定（§八B v5.6.0）
    redup = 0
    tokens = []
    for seq, cn_only in cn_texts:
        found = re.findall(r'([\u4e00-\u9fff])\1的', cn_only)
        redup += len(found)
        tokens.extend(found)
    distinct = set(tokens)
    if redup > 4:
        if len(distinct) <= 2 and redup >= 4:
            warns.append(f"叠词定语全书 {redup} 处但仅 {sorted(distinct)} 一对——疑似骨架型叠词（§八B 豁免候选），人工确认是否成对反义+位置固定")
        else:
            warns.append(f"叠词定语全书 {redup} 处 > 4（§八B 幼稚化风险）")

    # 起伏：有无问句/感叹反转句（认知冲突的粗信号；全半角标点归一后再判）
    has_turn = False
    for _, en, cn in rows:
        cn_norm = cn.replace('?', '？').replace('!', '！').replace(',', '，')
        if ('？' in cn_norm or '！' in cn_norm) and any(k in cn_norm for k in ('不', '吗', '什么', '哪里', '哪儿', '为什么', '谁', '怎么', '告诉', '呀')):
            has_turn = True
            break
        # 「不，不，不是」式重复否定反转（无问叹号也成立，小羊上山范式）
        if re.search(r'不[，,]\s*不[，,]?\s*不?是', cn_norm):
            has_turn = True
            break
    if not has_turn:
        warns.append("未检测到认知冲突信号句（问答/反转）——全书可能平铺（质感③），人工确认")

    return issues, warns


def main():
    args = sys.argv[1:]
    if args and args[0] == '--demo':
        text = """| 1 | SMALL AND BIG | 小和大 SMALL AND BIG |
| 2 | The grass is small | 小草小小的,small |
| 3 | The tree is big | 大树大大的,big |
| 4 | Is that big? No! | 那是大的吗?不,不是,no |
| 5 | The mountain is big | 大山大大的,big |
| 6 | The sky is bigger | 天空更大,sky |
| 7 | Dad hugs me | 爸爸抱着我,dad |
| 8 | I am big to dad | 在爸爸眼里我最大,big |"""
    else:
        text = sys.stdin.read()
    rows = parse_rows(text)
    if not rows:
        print("未解析到旁白行（期望「序号 | 英文 | 中文」格式）")
        sys.exit(1)
    issues, warns = check_book(rows)
    print(f"解析 {len(rows)} 行旁白")
    if issues:
        print("\n[必须修复]")
        for i in issues:
            print("  ✗", i)
    if warns:
        print("\n[建议人工确认]")
        for w in warns:
            print("  ⚠", w)
    if not issues and not warns:
        print("机械预检全过——请继续人工朗读终检（自然语境终检 > 机械检查）")


if __name__ == '__main__':
    main()
