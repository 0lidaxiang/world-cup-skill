# ID 与命名规范

> 版本：v1.0 · 对应任务 T004  
> 适用范围：知识库 CSV、实体表、拒答策略表、任务表及后续 Skill 检索

---

## 一、总则

1. **全局唯一**：同一项目内，知识条目 `id` 不得重复。
2. **可读优先**：ID 能从前缀看出类别或实体类型，便于人工排查与日志检索。
3. **固定格式**：字母大写、段间连字符 `-`、序号固定位数（前导零补齐）。
4. **只增不改**：已发布 ID 不因内容修改而变更；废弃条目保留 ID，在 `content_flags` 标记 `deprecated`。
5. **禁止赌博语义**：ID、文件名、`keywords` 中不得出现赔率、盘口、投注等赌博相关 token（见第七节）。
6. **外网抓取限速**：联网采集须遵守 [`data-collection-policy.md`](data-collection-policy.md)（默认 **≥1 秒/请求**，禁止高频并发）。

---

## 二、知识条目 ID

### 2.1 格式

```
WC-{分类缩写}-{5位序号}
```

| 部分 | 规则 | 示例 |
|------|------|------|
| 前缀 | 固定 `WC`（World Cup 项目） | `WC` |
| 分类缩写 | 见 §2.2，3–8 位大写字母/数字 | `RULE` |
| 序号 | `00001`–`99999`，分类内连续递增 | `00042` |

**完整示例：** `WC-RULE-00042`、`WC-WCED-20182`（历届世界杯见 §2.3）

### 2.2 分类缩写对照表

| category_l1 | 分类缩写 | CSV 文件 | 序号上限（规划） |
|-------------|----------|----------|:----------------:|
| 规则与裁判 | `RULE` | `data/knowledge_rules.csv` | 00800 |
| 世界杯赛制与组织 | `TFMT` | `data/knowledge_tournament_format.csv` | 00600 |
| 世界杯历史概览 | `WHIS` | `data/knowledge_wc_history.csv` | 00700 |
| 历届世界杯 | `WCED` | `data/knowledge_wc_editions.csv` | 02000 |
| 国家队与地域 | `NTEM` | `data/knowledge_national_teams.csv` | 01200 |
| 球员与教练 | `PLCO` | `data/knowledge_players_coaches.csv` | 01500 |
| 俱乐部与联赛 | `CLUB` | `data/knowledge_clubs_leagues.csv` | 00700 |
| 战术与位置 | `TACT` | `data/knowledge_tactics.csv` | 00600 |
| 术语与百科 | `GLOS` | `data/knowledge_glossary.csv` | 00500 |
| 纪录与统计 | `RECD` | `data/knowledge_records_stats.csv` | 00800 |
| 裁判与纪律 | `DISC` | `data/knowledge_discipline.csv` | 00300 |
| 场地装备与科技 | `VTEC` | `data/knowledge_venues_tech.csv` | 00400 |
| 女子世界杯 | `WWC` | `data/knowledge_womens_wc.csv` | 00400 |
| 足球文化与观赛 | `CULT` | `data/knowledge_culture.csv` | 00300 |
| 健康与训练 | `HLTH` | `data/knowledge_health_training.csv` | 00200 |

> **缩写命名原则**：3–4 字母为主，避免与 FIFA 国家码混淆；`WCED` = World Cup Edition。

### 2.3 历届世界杯特殊序号段

历届世界杯条目在 `WCED` 分类内按**届次预留号段**，便于按届筛选与批量维护：

| 届次 | 年份 | 主办 | ID 号段（末 5 位） | 示例 |
|:----:|:----:|------|-------------------|------|
| 第 1 届 | 1930 | 乌拉圭 | `01001`–`01090` | `WC-WCED-01001` |
| 第 2 届 | 1934 | 意大利 | `02001`–`02090` | `WC-WCED-02001` |
| 第 3 届 | 1938 | 法国 | `03001`–`03090` | `WC-WCED-03001` |
| … | … | … | `{届次×1000}+001` ~ `+090` | … |
| 第 22 届 | 2022 | 卡塔尔 | `22001`–`22090` | `WC-WCED-22001` |
| 第 23 届 | 2026 | 美加墨 | `23001`–`23080` | `WC-WCED-23001` |

**号段公式：**

```
序号 = 届次编号 × 1000 + 条内顺序（001 起）
```

例：第 22 届第 15 条 → `22015` → `WC-WCED-22015`

非届次专属的泛化条目（如「世界杯史上最快进球」）使用 `WCED-00001`–`00999` 保留段。

### 2.4 序号分配流程

1. 打开目标 CSV，查该分类当前最大序号。
2. 新批次从 **最大序号 + 1** 起连续编号（历届世界杯按 §2.3 号段内递增）。
3. 单批次任务（如 T041）写入前在 `tasks.csv` 的 `notes` 记录起止 ID。
4. 合并多文件前运行校验脚本检查全局唯一性。

### 2.5 关联 ID（related_ids）

- 格式：逗号分隔，无空格：`WC-RULE-00038,WC-HIST-00102`
- 只允许引用已存在或同期批次即将写入的 ID。
- 双向关联非强制；若 A 引用 B，建议在 B 的 `related_ids` 回链（抽检阶段处理）。

---

## 三、实体 ID（entities.csv）

### 3.1 格式

```
ENT-{实体类型}-{标识符}
```

### 3.2 实体类型与标识符

| entity_type | 前缀段 | 标识符规则 | 示例 |
|-------------|--------|------------|------|
| `team` | `TEAM` | FIFA 3 字母国家码（大写） | `ENT-TEAM-BRA` |
| `player` | `PLR` | 姓大写拼音/英文 + 4 位出生年 | `ENT-PLR-PELE-1940` |
| `coach` | `COA` | 姓 + 4 位出生年 | `ENT-COA-SACCHI-1946` |
| `tournament` | `WC` | 4 位年份 | `ENT-WC-2022` |
| `venue` | `VEN` | 城市缩写 + 场馆简称 | `ENT-VEN-LUS-STAD` |
| `term` | `TERM` | 英文术语大写缩写 | `ENT-TERM-VAR` |

**历史球队 / 已更名：** 使用当期常用码，在 `aliases` 记录旧称，不新增重复 ID。

**球员重名：** 追加中间名首字母或国籍码，如 `ENT-PLR-SILVA-POR-1985`。

### 3.3 实体与知识条目的引用

知识表 `entities` 列写法：

```
类型:标准名|类型:标准名
```

示例：`team:巴西|tournament:2022卡塔尔|player:梅西`

- 标准名应与 `entities.csv` 的 `name_zh` 一致。
- 尚未入库的实体可先写标准名，Phase 1 补建 `entity_id`。

---

## 四、拒答策略 ID（refusal_policy.csv）

```
REFUSE-{3位序号}
```

| 规则 | 示例 |
|------|------|
| 从 `001` 递增 | `REFUSE-001` |
| 一策略一行 | 赌博类、违法类、医疗诊断类分条 |

扩展时在文件末尾追加，不插入中间序号。

---

## 五、任务 ID（tasks.csv）

```
T{3位数字}
```

| 规则 | 示例 |
|------|------|
| Phase 0 基建 | `T000`–`T009` |
| Phase 1 实体 | `T010`–`T019` |
| Phase 2 术语 | `T020`–`T039` |
| 各 Phase 预留 10–30 个号段 | `T041` 规则批次 02 |

新增任务：取当前最大 `task_id` 数值 + 1，保持 3 位（超过 999 扩展为 4 位并更新本文档）。

---

## 六、文件与目录命名

### 6.1 知识 CSV

```
data/knowledge_{slug}.csv
```

`slug` 与 §2.2 文件列一致，全小写、下划线分隔。

### 6.2 批次临时文件（可选）

采集过程中可先写：

```
data/batches/{task_id}_{slug}.csv
```

验收合并后删除或归档至 `data/batches/archive/`。

### 6.3 合并全库

```
data/knowledge_all.csv        # 验收合并产物，不手改
```

### 6.4 脚本

```
scripts/validate_knowledge.py
scripts/merge_batches.py
scripts/fetch_utils.py
```

---

## 七、字段内命名约定

### 7.1 枚举值（小写英文）

| 字段 | 允许值 |
|------|--------|
| `scope` | `world_cup`, `football_general`, `both` |
| `answer_format` | `fact`, `definition`, `procedure`, `comparison`, `list`, `timeline` |
| `difficulty` | `入门`, `进阶`, `专业` |
| `fact_type` | `rule`, `history`, `record`, `stat`, `bio`, `tactic`, `culture`, `term` |
| `confidence` | `official`, `verified`, `common_knowledge` |
| `source_type` | `FIFA`, `IFAB`, `historical_record`, `media_archive` |
| `language` | `zh-CN`（v1 默认） |

### 7.2 content_flags

逗号分隔，常用值：

| 值 | 含义 |
|----|------|
| `time_sensitive` | 规则/赛制可能随届次变化 |
| `rule_change_2026` | 与 2026 扩军相关 |
| `deprecated` | 已废弃，Skill 不应优先引用 |
| `needs_review` | 待人工复核 |

### 7.3 赌博禁词（写入前扫描）

以下词及变体**不得**出现在 `question`、`answer_short`、`answer_detail`、`keywords`：

```
彩票, 竞彩, 足彩, 体彩, 福彩, 博彩, 赌博, 赌球, 投注, 下注,
赔率, 盘口, 让球, 大小球, 亚盘, 欧赔, 水位, 串关, 稳赚, 必中
```

Skill 层另以 `refusal_policy.csv` 拦截用户提问意图。

---

## 八、分类内二级命名建议（category_l2 / l3）

不强制 ID 体现二级分类，但 `category_l2` 应使用**稳定中文短语**，便于分组统计：

| 推荐 | 避免 |
|------|------|
| `越位规则` | `规则1` |
| `2022卡塔尔` | `上一届` |
| `巴西` | `南美那个强队` |

`category_l3` 可选，用于技术细分（如 `半自动越位`、`VAR介入流程`）。

---

## 九、快速对照示例

| 对象 | 命名结果 |
|------|----------|
| 越位是什么 | `id=WC-GLOS-00012`, `category_l1=术语与百科` |
| 2022 决赛结果 | `id=WC-WCED-22045`, `entities=tournament:2022卡塔尔` |
| 巴西队世界杯冠军次数 | `id=WC-NTEM-00003`, `entities=team:巴西` |
| 梅西世界杯进球 | `id=WC-PLCO-00128`, `entities=player:梅西` |
| 巴西实体 | `entity_id=ENT-TEAM-BRA` |
| 2022 届次实体 | `entity_id=ENT-WC-2022` |
| 拒答彩票 | `policy_id=REFUSE-001` |
| 采集任务 | `task_id=T041` |

---

## 十、变更记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0 | 2026-06-03 | 初版：15 类知识缩写、WCED 届次号段、实体与任务 ID 规则 |
