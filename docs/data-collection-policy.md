# 数据采集与外部请求规范（公开模板版）

> 版本：v1.0 · 所有 Agent 与采集脚本必须遵守

---

## 一、核心原则

**对外部网站/API 的请求必须限速，宁可慢，不可高频。**

| 要求 | 说明 |
|------|------|
| 默认间隔 | 相邻两次请求之间 **至少间隔 1 秒**（`MIN_REQUEST_INTERVAL_SEC = 1.0`） |
| 禁止行为 | 并发轰炸、无间隔循环、多线程同时抓同一域名 |
| 优先顺序 | ① 用户本地已清权 CSV/文档 ② 单次批量公开数据 ③ 必要时才联网抓取 |
| 失败重试 | 遇 429/503 时 **指数退避**（建议 2s → 4s → 8s），不得立即连发重试 |

本公开仓库不包含采集数据或生成种子。**今后凡新增联网抓取逻辑，必须使用** [`scripts/fetch_utils.py`](../scripts/fetch_utils.py)。

---

## 二、Agent 执行 SOP 补充

1. 采集或维护本地数据前，先确认来源条款、版权、商标、隐私与商业使用权限；能用已清权资料编写字段的，**不要**为省事开爬虫。
2. 必须使用 Firecrawl、MCP 搜索、脚本 `requests` 等时：
   - 串行请求，间隔 ≥ 1 秒；
   - 单次会话抓取 URL 数量设上限（建议 ≤ 30），超出则分批、下次会话继续；
   - 在本地维护记录中保存数据源、抓取时间、许可或使用依据，便于复查。
3. 尊重目标站 `robots.txt` 与版权；不抓取赌博、赔率、盘口类页面（与 [`id-conventions.md`](id-conventions.md) §7.3 一致）。

---

## 三、脚本实现要求

```python
from fetch_utils import RateLimitedFetcher

fetcher = RateLimitedFetcher(min_interval_sec=1.0)
html = fetcher.get("https://example.com/page")  # 自动等待 ≥1s
```

- `min_interval_sec` 不得小于 **1.0**。
- 禁止在生成脚本里直接 `requests.get` 循环而不调用 `RateLimitedFetcher`。
- 批量导出类 API 若支持一次返回整表，**优先一次请求**，避免拆成数百次小请求。

---

## 四、违规处理

- 校验/合并阶段不检查网速；若发现脚本高频访问、违反 robots.txt、违反来源条款或抓取受限内容，应停止发布并移除相关数据。
- 审核与复核工作应优先使用本地文件，不触发外网抓取。

---

## 五、相关文件

| 文件 | 用途 |
|------|------|
| [`.cursor/rules/world-cup-data-collection.mdc`](../.cursor/rules/world-cup-data-collection.mdc) | **Cursor 强制规则**（`alwaysApply: true`） |
| [`.cursor/rules/world-cup-scripts.mdc`](../.cursor/rules/world-cup-scripts.mdc) | `scripts/**/*.py` 编写约定 |
| [`AGENTS.md`](../AGENTS.md) | Agent 总览与必须遵守项 |
| [`scripts/fetch_utils.py`](../scripts/fetch_utils.py) | 限速 HTTP 工具 |
| [`docs/id-conventions.md`](id-conventions.md) | 禁赌关键词 |

---

## 六、校验与合并门禁

| 场景 | 命令 |
|------|------|
| 单批次写入后 | `python3 scripts/validate_knowledge.py data/knowledge_*.csv --strict` |
| 合并全库后 | `python3 scripts/merge_batches.py --build-all` → `python3 scripts/validate_knowledge.py data/knowledge_all.csv --strict` |
| 全库一键验 | `python3 scripts/validate_knowledge.py --all --strict`（仅 `knowledge_all.csv`） |
| 分文件全扫 | `python3 scripts/validate_knowledge.py --batches --strict`（排除 `knowledge_all.csv`，避免跨文件重复 ID 误报） |

`knowledge_all.csv` 为合并产物，与分文件 ID 相同属预期；**不要**同时对 `knowledge_all.csv` 与各分文件跑跨文件 ID 去重。
