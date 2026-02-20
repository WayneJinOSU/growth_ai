# Phase 6: Strategic Pricing (战略定价)

**文件:** `strategy.py`
**类:** `StrategyAnalyzer`
**定位:** 将所有定性情报转化为定量的操作指令 — 逻辑的终点，行动的起点。

---

## 核心理念

> 前 5 个 Phase 收集了海量信息，但投资决策需要"一句话答案"。Strategy 就是那个把所有信号压缩成一个可执行指令的引擎。

---

## 四步定价流程

### Step 1: Valuation Scrub (估值清洗)

**核心问题:** 管理层是"扮猪吃虎"还是"画饼充饥"？

**逻辑:**
1. 检查 Phase 2 (Shadow Audit) 的 `sandbagging_detected`
2. 检查 Phase 3 (Intelligence) 的 `management_integrity` 文本:
   - 包含 "sandbag" / "conservative" → **Sandbagger**
   - 包含 "over-promis" / "miss" → **Over-Promiser**
3. 调整方向:
   - Sandbagger → PE 折价 -20% (实际盈利能力被低估，看涨)
   - Over-Promiser → PE 溢价 +20% (风险溢价)

**输出:** `adjusted_pe`, `adjustment_reason`

### Step 2: Fortress Test (底仓资格认证)

**核心问题:** 这家公司的护城河有多深？值不值得长期持有？

**逻辑:**

| 条件 | Tier | 含义 |
|------|------|------|
| Phase 1 Passed + (King Makers 巨头背书 或 Organic Growth + App Store Dominance) | **Tier 1** | 深护城河 (B2B的生态锚点 或 B2C的自然增长霸主) |
| Phase 1 Passed 但缺乏上述强护城河信号 | **Tier 2** | 基本面健康但缺乏战略验证 |
| Phase 1 Failed | **Tier 3** | 弱护城河或基本面有问题 |

**输出:** `tier_level` (TierLevel), `tier_rationale`

### Step 3: Blue Sky Re-Rating (蓝天重定价)

**核心问题:** 有第二增长曲线吗？值得放宽估值容忍度吗？

**逻辑:**
1. 提取 Phase 4 (Blue Sky) 生成的 `is_strong_second_curve` 结构化布尔值标志
2. 若为 True → Blue Sky Triggered:
   - PEG 上限从 **2.0 放宽到 2.5**

**输出:** `blue_sky_triggered` (bool), `peg_limit` (float)

### Step 4: Executive Matrix (最终决策矩阵)

**核心问题:** 综合所有信号，应该怎么做？

#### 输入维度

| 维度 | 来源 | 取值 |
|------|------|------|
| Catalyst Strength | Phase 5 wave_strength + upcoming_events | High / Low |
| Valuation Status | Phase 1 PEG vs peg_limit | Green (便宜) / Red (贵) |
| Tier Level | Step 2 | Tier 1 / 2 / 3 |

> **V3.5 SaaS 豁免：** 若 `BusinessModel = SaaS/Consumption` 且 `Rule of 40 ≥ 50%`，即使 PEG 超限，Valuation Status 仍强制为 **Green**。

#### 决策矩阵

| Catalyst | Valuation | Tier | Strategic Definition | Action |
|----------|-----------|------|---------------------|--------|
| High | Green | Tier 1 | 💎 **Diamond Setup** | 完美击球区，激进买入 |
| High | Green | Tier 2/3 | 🚀 **Momentum Ride** | 催化剂覆盖弱护城河，纯动量右侧投机 |
| High | Red | Any | 🚀 **Momentum Ride** | 动量覆盖估值，右侧追入 |
| Low | Green | Tier 1 | 🏰 **Fortress Accumulation** | 深护城河便宜货，左侧建仓 |
| Low | Green | Tier 2/3 | ⚰️ **Dead Money** | 便宜但平庸，仅观察 |
| Low | Red | Tier 1 | ⏸️ **Correction Watch** | 贵+无催化，不做空 Tier 1，等回调 |
| Low | Red | Tier 2/3 | 💣 **Short Target** | 无护城河+无催化+高估值，做空候选 |

**输出:** `catalyst_strength`, `valuation_status`, `strategic_definition`, `action_instruction`

---

## 数据流

```
输入:
  - data: CompanyData (包含所有前序 Phase 结果)
  - catalyst_data: CatalystData (Phase 5，可选)

外部依赖:
  - 无外部 API 调用 (纯逻辑聚合)

输出:
  - StrategicPricingData(
      adjusted_pe, adjustment_reason,
      tier_level, tier_rationale,
      blue_sky_triggered, peg_limit,
      catalyst_strength, valuation_status,
      strategic_definition, action_instruction
    )
```

---

## 在流水线中的位置

```
[Phase 5: Catalysts] → [Phase 6: Strategy] → [Phase 7: Physics]
```

Strategy 是整个分析链的"逻辑枢纽":
- **汇聚:** Phase 1 (Audit) + Phase 2 (Shadow) + Phase 3 (Intelligence) + Phase 4 (Blue Sky) + Phase 5 (Catalysts) 的全部信号
- **输出:** `strategic_definition` 直接被 Phase 8 (Tribunal) 用于最终判决的核心决策逻辑
