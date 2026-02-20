# Phase 8: The Final Tribunal (最终审判)

**文件:** `tribunal.py`
**类:** `Tribunal`
**定位:** 下单前的最后 60 秒 — 将所有 Phase 的信号压缩成一个明确的"开火/观察/剔除"决策。

---

## 核心理念

> 信息过载是投资的敌人。Tribunal 不是再做新的分析，而是做**最终的裁决** — 一份 6 项 Checklist，全部 Yes 才能开枪。

---

## 60 秒核对清单 (6 Gates)

| # | Gate | 检查内容 | 数据来源 |
|---|------|---------|---------|
| 1 | **Risk Fuse** (风险熔断) | VIX < 30? 宏观稳定? | Phase 0 Gatekeeper |
| 2 | **Audit Passed** (审计通过) | 核心指标健康? 无内幕大额抛售? | Phase 1 Deep Audit |
| 3 | **Blue Sky** (蓝天确认) | 有第二增长曲线或 TAM 扩张? | Phase 4 Blue Sky + Phase 6 Strategy |
| 4 | **Strategic Match** (战略匹配) | Tier 1/2 护城河? 估值合理? | Phase 6 Strategy |
| 5 | **Wave Resonance** (势能共振) | 身处全行业不可逆浪潮? | Phase 5 Catalysts |
| 6 | **Physical Ignition** (物理点火) | 量价信号确认? | Phase 7 Physics |

---

## 决策逻辑 (优先级从高到低) — V3.5 增强

### 一票否决 (TRAP)
- `audit_passed = False` → **TRAP** (High Confidence)

### 趋势破位判断 (V3.5 Fortress 豁免)
- `physics.is_broken_trend = True` 时，进入三级判断：

| 条件 | 结果 | 原因 |
|------|------|------|
| Fortress + True Discount + **VIX < 30** | 🏰 **ACCUMULATE** (Medium) | 左侧建仓机会，真折价 + 深护城河 |
| Fortress + True Discount + **VIX ≥ 30** | ⚠️ **WATCH** (Low) | VIX 安全栓：极端恐慌不接飞刀 |
| 其他情况 | 🚩 **TRAP** (High) | 原始逻辑，破位即熔断 |

> **True Discount 解析：** 从 Phase 3 Intelligence 的 `dislocation_context` 中程序化提取 `[DISCOUNT_TYPE: TRUE_DISCOUNT]` 标签

### 全部通过 (FIRE)
- 6 项全部 Pass → **FIRE** (High Confidence) — 全仓开火

### 战略定义驱动 (Strategic Pricing Override)
当 Phase 6 有 Strategic Definition 且未触发 FIRE/TRAP 时：

| Strategic Definition | Decision | Confidence |
|---------------------|----------|------------|
| 💎 Diamond Setup | CONVICTION BUY | High |
| 🚀 Momentum Ride | SPECULATIVE BUY | Medium |
| 🏰 Fortress Accumulation | ACCUMULATE | Medium |
| ⚰️ Dead Money | WATCH | Low |
| ⏸️ Correction Watch | WATCH | Medium |
| 💣 Short Target | TRAP | High |

### 遗留逻辑 (Legacy)
- Audit Passed + Accumulation Signal → **ACCUMULATE** (Medium)

### 默认
- 以上均不满足 → **WATCH** (Low Confidence)

---

## Deep Search 对抗审查 (Adversarial Review)

当 `deep_search=True` 且决策为 FIRE 或 ACCUMULATE 时，触发红队审查：

1. 将看涨论点提交给 `DeepSearchClient.adversarial_review()`
2. 如果审查未通过 (发现红旗):
   - 决策降级为 **WATCH** (Low Confidence)
   - 红旗记录到 `tribunal_notes`
3. 如果审查通过: 维持原判

---

## LLM Executive Summary

最终由 LLM 生成 3-4 句话的 Executive Summary：
- 直接切入核心洞察 (禁止 "Based on..." 开头)
- 必须包含时间维度 — 为什么是**现在**做这个决策
- 解释论点的预期持续时间或关键窗口
- 截断到 500 字符以内

---

## 数据流

```
输入:
  - data: CompanyData (全部 Phase 结果)
  - strategic_pricing: StrategicPricingData (Phase 6)
  - deep_search: bool

外部依赖:
  - LLMClient → Executive Summary 生成
  - DeepSearchClient → Adversarial Review (可选)

输出:
  - TribunalDecision(
      decision,             # Decision enum (FIRE/TRAP/WATCH/ACCUMULATE/...)
      confidence,           # Confidence enum (High/Medium/Low)
      rationale,            # str — Executive Summary
      checklist_results,    # dict[str, bool] — 6 Gates 的结果
      growth_thesis_intact, # bool
      valuation_fit,        # bool
      is_true_discount      # bool
    )
```

---

## 在流水线中的位置

```
[Phase 7: Physics] → [Phase 8: Tribunal] → 生成报告
```

Tribunal 是整条流水线的终点。它的 `decision` 直接决定：
- 报告封面的 Verdict
- 是否值得写入 Portfolio
- 报告中 60-Second Checklist 的可视化展示
