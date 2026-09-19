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

    # 中文核心词同现率（2026-09-18 peekaboo册实测）：查中文翻译覆盖率（盲听强化）
    tw2 = (target_word or '').lower().strip()
    cn_core = CN_MAP.get(tw2)
    if cn_core:
        hit = sum(1 for _, _, cn in rows if cn_core in cn)
        if hit < len(rows):
            warns.append(f"中文核心词翻译 '{cn_core}' 仅 {hit}/{len(rows)} 句出现——盲听强化断裂（中文核心词同现率），缺译句人工补译")
    # 绑定形态唯一性（2026-09-18 4样本实测）：中文列末尾绑定的英文块应一致，禁情态拼装块
    binds = []
    for seq, en, cn in rows:
        m = re.search(r"[，,]\s*([A-Za-z][A-Za-z' ]*[a-zA-Z'])\s*[!.?！？]*\s*$", cn)
        if not m:
            m2 = re.search(r"^([A-Za-z][A-Za-z' ]*[a-zA-Z'])\s*[!.！。]\s*$", cn)
            m = m2
        if m:
            blk = m.group(1).strip().lower()
            if blk:
                binds.append((seq, blk))
    if len(binds) >= 4:
        from collections import Counter
        cnt = Counter(b for _, b in binds)
        MODAL = {"can", "will", "want", "love", "like"}
        last_row = binds[-1][0]
        from collections import Counter as _C
        blk_cnt = _C(b for _, b in binds)
        for seq, b in binds:
            words = b.split()
            if len(words) >= 2 and words[0] in MODAL:
                if blk_cnt[b] >= 2:
                    issues.append(f"row{seq}: 绑定块 '{b}' 是情态拼装且重复出现（can/want/love+动词），不是常用整块（绑定形态唯一性）")
                elif seq != last_row:
                    warns.append(f"row{seq}: 绑定块 '{b}' 情态拼装出现在非末句——若作教学绑定应改常用整块")
                # 单次+末句 = 互动收尾（落幕型③），合法
        # 变体计数排除功能前缀: 疑问词/情态问句/冠词/否定（教学点本身或反转落幕机制，非教学变体）
        FUNC_PREFIX = {"who", "where", "what", "how", "when", "why", "is", "are", "do", "does",
                       "can", "will", "a", "an", "the", "no", "not", "so"}
        content_forms = {b for b in cnt if b.split()[0] not in FUNC_PREFIX}
        main_binding = cnt.most_common(1)[0][0]
        extra = sorted(x for x in content_forms if x != main_binding)
        if len(extra) >= 2:
            warns.append(f"中文列绑定英文块有 {len(extra)} 种内容变体（{extra}）——变体过多难度大，应全书统一一个常用整块（人工确认）")

    # 中英主语对齐粗检：英文有动物主语而中文无对应（宽松提示）
    CN_ANIMAL = ("狗","猫","鸟","马","象","鱼","兔","鸭","鹅","猪","牛","羊","鹿","鲸","河马","长颈鹿","宝宝","宝贝")
    EN_ANIMAL = ("dog","cat","bird","horse","elephant","hippo","giraffe","whale","rabbit","duck","goose","pig","cow","sheep","deer","baby")
    for seq, en, cn in rows:
        en_main = [w for w in EN_ANIMAL if re.search("(^|[^A-Za-z])" + w + "([^A-Za-z]|$)", en, re.I)]
        if en_main and not any(a in cn for a in CN_ANIMAL):
            warns.append(f"row{seq}: 英文主语 '{en_main[0]}' 在中文列未见对应——中英对齐?")

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



_SKELETON_KEEP = set("呀吗呢吧啊哦哟的了吗是谁哪这那我你他她它和跟不用上下去里外有在")


def cn_skeleton(cn, target_cn=""):
    """提取中文句式骨架(不依赖词表): 实词汉字→□, 功能字/代词/疑问字保留, 拟声叠字保留原字, 英文→X。
    「白天呀白天，day!」→「□呀□X」;「时间呀时间，time!」→「□呀□X」→ 同骨架=模板化(批量查重必报)。
    「滴答，滴答，time!」→「滴答滴答X」(拟声ABAB保留) vs「看，白天来啦，day!」→「看□□X」→ 不同构, 不误伤。
    「这条路通向哪儿，way?」→「□□□□□哪X」;「我背后是谁呀，back?」→「我□□是□呀X」→ 互不同构。"""
    t = re.sub(r"[a-zA-Z0-9'’]+", "X", cn)              # 英文归一
    t = re.sub(r"[，,。！!？?…～—、\-]", "", t)           # 标点删除
    prot = {}                                            # 叠字保护: ABAB与AA占位
    def _protect(mt):
        key = f"\x01{len(prot)}\x01"
        prot[key] = mt.group(0)
        return key
    t = re.sub(r'([\u4e00-\u9fff]{2})\1', _protect, t)    # ABAB(滴答滴答)
    t = re.sub(r'([\u4e00-\u9fff])\1', _protect, t)      # AA(叮叮)
    chars = []
    for ch in t:
        if '\u4e00' <= ch <= '\u9fff':
            chars.append(ch if ch in _SKELETON_KEEP else '□')
        else:
            chars.append(ch)
    t = ''.join(chars)
    t = re.sub(r'□+', '□', t)                            # 连续实词归一
    for key, orig in prot.items():                       # 还原叠字原字
        t = t.replace(key, orig)
    return t.strip()





CN_MAP = {'jump': '跳', 'run': '跑', 'big': '大', 'apple': '苹果', 'rain': '雨',
              'moo': '哞', 'peekaboo': '躲猫猫', 'mummy': '妈妈', 'think': '想'}

def title_check(books_titles):
    """标题备选核心词闸门(2026-09-19用户定版): books_titles = {word: [备选1, 备选2, ...]}
    每条备选必须显示英文核心词(忽略大小写字面匹配)。违规清单返回, 空列表=全过。
    背景: 旧「拟声式允许隐去核心词」豁免已作废——《滴答滴答 · Tick Tock》类被用户审核拦下。"""
    problems = []
    for word, titles in books_titles.items():
        w = word.strip().lower()
        for i, t in enumerate(titles, 1):
            if t and w not in t.lower():
                problems.append(f"{word} 备选{i}《{t}》未显示核心词 → 重写该条(避撞名=换中文侧结构, 不隐去英文词)")
    return problems


def batch_check(books_first_rows, word_cn=None):
    """批量开场句查重(2026-09-18用户定版): books_first_rows = {word: (en_row1, cn_row1)}
     骨架归一默认接模块级 CN_MAP(中文同现率检查同源), word_cn 显式传入优先覆盖。
    同批内骨架重复 ≥2 册 → 问题清单（模板化=必须修复, 锚·批量开场句查重）。"""
    merged = dict(CN_MAP)
    merged.update(word_cn or {})
    seen = {}
    problems = []
    for word, (en, cn) in books_first_rows.items():
        sk = cn_skeleton(cn, target_cn=merged.get(word, ""))
        seen.setdefault(sk, []).append((word, cn))
    for sk, hits in seen.items():
        if len(hits) >= 2:
            words = "、".join(w for w, _ in hits)
            examples = "／".join(cn for _, cn in hits[:3])
            problems.append(
                f"开场句式模板化: {words} 共{len(hits)}册同骨架「{sk}」（如 {examples}）"
                f"——批量开场查重违规（锚·批量开场句查重），每册换开场型（感叹提名/场景引入/悬念提问/声音开场/对话召唤/动作进行）"
            )
    return problems


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
    # Windows GBK 控制台兼容: ✗/⚠ 不在 GBK 内, 输出流不可写时降级 ASCII 标记
    try:
        "✗⚠".encode(sys.stdout.encoding or "ascii")
        mark_bad, mark_warn = "✗", "⚠"
    except (UnicodeEncodeError, LookupError):
        mark_bad, mark_warn = "X", "?"
    print(f"解析 {len(rows)} 行旁白")
    if issues:
        print("\n[必须修复]")
        for i in issues:
            print(" ", mark_bad, i)
    if warns:
        print("\n[建议人工确认]")
        for w in warns:
            print(" ", mark_warn, w)
    if not issues and not warns:
        print("机械预检全过——请继续人工朗读终检（自然语境终检 > 机械检查）")


if __name__ == '__main__':
    main()
