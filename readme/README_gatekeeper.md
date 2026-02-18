# Phase 0: The Gatekeeper (门槛熔断)

**文件:** `gatekeeper.py`
**类:** `Gatekeeper`
**定位:** MGP V3.5 流水线的第零道关卡 — 在进入任何财报分析之前，先排除"不该玩的赛道"和"不该玩的时间"。

---

## 核心理念

> 不是所有股票都值得花时间分析。Gatekeeper 是一道"宏观 + 行业"级别的过滤器，目标是在 Phase 1 之前就把明显不合适的标的踢掉，节省后续所有 Phase 的计算资源。

---

## 四项核心检查

### 1. 宏观压力阀 (Macro Valve)

根据**美国 10 年期国债收益率 (US10Y)** 判定当前宏观环境：

| 收益率区间 | MacroMode | 含义 |
|-----------|-----------|------|
| < 3.0% | `LOOSE` (宽松) | 资金充裕，成长股友好 |
| 3.0% - 4.5% | `NEUTRAL` (中性) | 正常估值环境 |
| > 4.5% | `TIGHT` (紧缩) | 高利率压制估值，需谨慎 |

此 MacroMode 不会直接导致 Fail，但会传递给下游 Phase 4 (Blue Sky) 用于动态调整 PE 倍数。

### 2. VIX 熔断机制 (VIX Breaker)

- 阈值: VIX > 30 → 标记为**恐慌模式**
- 不直接 Fail，但会在报告中发出 Warning，下游 Phase 8 (Tribunal) 会将其纳入风险评估

### 3. 行业黑名单 (Absolute Blacklist)

从 `config.BLACKLIST_SECTORS` 读取不可验证护城河的行业列表，匹配公司的 `sector` 或 `industry` 字段：
- 命中黑名单 → **直接 Fail**
- 数据来源: FMP Profile API

### 4. 20% 铁律 (Future 20% Iron Rule)

- 通过 Yahoo Finance 获取 3 年预期营收 CAGR
- 若预期增速 < `config.FUTURE_CAGR_THRESHOLD` (默认 20%) → **Fail**
- 数据不可用时跳过此项检查

---

## 数据流

```
输入:
  - ticker (股票代码)

外部依赖:
  - FMPClient → VIX, Company Profile
  - SearchClient → US10Y Treasury Yield
  - YahooClient → Future Growth Estimates

输出:
  - GatekeeperData(
      sector_check_passed,   # bool
      macro_mode,            # MacroMode enum
      us10y_yield,           # float
      vix_value,             # float
      future_revenue_cagr_3y,# float
      passed,                # bool (综合判定)
      fail_reason            # str (失败原因)
    )
```

---

## 在流水线中的位置

```
[Phase 0: Gatekeeper] → Pass → [Phase 1: Deep Audit] → ...
                      → Fail → 终止分析 (除非 force_deep_dive=True 或 Mega Cap > $150B 豁免)
```

Mega Cap ($150B+) 公司即使 Gatekeeper 失败也会强制继续分析，因为大型公司可能有独特的投资逻辑。
