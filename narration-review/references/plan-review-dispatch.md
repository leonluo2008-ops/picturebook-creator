# 闸门2 反对者派单模板与失败排查（2026-09-15/16 实测）

## 派单模板要点（delegate_task）
- role=leaf；goal 首句定性「你是 <审查对象> 的强烈反对者」。
- 必读文件全文列绝对路径（审查对象 + 方案档案 + 工作流参照），声明「必读全文再审」。
- 行为约束写死：只审不改；每条问题标严重度（致命/严重/中等/轻微）+证据（引原文）；最后 1-10 总评+一句话总结；禁止凑数，某维度无问题就明说。
- **output_schema**：`{score:number, one_line:string, issues:[{title, severity, evidence}]}`——结构化输出防长报告被截断。
- 硬性输出上限（如 ≤150 行）防子 agent 迭代耗尽；「已验证事实不必重验」写进 context 防重复劳动。
- 声明「依赖习惯/内化的假设不成立」（qa-test-agent 规范：审查对象是无记忆 LLM）。

## 派单失败排查（三连实测）
1. **症状：status=completed 但报告为空 / HTTP 400 "missing x-opencode-session"** → 这是 **provider 路由问题，不是任务问题**。排查 delegation.model 与 fallback 链（opencode-go 端点 chat 全 400）。修复：delegation 切到实测可用 provider/model（如 ollama-cloud/deepseek-v4-flash:0731），先 raw curl 验证 200 再重派。
2. **症状：TRUNCATED: hit max_iterations，报告不完整** → 完整 trace 在 live transcript 日志（结果里给了路径）；重派时收窄必读文件清单 + 加输出上限。
3. **症状：subagent summary 头尾保留中间略** → 全文在 `~/.hermes/cache/delegation/subagent-summary-*.txt`，read_file 续读，勿凭截断版下结论。

## 多轮闸门
首轮报告有致命/严重 → 修复落回正文 → 再派一轮，直到无致命/严重（不是一轮放行）。闸门2 = 唯一判定权威；审计清单只提示「审什么」。

## 修复映射与扫尾纪律（2026-09-17 三轮闸门实测，score 3→4→7 收敛）
- 每轮派单 context = 上轮问题清单 + 修复映射，声明「已验证事实勿重验报告过程，直接验修复后实文」——收敛快的关键。
- **声称已修 ≠ 已修**：映射中每条「已修」必须先在盘上 grep/回读验证过才可写进派单——R2 实测抓到「声称已清的致命短语仍残留在未扫到的章节」。写映射前逐条自验。
- **扫残留 = 全文短语级 grep**，不是只修派单里列过的几处——致命短语可藏在任何触发条件句/理由句里（R1 修三处、§七 第四处漏网）。
- **回归集期待值自己也要过被测判据**（E1/E3 期待修正句时态与全书主线不一致被 R2 抓）——改期待值后用同一判据回测。
- 放行线 = 无致命/严重；轻微记录、中等酌情；交付说明附一行闸门记录（轮次+score+修复要点）。
