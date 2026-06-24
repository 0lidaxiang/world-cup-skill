# World Cup 知识库 — Skill 检索参考

> 对应任务 T401 · 配合 [`.cursor/skills/world-cup/SKILL.md`](../.cursor/skills/world-cup/SKILL.md)

---

## 一、检索前：拒答检测

1. 读取 `data/refusal_policy.csv`
2. 将用户问题与 `intent_pattern` 做子串/关键词匹配（赌博、赔率、投注、推荐买球等）
3. 命中则返回 `refusal_message_zh`，**不**检索知识库

---

## 二、数据源选择

| 用户意图 | 优先文件 |
|----------|----------|
| 规则、越位、犯规、VAR、点球 | `knowledge_rules.csv` |
| 术语、黑话、缩写 | `knowledge_glossary.csv` |
| 赛制、积分、抽签、扩军 | `knowledge_tournament_format.csv` |
| 世界杯通史、时代概览 | `knowledge_wc_history.csv` |
| 某一届世界杯 | `knowledge_wc_editions.csv`（ID 号段见 `docs/id-conventions.md` §2.3） |
| 球队、国家队 | `knowledge_national_teams.csv` |
| 球员、教练 | `knowledge_players_coaches.csv` |
| 不确定 / 跨类 | `knowledge_all.csv`（合并全库） |

实体标准化：查 `data/entities.csv` 的 `name_zh`、`aliases`，写入回答时与知识条 `entities` 列一致。

---

## 三、匹配策略（推荐顺序）

1. **精确问句**：`question` 与用户问题相同或高度相似
2. **别名**：`question_aliases` 以 `|` 分隔，任一片段匹配
3. **关键词**：`keywords` 逗号分隔，命中 ≥2 个优先，≥1 个次之
4. **实体**：用户提到「巴西」「2022世界杯」等，匹配 `entities` 列 `team:巴西|tournament:2022卡塔尔`

多命中时：

- `priority` 数字越大越优先（若已填）
- 同分取 `scope` 与问题更贴合者（`world_cup` / `football_general` / `both`）
- 仍多条：合并 `answer_short`，避免矛盾

---

## 四、回答组装

```
[answer_short]

（用户追问细节时）
[answer_detail]

（若 content_flags 含 time_sensitive 或 rule_change_2026）
提示：规则或赛制可能已更新，请以 FIFA / IFAB 最新公布为准。
```

- 勿编造库外事实；无命中时说明暂无条目并建议相关话题
- 回答中**禁止**出现赔率、盘口、投注、购彩等表述

---

## 五、字段速查

| 字段 | 检索用途 |
|------|----------|
| `id` | 维护引用，格式 `WC-{ABBR}-{5位}` |
| `category_l1/l2/l3` | 分类过滤 |
| `difficulty` | 入门 / 进阶 / 专业，可简化用语 |
| `related_ids` | 延伸阅读，逗号分隔无空格 |
| `confidence` | official > verified > common_knowledge |
| `source_ref` | 可追溯来源 |

---

## 六、命令行辅助（维护者）

```bash
# 校验单库
python3 scripts/validate_knowledge.py data/knowledge_rules.csv --strict

# 重建全库
python3 scripts/merge_batches.py --build-all --skip-validate

# 若维护多批次本地数据，可自行补充进度统计脚本
```

---

## 七、外网补充（仅维护采集时）

- 必须 `scripts/fetch_utils.py`，间隔 ≥1 秒
- 见 `docs/data-collection-policy.md`
