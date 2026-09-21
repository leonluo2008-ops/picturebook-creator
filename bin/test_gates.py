#!/usr/bin/env python3
"""批量闸门常驻测试夹具（2026-09-20 B011-B018 事故沉淀）
双向样本固化：违规样本（本批实况特征）必须被拦、合规样本（B006-B010 特征）必须放行。
后人调阈值/改逻辑后跑一遍：python3 bin/test_gates.py，全 PASS 才许提交。
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from narration_quality_check import style_check, ending_check  # noqa: E402

FIXTURE = Path(__file__).parent / "fixtures" / "audit_b011_18.json"      # 违规样本数据源（8册实况快照, 仓内自持）
FIXTURE_OK = Path(__file__).parent / "fixtures" / "audit_b006_10_endings.json"  # 合规末句样本（仓内自持）


def main():
    fails = []
    # ---- 违规样本必须拦 ----
    d = json.load(open(FIXTURE, encoding="utf-8"))
    rows = {bid: [(r[0], r[1]) for r in b["narration"]] for bid, b in d.items()}
    sc = style_check(rows)
    hit_words = {w for w, _ in sc}
    for need in ("B013", "B018"):  # 「妈妈」8连 / 「爸爸」7连
        if need not in hit_words:
            fails.append(f"style_check 未拦 {need}（同构病灶回退?）")
    clean = {k: v for k, v in rows.items() if k not in ("B013", "B018")}
    sc2 = style_check(clean)
    extra = {w for w, _ in sc2} - {"B012"}  # B012 骨架边界允许争议，主通道必须零误报
    if extra:
        fails.append(f"style_check 误杀合规册: {extra}")
    # ending: B012休息/B015晚安/B016休息 = 3册静止型
    ec = ending_check({bid: b["narration"][-1][1] for bid, b in d.items()})
    if not ec or "3册" not in ec[0][1]:
        fails.append(f"ending_check 未拦静止三连: {ec}")

    # ---- 合规样本必须放行 ----
    d2 = json.load(open(FIXTURE_OK, encoding="utf-8"))
    ec2 = ending_check({k: v["last"] for k, v in d2.items()})
    if ec2:
        fails.append(f"ending_check 误杀 B006-B010: {ec2}")

    if fails:
        print("FAIL")
        for f in fails:
            print(" -", f)
        sys.exit(1)
    print("PASS: 违规拦(B013/B018 style + 3册 ending) / 合规放行(B006-B010 + 其余5册) 双向成立")


if __name__ == "__main__":
    main()
