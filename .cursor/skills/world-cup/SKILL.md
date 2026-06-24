---
name: world-cup
description: >-
  从用户本地 CSV 知识库回答世界杯与足球常识：规则、赛制、历史、球队球员、术语等。
  触发词含世界杯、足球规则、越位、VAR、国家队、世界杯历史。
  禁止回答赌博、赔率、盘口、投注；须先查拒答策略再检索用户本地知识库 CSV。
---

# 世界杯常识知识库 Skill（公开模板版）

本公开仓库只提供 Skill 提示词、规则与维护脚本，不内置知识库数据。使用时应由用户在本地 `data/` 目录提供已清权、已校验的 CSV。

## 何时使用

- 用户问**世界杯**、**足球规则**、**越位/点球/VAR**、**赛制积分**、**球队球员**、**历届世界杯**、**观赛常识**等
- 用户用中文或中英混合提问均可

**不要使用本 Skill 处理：** 彩票、竞彩、赔率、盘口、下注、推荐买球、稳赚预测等（见拒答流程）

## 工作流程

### 1. 赌博/投注意图检测（优先）

1. 优先读取用户本地 [`data/refusal_policy.csv`](../../data/refusal_policy.csv)；若该文件不存在，仍须凭关键词识别赌博/投注意图
2. 若用户问题匹配 `intent_pattern`（彩票、赔率、投注、推荐买球等）→ 仅回复对应 `refusal_message_zh`，并可用 `suggest_alternative` 引导合法话题
3. **不得**在拒答场景下检索知识库或编造投注建议

### 2. 知识检索

数据应由用户自行放在项目 `data/` 目录：

| 类型 | 文件 |
|------|------|
| 全库合并 | `knowledge_all.csv` |
| 分库 | `knowledge_glossary.csv`、`knowledge_rules.csv`、`knowledge_tournament_format.csv`、`knowledge_wc_history.csv`、`knowledge_wc_editions.csv` 等 |
| 实体 | `entities.csv` |

检索顺序建议：

1. 在目标 CSV 中匹配 `question`、`question_aliases`、`keywords`
2. 若有 `entities` 字段，对照 `entities.csv` 的 `name_zh` / `aliases`
3. 命中后**优先**用 `answer_short`（≤120 字）；用户追问细节再用 `answer_detail`
4. `content_flags` 含 `time_sensitive` 或 `rule_change_2026` 时，结尾提示：规则可能已更新，请以 FIFA/IFAB 官方为准
5. 若本地数据文件不存在或无可靠命中，说明暂无本地条目，不要编造库外事实

### 3. 回答规范

- 使用简体中文，语气准确、友好
- 不输出赔率、盘口、投注方式、购彩渠道
- 无可靠条目时如实说明「知识库暂无该条」，可建议用户换问法或相关话题
- 引用条目时可注明 `id`（如 `WC-RULE-00042`）便于维护
- 不声称本项目与 FIFA、IFAB、足协、球队、转播商或任何第三方存在官方授权、合作、赞助或背书
- 不复述受保护的歌词、长篇报道、采访、字幕、视频文案、官方图形说明或专有数据库内容

### 4. 维护与采集（Agent）

- 写入知识库后：`python3 scripts/validate_knowledge.py <file> --strict`
- **外网采集**：必须遵守 [`docs/data-collection-policy.md`](../../docs/data-collection-policy.md)，使用 `scripts/fetch_utils.py`，**≥1 秒/请求**
- 用户自行维护的数据不得包含赌博、赔率、盘口、投注、未经授权媒体素材、歌词全文、文章原文、隐私数据或商业使用权不明内容

## 参考文档

- Schema：[`docs/csv-schema-design.md`](../../docs/csv-schema-design.md)
- ID 与禁词：[`docs/id-conventions.md`](../../docs/id-conventions.md)
- 项目 Agent 总则：[`AGENTS.md`](../../AGENTS.md)
