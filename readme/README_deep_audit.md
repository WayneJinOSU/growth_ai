# Phase 1: The Deep Audit (深度审计)

**文件:** `deep_audit.py`
**类:** `DeepAudit`
**定位:** MGP V3.5 的第一道核心关卡 — 针对不同商业模式进行"核磁共振"级别的财务体检。

---

## 核心理念

> 不同商业模式有不同的"物理法则"。SaaS 看 NDR，硬件看库存周转，Marketplace 看 Take Rate。Deep Audit 先识别公司 DNA，再按对应协议执行审计。

---

## 两大职责

### 职责 A: 商业模式识别 (`identify_business_model`)

通过 **规则 + LLM** 双通道判定公司属于哪种商业模式：

| BusinessModel | 典型公司 | 核心 KPI |
|--------------|---------|---------|
| `SaaS` | CrowdStrike, Datadog | NDR, RPO, Billings |
| `Consumption` | Snowflake, AWS | Rule of 40, FCF Margin |
| `Marketplace` | Uber, Airbnb | Take Rate, GMV |
| `Advertising` | Meta, Google | ARPU, DAU/MAU |
| `Hardware` | Nvidia, Apple | Inventory Days, Book-to-Bill |
| `Other` | 无法归类 | 通用指标 |

**快速路径:** 先用 FMP Profile 中的 `industry` / `sector` / `description` 做规则匹配。
**精准路径:** 规则不明确时，调用 LLM 进行语义分类。

### 职责 B: 深度审计 (`analyze`)

分为四个审计层级：

#### 层级 1: 历史增长 & 财务卫生 (V3.5 Enhanced)

| 指标 | 计算方式 | 说明 |
|------|---------|------|
| Revenue CAGR (N-Year) | `(Latest / Oldest)^(1/N) - 1` | 年化复合增长率 |
| **EPS CAGR (N-Year)** | 同上，基于 EPS | V3.5 新增：盈利杠杆验证 |
| Q/Q Revenue Growth | `(Current Q - YoY Q) / YoY Q` | 季度同比增速 |
| **Net Dilution** | `(今年 weightedAverageShsOutDil - 去年) / 去年` | V3.5：用 FMP 真实股本替代 SBC 绝对值，>5% 触发红旗 |
| SBC / Revenue (Fallback) | `TTM SBC / TTM Revenue` | 仅当股本数据不可用时使用 |

#### 层级 2: 细分领域审计 (V3.5 — Tavily + LLM 提取)

- **SaaS:** NDR (净收入留存率) — 通过 Tavily 搜索最近季度财报/电话会议，LLM 提取 NDR 数值，与 `config.NDR_THRESHOLD` (110%) 比较
- **SaaS:** RPO Growth (剩余履约义务增速) — 同上路径提取，验证"订单蓄水池"是否在扩大
- **Consumption/SaaS:** Rule of 40 = `Rev Growth + FCF Margin`
- **Hardware:** Inventory Death Cross = 库存天数上升 + 毛利率下降
- **Hardware:** Book-to-Bill Ratio — 通过 Tavily 搜索 Bookings/Orders 数据，LLM 提取，> 1.0 表示供不应求
- **Marketplace:** Take Rate Trend — 通过 Tavily 搜索 Take Rate / GMV 数据，LLM 提取并检测"Take Rate Trap"（变现率↑但GMV↓）

#### 层级 3: 全局测谎仪 (Universal Lie Detector — V3.5 增强)

| 检测项 | 逻辑 | V3.5 变更 |
|--------|------|------|
| CFO Divergence | NI 增长 > 20% 但 CFO 下降 | **需连续 2 季度或 TTM 成立**，单季度不触发 |
| Insider Selling | Yahoo Insider TX 中 Sell > 3 笔 | **降级为红旗**，不再直接 Fail |

#### 层级 4: Pass/Fail 判定 (V3.5 Red Flag System)

**V3.5 核心改动：** 不再"一触即死"，改为**红旗累积制**。红旗 ≥ 2 才硬性熔断。

| 触发项 | 红旗数 | 豁免条件 |
|--------|--------|----------|
| 低增长 (CAGR/Q-Growth) | +1 | Rule of 40 > 40% 或 EPS CAGR > 20% 可豁免 |
| 净稀释率 > 5% YoY | +1 | — |
| CFO Divergence (TTM/连续) | +1 | — |
| Insider Selling > 3 笔 | +1 | — |
| Inventory Death Cross | **+2** | 直接触发 Fail |

- 红旗 = 0 → **PASSED**
- 红旗 = 1 → **PASSED (with Warning)**
- 红旗 ≥ 2 → **FAILED**

---

## 数据流

```
输入:
  - ticker
  - identifier_data (可选，不传则内部自动识别)

外部依赖:
  - FMPClient → Income Statement, Cash Flow, Balance Sheet, Profile
  - YahooClient → Insider Roster
  - LLMClient → 商业模式分类 + 非 GAAP 指标提取
  - SearchClient (Tavily) → 搜索财报/电话会议文本 (NDR, RPO, Book-to-Bill, Take Rate)

输出:
  - IdentifierData(business_model, specific_kpis, bear_case_hook)
  - DeepAuditData(
      revenue_cagr_ny, revenue_growth_current_q,
      sbc_revenue_ratio, rule_of_40, inventory_health,
      ndr, rpo_growth, book_to_bill, take_rate_trend,
      insider_selling_risk,
      passed, fail_reason
    )
```

---

## 在流水线中的位置

```
[Phase 0: Gatekeeper] → [Phase 1: Deep Audit] → Pass → [Phase 2: Shadow Audit] → ...
                                                → Fail → 终止 (除非 force / Mega Cap)
```

Deep Audit 的 `passed` 状态会直接影响下游 Phase 6 (Strategy) 的 Tier 分级和 Phase 8 (Tribunal) 的最终判决。
