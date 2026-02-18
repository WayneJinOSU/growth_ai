# Intelligence Module Documentation (`phases/intelligence.py`)

## 1. 模块简介
`intelligence.py` 是 MGP (Macro-Growth-Psychology) 投资策略系统的核心情报处理单元，涵盖了 **Phase 3 (情报收集/软实力)** 和 **Phase 4 (蓝天展望 & 估值)**。

它的主要职责是超越基础财务数据，通过网络搜索和 LLM 分析，收集定性指标（软实力）、评估增长潜力（蓝天分析），并结合宏观环境给出动态估值判断。

> **注意**: 催化剂分析 (Catalysts) 和预期差 (Variant Perception) 已迁移至 `phases/catalysts.py` (Phase 5)，避免与专业催化剂模块的职责重叠。

## 2. 核心逻辑流程

该模块的主要入口是 `gather` 方法，其执行流程如下：

### 2.1 深度搜索预充实 (Deep Search Pre-Enrichment) [可选]
- **触发条件**: 当 `deep_search=True` 时启动。
- **逻辑**:
    1. 调用 `DeepSearchClient` 生成针对关键财务指标（如 Revenue Growth, NRR, CAC 等）的搜索矩阵。
    2. 执行搜索并获取初步结果。
    3. 运行 **Echo Loop (回声循环)**：分析初步结果中的缺口，进行二次针对性搜索。
    4. 生成 `deep_context`，作为后续 KPI 验证的增强上下文。

### 2.2 Phase 3: 软实力情报 (Soft Skills)
此阶段关注企业的定性健康度：

1.  **KPI 验证 (Specific KPIs)**
    - **目的**: 验证 Phase 2 (Identifier) 中识别出的关键特异性指标（如 SaaS 的 NRR, 电商的 GMV）。
    - **方法**: 通过 `_unified_search` 搜索最新季度的财报数据，利用 LLM 精确提取数值和时间戳。

2.  **管理层诚信 (Management Integrity)**
    - **目的**: 判断管理层是"画大饼" (Over-promise) 还是"保守稳健" (Sandbaggers)。
    - **方法**: 分析过去的新闻稿和业绩对比，寻找承诺与兑现的差距。

3.  **护城河分析 (Competitive Moat)**
    - **目的**: 评估竞争优势的动态变化（扩大 vs 缩小）。
    - **方法**: 搜索新产品发布和竞争对手动态。

4.  **内部人交易 (Insider Activity)**
    - **目的**: 捕捉内部人员的信心信号。
    - **方法**: 搜索最近 90 天的内部买卖记录，区分常规行权与机会性买卖。

5.  **价格错杀分析 (Dislocation Context)**
    - **目的**: 判断股价下跌的性质。
    - **逻辑**: 区分 **True Discount** (宏观/板块错杀) 与 **Fake Discount** (基本面恶化)。

### 2.3 Phase 4: 蓝天展望 & 估值 (Blue Sky & Valuation)
此阶段关注未来的增长空间：

1.  **蓝天分析 (Blue Sky Analysis)**
    - **R&D 效能**: 评估研发投入是用于维护现有业务，还是创造"第二增长曲线" (Offensive R&D)。
    - **TAM 扩张**: 分析企业是否有能力跨越现有市场边界 (Total Addressable Market)。

2.  **宏观动态估值 (Macro-Adjusted Valuation) [V3.5]**
    - 系统不再使用静态 PE 进行估值，而是根据 `Gatekeeper` 模块提供的宏观状态 (`MacroMode`) 动态调整估值倍数。

**估值参数矩阵 (`MACRO_PE_ADJUSTMENTS`):**

| 宏观状态 (Macro Mode) | Bear PE (熊市) | Target PE (目标) | Bull PE (牛市) | Max PEG |
| :--- | :--- | :--- | :--- | :--- |
| **LOOSE (宽松)** | 20x | 30x | 45x | 2.0 |
| **NEUTRAL (中性)** | 18x | 25x | 35x | 1.5 |
| **TIGHT (紧缩)** | 15x | 20x | 25x | 1.2 |

**评级逻辑**:
系统结合当前 EPS 和上述倍数计算目标价，并给出评级：
- STRONG BUY: 现价 < Bear Case Price
- BUY: Bear Case < 现价 < Target Price
- HOLD: Target Price < 现价 < Bull Case Price
- SELL: 现价 > Bull Case Price

## 3. 公共工具方法

### `_collect_refs(results, references) -> str`
去重搜索结果并构建带 `[ID]` 引用的上下文字符串。同一 URL 不会重复入库。

### `_unified_search(query, max_results, days, deep_search) -> list`
统一搜索分派：`deep_search=True` 时优先使用 Tavily advanced search，无结果时自动 fallback 到标准搜索。

## 4. 关键类与方法

### `class Intelligence`
- `__init__(...)`: 初始化 LLM, Search, FMP, DeepSearch 客户端。
- `gather(...)`: 主流程控制函数（Phase 3 + Phase 4）。
- `_analyze_blue_sky(...)`: 专门处理 R&D 和 TAM 的子流程。
- `_analyze_macro_adjusted_valuation(...)`: 执行宏观估值计算逻辑。

## 5. 数据结构
输出结果封装在 `IntelligenceData` 对象中，包含：
- `kpi_values`: 验证后的 KPI 字典。
- `management_integrity`: 管理层诚信评估文本。
- `product_moat`: 护城河分析文本。
- `insider_activity`: 内部人交易分析文本。
- `dislocation_context`: 错杀分析文本。
- `blue_sky`: `BlueSkyData` 对象 (R&D, TAM)。
- `catalysts`: 由 Phase 5 (`catalysts.py`) 填充的 `CatalystData` 对象。

## 6. 与 Phase 5 (catalysts.py) 的关系
`intelligence.py` 不再处理催化剂分析。在 `main.py` 的流水线中：
1. Phase 3/4: `Intelligence.gather()` 收集软实力 + 蓝天 + 估值
2. Phase 5: `CatalystsAnalyzer.analyze()` 收集浪潮 + 硬事件 + 预期差
3. Phase 5 的结果覆盖写入 `data.intelligence.catalysts`
