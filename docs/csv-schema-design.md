# 世界杯足球常识知识库 — CSV 表头设计

> 目标：支撑约 10,000 条可检索常识，供 `world-cup` Skill 回答用户常见问题；**不包含**彩票、赔率、投注等赌博类内容。

---

## 一、设计原则

| 原则 | 说明 |
|------|------|
| **问答优先** | 每条记录对应一个用户可能问的问题 + 标准答案，Skill 可直接引用或改写 |
| **多维检索** | 分类、标签、关键词、实体并列，支持按主题/人名/届次/规则快速过滤 |
| **可拆分文件** | 按一级分类拆成多个 CSV，单文件约 500–2000 行，便于维护与增量更新 |
| **来源可追溯** | 记录置信度与来源类型，便于后续人工抽检 |
| **赌博隔离** | 数据层不含赔率/盘口；Skill 层对赌博类提问单独拒答（见 `refusal_policy` 字段说明） |

---

## 二、主表列名（26 列）

文件名建议：`data/knowledge_{category_l1_slug}.csv`  
示例：`data/knowledge_rules.csv`、`data/knowledge_world_cup_history.csv`

### 2.1 标识与分类（6 列）

| 列名 | 类型 | 必填 | 说明 | 示例 |
|------|------|:----:|------|------|
| `id` | string | ✓ | 全局唯一 ID，格式 `WC-{分类缩写}-{5位序号}` | `WC-RULE-00042` |
| `category_l1` | enum | ✓ | 一级分类（见第三节） | `规则与裁判` |
| `category_l2` | string | ✓ | 二级子类 | `越位规则` |
| `category_l3` | string | | 三级细类（可选） | `半自动越位` |
| `scope` | enum | ✓ | 知识适用范围 | `world_cup` / `football_general` / `both` |
| `priority` | int | | 展示优先级 1–5，FAQ 越高越靠前 | `4` |

### 2.2 问答核心（5 列）

| 列名 | 类型 | 必填 | 说明 | 示例 |
|------|------|:----:|------|------|
| `question` | text | ✓ | 用户常见问法（中文，可含口语） | `世界杯小组赛怎么分组？` |
| `question_aliases` | text | | 同义问法，`\|` 分隔 | `小组怎么分\|世界杯分组规则` |
| `answer_short` | text | ✓ | 简短答案（≤120 字，Skill 快答用） | `32 队分 8 组，每组 4 队…` |
| `answer_detail` | text | | 详细解释（≤500 字） | 完整规则说明 |
| `answer_format` | enum | | 答案形态 | `fact` / `definition` / `procedure` / `comparison` / `list` / `timeline` |

### 2.3 检索增强（5 列）

| 列名 | 类型 | 必填 | 说明 | 示例 |
|------|------|:----:|------|------|
| `keywords` | text | ✓ | 检索关键词，逗号分隔 | `小组赛,分组,抽签,32强` |
| `tags` | text | | 自由标签，逗号分隔 | `赛制,2026扩军` |
| `entities` | text | | 关联实体 JSON 或 `类型:名称` 对，`\|` 分隔 | `tournament:2022卡塔尔\|team:巴西` |
| `related_ids` | text | | 关联条目 ID，逗号分隔 | `WC-RULE-00038,WC-HIST-00102` |
| `difficulty` | enum | | 用户理解难度 | `入门` / `进阶` / `专业` |

### 2.4 时空与版本（4 列）

| 列名 | 类型 | 必填 | 说明 | 示例 |
|------|------|:----:|------|------|
| `era_start` | year | | 适用起始年（规则/纪录类） | `2018` |
| `era_end` | year | | 适用结束年，空=至今 | `` |
| `region` | string | | 地理范围 | `全球` / `南美` / `欧洲` |
| `language` | string | ✓ | 内容语言 | `zh-CN` |

### 2.5 质量与治理（6 列）

| 列名 | 类型 | 必填 | 说明 | 示例 |
|------|------|:----:|------|------|
| `fact_type` | enum | ✓ | 事实类型 | `rule` / `history` / `record` / `stat` / `bio` / `tactic` / `culture` / `term` |
| `confidence` | enum | ✓ | 可信度 | `official` / `verified` / `common_knowledge` |
| `source_type` | enum | | 来源类型 | `FIFA` / `IFAB` / `historical_record` / `media_archive` |
| `source_ref` | string | | 来源简述或 URL | `IFAB Laws of the Game 2024/25` |
| `content_flags` | text | | 内容标记，逗号分隔 | `time_sensitive,rule_change_2026` |
| `updated_at` | date | ✓ | 最后更新日期 ISO | `2026-06-03` |

---

## 三、一级分类与预估体量（合计 ≈ 10,000 条）

| category_l1 | 文件 slug | 预估条数 | 典型 category_l2 示例 |
|-------------|-----------|:--------:|------------------------|
| 规则与裁判 | `rules` | 800 | 越位、犯规、点球、VAR、补时、红黄牌 |
| 世界杯赛制与组织 | `tournament_format` | 600 | 预选赛、正赛、抽签、扩军、主办国 |
| 世界杯历史概览 | `wc_history` | 700 | 创立、里程碑、经典时刻、争议事件 |
| 历届世界杯 | `wc_editions` | 2,000 | 按届次：冠军、金靴、亮点、数据（每届约 40–50 条 × 22 届） |
| 国家队与地域 | `national_teams` | 1,200 | 传统强队、黑马、洲际分布、队徽绰号 |
| 球员与教练 | `players_coaches` | 1,500 | 球王、名帅、位置传奇、世界杯表现 |
| 俱乐部与联赛 | `clubs_leagues` | 700 | 五大联赛、欧冠、与世界杯关系 |
| 战术与位置 | `tactics` | 600 | 阵型、位置职责、经典战术 |
| 术语与百科 | `glossary` | 500 | 足球黑话、英文缩写、解说常用语 |
| 纪录与统计 | `records_stats` | 800 | 进球纪录、出场、年龄、连胜等 |
| 裁判与纪律 | `discipline` | 300 | 黄牌累计、停赛、公平竞赛 |
| 场地装备与科技 | `venues_tech` | 400 | 球场、草皮、足球、门线、VAR 技术 |
| 女子世界杯 | `womens_wc` | 400 | 女足世界杯独立条目 |
| 足球文化与观赛 | `culture` | 300 | 球迷文化、观赛礼仪、主题曲、吉祥物 |
| 健康与训练 | `health_training` | 200 | 伤病、体能、青训（非医疗诊断） |

**合计：约 10,000 条**

---

## 四、辅助表（可选，2 张）

### 4.1 实体索引表 `data/entities.csv`

用于人物、球队、届次、场馆的标准名称与同义词。

| 列名 | 说明 |
|------|------|
| `entity_id` | 如 `ENT-TEAM-BRA` |
| `entity_type` | `team` / `player` / `coach` / `tournament` / `venue` / `term` |
| `name_zh` | 中文主名 |
| `name_en` | 英文主名 |
| `aliases` | 别名，`\|` 分隔 |
| `country_code` | ISO 国家码（如适用） |
| `related_knowledge_ids` | 关联知识 ID |

### 4.2 拒答策略表 `data/refusal_policy.csv`

Skill 层使用，**不进入**常知识库正文；定义哪些意图必须友好拒答。

| 列名 | 说明 |
|------|------|
| `policy_id` | 如 `REFUSE-001` |
| `intent_pattern` | 意图关键词或正则描述 |
| `refusal_category` | `gambling` / `illegal` / `medical_diagnosis` / `personal_betting_advice` |
| `refusal_message_zh` | 友好拒答话术 |
| `suggest_alternative` | 可引导的合法话题 |

---

## 五、CSV 表头一行（可直接复制）

```csv
id,category_l1,category_l2,category_l3,scope,priority,question,question_aliases,answer_short,answer_detail,answer_format,keywords,tags,entities,related_ids,difficulty,era_start,era_end,region,language,fact_type,confidence,source_type,source_ref,content_flags,updated_at
```

---

## 六、与 Skill 的配合方式（预览）

1. 用户提问 → Skill 先做**赌博/投注意图检测**（查 `refusal_policy.csv`）
2. 非拒答类 → 按 `keywords` / `question_aliases` / `entities` 检索主表
3. 命中后优先返回 `answer_short`，用户追问细节时用 `answer_detail`
4. `content_flags` 含 `time_sensitive` 的条目，Skill 应提示「规则可能已更新，以官方为准」

---

## 七、下一步建议

1. 确认表头是否需要增减列（如是否要英文问答列 `question_en`）
2. 按第三节体量分批采集，建议先从 `rules`、`glossary`、`wc_editions` 开始
3. 每批 500 条做质量抽检后再合并
