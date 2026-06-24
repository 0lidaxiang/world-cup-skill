# 世界杯 Skill 模板

[English](README.en.md)

这是一个公开、无数据的 Cursor Agent Skill 模板，用于基于本地 CSV 知识库回答世界杯与足球常识问题。

本仓库只包含：

- Cursor Skill 提示词与项目规则
- CSV 表结构与检索流程说明
- 本地校验、合并、ID 检查、赌博关键词扫描、限速请求辅助脚本
- 合规说明与来源标注边界

本仓库刻意**不包含**私有或完整知识库 CSV、实体表、任务计划、生成种子、审查报告、抓取内容、媒体素材、图片、logo、音频、视频或 FIFA 官方素材。

## 这是什么

这个 Skill 期望用户自行维护本地 `data/` 目录，并放入符合 [`docs/csv-schema-design.md`](docs/csv-schema-design.md) 的 CSV 文件。运行时，Skill 会先检查赌博/投注拒答策略，再按问题、别名、关键词和实体检索本地 CSV 行。

## 这不是什么

- 不是 FIFA、IFAB、足协、球队或转播商的官方产品
- 不代表获得 FIFA 或任何第三方的背书、赞助或授权
- 不提供投注、赔率、彩票、盘口或赌博建议
- 不作为医疗、法律或商业权利建议
- 不包含已授权的世界杯数据包或官方媒体素材

## 文件结构

```text
.cursor/
  rules/                         # 采集与脚本护栏
  skills/world-cup/SKILL.md       # 公开版 Skill 提示词
docs/
  csv-schema-design.md            # CSV 表结构
  data-collection-policy.md       # 外网请求规范
  id-conventions.md               # ID 与禁赌 token 规范
  skill-retrieval-guide.md        # 检索流程
scripts/
  fetch_utils.py                  # >=1 秒间隔的限速 HTTP 工具
  validate_knowledge.py           # CSV 表结构与内容校验
  merge_batches.py                # 本地 CSV 合并工具
  scan_gambling_all.py            # 禁止词扫描
  check_ids_all.py                # ID/related_id 一致性检查
data/
  .gitkeep                        # 占位文件
```

## 快速开始

1. 克隆本仓库。
2. 按文档表结构，把你自己的本地 CSV 文件放到 `data/`。
3. 用 Cursor 打开这个文件夹。
4. 在 Agent 模式中提问足球或世界杯相关问题。

常用维护命令：

```bash
python3 scripts/validate_knowledge.py --all --strict
python3 scripts/scan_gambling_all.py
python3 scripts/check_ids_all.py
```

## 数据与合规

你添加的任何数据都应自行确认可发布、可使用。请避免复制受保护的文章、图片、logo、吉祥物形象、歌曲、比赛画面、字幕、采访稿、转录文本或专有数据库。事实和短事实表述通常比原始表达更安全，但仍需遵守来源条款。

任何外网采集都必须遵守 robots.txt、来源条款、版权要求，并符合本项目相邻请求至少间隔 1 秒的要求。不要采集投注、赔率、盘口、彩票或赌博相关材料。

详见 [`NOTICE`](NOTICE) 和 [`docs/data-collection-policy.md`](docs/data-collection-policy.md)。

## 许可证

本仓库中的代码和文档以 [Apache License 2.0](LICENSE) 发布，但不包括第三方名称、商标，以及你在本地自行添加的任何数据或内容。
