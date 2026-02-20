# Phase 3: Intelligence (情报收集)

**文件:** `intelligence.py`
**类:** `Intelligence`
**定位:** 收集软实力指标 — 那些财报上看不到、但决定公司长期命运的定性信息。

---

## 核心理念

> 财务数据是"骨架"，Intelligence 是"血肉"。管理层诚信、护城河动态、内部人行为、价格错杀原因 — 这些信息决定了同样财务数据背后的公司是"金矿"还是"陷阱"。

---

## 五大子分析模块

### 1. KPI 验证 (`_verify_kpis`)

**输入:** Phase 1 识别出的 `specific_kpis` 列表 (如 RPO, Billings, NDR 等)

**逻辑:**
1. 对每个 KPI 执行针对性搜索: `{ticker} {kpi} latest quarter financial results`
2. 如果启用 Deep Search，合并深度搜索上下文
3. LLM 从搜索结果中精确提取最新数值和时间戳
4. 要求格式: `"120% (Q3 2024)"` 或 `"Not Found"`

**输出:** `kpi_values` (dict) — `{KPI名称: 值+时间}`

### 2. 管理层诚信 (`_analyze_management`)

**逻辑:**
1. 通过 `get_press_releases` 获取最近 5 条官方发布
2. LLM 分析管理层是"保守派 (Sandbagger)" 还是"画饼派 (Over-Promiser)"
3. 要求举出具体的 Guidance vs Actual 对比实例，附带季度/日期

**输出:** `management_integrity` (str) — 详细的诚信评估报告

### 3. 竞争护城河 (`_analyze_moat`)

**逻辑:**
1. 搜索: `{ticker} competitive advantage moat analysis new products`
2. LLM 分析护城河是在"变宽"还是"变窄"
3. 关注新产品动力、竞争威胁、数据支撑

**输出:** `product_moat` (str) — 护城河动态分析

### 4. 内部人交易 (`_analyze_insider`)

**逻辑:**
1. 搜索: `{ticker} insider trading recent selling buying` (90 天内)
2. LLM 区分**例行减持** (如期权到期行权) 和**异常抛售** (如 CEO 突然大量卖出)
3. 要求标注具体交易日期和金额

**输出:** `insider_activity` (str) — 内部人行为分析

### 5. 价格错杀判别 (`_analyze_dislocation`) — V3.5 结构化标签

**逻辑:**
1. 搜索: `{ticker} stock price drop reason recent news` (30 天内)
2. LLM 判断下跌是**真折价 (True Discount)** 还是**假折价 (Fake Discount)**:
   - True Discount: 宏观因素 / 板块轮动导致 → 买入机会
   - Fake Discount: 基本面恶化 / 竞争对手威胁 → 陷阱
3. **V3.5 新增：** LLM 被强制要求在输出开头标注 `[DISCOUNT_TYPE: TRUE_DISCOUNT]` 或 `[DISCOUNT_TYPE: FAKE_DISCOUNT]`，供 Phase 8 Tribunal 程序化解析
4. 要求提供价格变动时间线

**输出:** `dislocation_context` (str) — 包含结构化标签 + 分析文本

---

## Deep Search 预充实 (`_deep_enrich`)

当 `deep_search=True` 时，在执行五大子分析之前：
1. 生成财务搜索矩阵 (Revenue Growth, NDR, CAC, Churn, FCF Margin, 管理层变动)
2. 执行矩阵搜索
3. 运行 Echo Loop 循环验证
4. 将所有深度搜索结果合并到全局 `references`

这一步为后续所有子分析提供更丰富的上下文。

---

## 数据流

```
输入:
  - ticker
  - identifier_data (来自 Phase 1，含 specific_kpis)
  - references (全局引用列表)
  - deep_search (bool)

外部依赖:
  - LLMClient → 所有分析的核心推理引擎
  - SearchClient → 新闻、新闻稿搜索
  - DeepSearchClient → 深度搜索矩阵 + Echo Loop
  - SearchHelper → 统一搜索 + 引用收集

输出:
  - IntelligenceData(
      kpi_values,            # dict[str, str]
      management_integrity,  # str
      product_moat,          # str
      insider_activity,      # str
      dislocation_context    # str
    )
```

---

## 在流水线中的位置

```
[Phase 2: Shadow Audit] → [Phase 3: Intelligence] → [Phase 4: Blue Sky]
```

Intelligence 的输出主要用于：
- Phase 6 (Strategy): `management_integrity` 影响估值调整 (Sandbagger Discount / Over-Promiser Premium)
- Phase 8 (Tribunal): 多项指标汇入最终判决的定性分析
- Report: 直接展示在最终报告的 Intelligence 章节
