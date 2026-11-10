# Notion 排产台账

在 Skill 根目录运行配套脚本。只有台账和资产操作需要当前 Hermes 环境的 `NOTION_API_KEY` 与集成访问权限。脚本读取进程变量或当前 Hermes 配置目录的 `.env`。凭据只在进程中使用。

## 查询与定位

- `python3 scripts/notion_archive.py --word WORD --locate` 只读定位。用排产号、核心词和 page_id 区分同名条目。
- 按状态取书时复用 `scripts/notion_archive.py` 的 `resolve_data_source()` 和 `api()` 查询数据源。使用真实状态属性，处理全部分页。记录排产号、核心词、状态和链接，再读取指定稿件的旁白表、简介和单个 L4 代码块。查询和起草本身不推进台账状态。
- 参考资产用 `python3 scripts/asset_ref.py --list` 或 `--name NAME` 只读查找。归档的 `--asset NAME` 在正文添加资产页提及。需要写入资产关系时，定位并确认排产行后使用 `python3 scripts/asset_ref.py --name NAME --link-word WORD`。提示词保持纯文本，资产链接单独保留。

## 新稿归档

用户已确认整本提示词后，属于 Notion 排产交付的任务直接归档。仅预览或仅起草按用户指定的范围交付。按需先加 `--dry-run` 预览将写入的块。已有目标行优先用 `--page-id`；只允许更新现有行、尚无 page_id 时使用 `--no-create`。

```sh
python3 scripts/notion_archive.py --word WORD --page-id PAGE_ID --title "English title" --title-cn "中文标题" --brief "选定简介" --narration narration.md --l4 l4.txt
python3 scripts/notion_verify.py --page-id PAGE_ID --pages PAGE_COUNT
```

新归档由脚本推进为「待生图」。代码、表格已写入但状态推进失败时，先独立回读，只补缺失步骤。

## 存量稿原位修订

1. 按用户范围读取并保存现行旁白表、选定标题、简介和 L4。以页号比对新旧内容，核对简介是否还对应真实动作；同步改动的旁白与画面。单独改旁白时，如果 L4 引用了原句，同步更新对应旁白行。画面事实相符时保留构图。
2. 写前检查原稿是否有并发变化。只 PATCH 已确定的块和受影响的表格行，保护筛查信息、人工批注、附件、状态和未改字段。表格 PATCH 按原表宽度提供每格一个 rich_text 数组。
3. 保留一个 L4 代码块。用 `code_blocks()` 约 1900 字符分段并交替设置 bold 注解，避免 Notion 合并相邻段；回读单块端点拼回全文。修改时逐本处理，保留原状态，包括「修改中」「待生图」。
4. 写后重新 GET 旁白表、整本代码块、涉及的简介与台账状态，与定稿对照。用户要求备注时，用一条本轮摘要标明改动或测试重点。中断时先回读再补写，避免重复附加。
