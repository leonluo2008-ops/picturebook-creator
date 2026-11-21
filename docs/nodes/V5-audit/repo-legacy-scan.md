# 全仓旧口径扫描 · 结果（2026-11-21）

- 工具：`picturebook-creator/tools/repo_legacy_scan.py`（v13 新增，可复跑）
- 起因：v13 重构早期只扫 `SKILL.md` 就宣称「术语残留 = 0」，结果 `SOUL.md` / 仓 `AGENTS.md` / `README.md` 仍写 v11 口径（六视图、每页必须标注、`~/huiben-v2`）——终审抓出，已修（`8137ca0`）

## 扫描范围与结果

```
python3 tools/repo_legacy_scan.py
→ 扫描 31 个文本文件（排除 .git/.venv/__pycache__/node_modules/projects/作品）
→ 合法历史提及 23 处；真残留 0
→ exit 0「全仓旧口径扫描：通过」
```

负控：在临时目录放一个含「六视图/每页必须标注」的 md → **exit 1，准确点名 `BAD.md:1`**。

## 旧词分布（全部为合法语境）

| 文件 | 旧词 | 为什么合法 |
|---|---|---|
| `CHANGELOG.md` | 语境重复页 / audit_ledger | 版本历史必须写清「旧→新」 |
| `RELEASE_NOTES_v13.0.0.md` | 六个视角 / 语境重复页 | 「改前 → 改后」对比表 |
| `SKILL.md:890, 1239` | 语境重复页 | 作为**旧档漂移示例**（「写成『P1 语境重复页』——去掉前缀」） |
| `tools/dangling-whitelist.txt` | huiben-v2 | 本身就是历史例外清单 |
| `tools/repo_legacy_scan.py` | 全部旧词 | 搜索词表 + 自述（脚本自排除） |

## 一个附带发现

`tools/dangling-whitelist.txt:7` 仍写着 `README.md:5 # ~/huiben-v2/ 工作区约定`，但本轮已把 README:5 改成新路径 → 该白名单条目**已过期**（白名单允许多余条目，不影响，但下次维护可清理）。

## 结论

v13 的「术语/格式代际统一」现在有**仓级**证据（不只是 SKILL.md 单文件）：真残留 0，旧词只出现在历史与示例语境。这条比之前「`六视图`=0」的窄口径声明强得多。
