# 绘本项目目录结构参考

> 用于快速定位工作文件，而非每次搜索。更新于 2026-05-27。

## 活跃工作区

| 路径 | 用途 |
|------|------|
| `/home/luo/huiben-v2/` | 主要绘本项目目录（故事模式 + 领读模式存档） |
| `/home/luo/.openclaw/workspace-huiben-v2/` | OpenClaw 旧版工作区（仍含 session 日志） |
| `/home/luo/作品/` | 已完成绘本作品存档 |

## 典型文件命名模式

```
[项目名]_旁白.md           # 双语旁白（Story 格式：EN/CN 行对）
[项目名]_生图提示词.txt     # 即梦生图提示词
[项目名]_角色定型_即梦提示词.txt  # 六视图定妆提示词
```

## 查找命令

```bash
# 找所有旁白文件
find /home/luo/huiben-v2 -name "*旁白*" -type f

# 按目标词查找（领读绘本）
find /home/luo/huiben-v2 -name "*.md" | xargs grep -l "BLUE\|目标词"

# 按时间找最新文件
find /home/luo/huiben-v2 -type f -name "*.md" -newer /home/luo/huiben-v2/memory/2026-04-13-修正记录.md
```

## 领读模式 vs 故事模式文件区分

- **领读模式旁白**：表格格式 `| 序号 | 英文 | 中文 |`，每行含目标词
- **故事模式旁白**：行对格式 `EN: ... CN: ...`，叙事性更强

## Session Memory 位置

```
/home/luo/huiben-v2/memory/YYYY-MM-DD-*.md    # 每日 session 记录
/home/luo/.openclaw/workspace-huiben-v2/memory/YYYY-MM-DD-*.md  # 旧版 session
```

当用户说"修正 X 旁白"但没提供文件时，优先查 memory 目录看是否有相关 session 记录。
