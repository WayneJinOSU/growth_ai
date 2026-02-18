# Phase 7: The Physics of VPA (量价物理学)

**文件:** `physics.py`
**类:** `Physics`
**定位:** 用物理学类比解读量价关系，捕捉机构资金进场/离场的瞬间信号。

---

## 核心理念

> 废弃滞后指标 (MACD, RSI 等)，回归最原始的量价本质。均线铁律: **SMA20 是生命线 — 线下不买，线上不卖。**

---

## 技术指标计算

基于 FMP 历史日线 OHLCV 数据 (90 天窗口)，本地计算：

| 指标 | 公式 | 说明 |
|------|------|------|
| SMA 20 | 20 日收盘价简单移动平均 | 生命线 |
| RVol | `当日成交量 / 20 日平均成交量` | 相对成交量，衡量资金活跃度 |
| Daily Range | `(High - Low) / Open` | 日内振幅 |
| Close Strength | `(Close - Low) / (High - Low)` | 收盘位置强度 (1.0 = 收在最高) |

---

## 三大核心形态

### 1. Accumulation 📦 (吸筹)

**物理类比:** 底部横盘，弹簧被压缩

**触发条件:**
- `Daily Range < config.ACCUMULATION_RANGE_PCT` (振幅极小)
- `RVol > config.RVOL_ACCUMULATION` (成交量异常放大)

**含义:** 价格不动但有大资金在安静建仓 — 蓄力阶段

### 2. Ignition 🚀 (点火)

**物理类比:** 火箭点火，能量爆发

**触发条件 (全部满足):**
- `Close > SMA20` (突破生命线)
- `Close > Open` (收阳)
- `Close Strength > 0.7` (收在日内高位区)
- `RVol > config.RVOL_IGNITION` (巨量)

**含义:** 机构资金大举入场，动量启动 — 最强买入信号

### 3. Broken Trend 📉 (破位)

**物理类比:** 结构崩塌，地基被抽走

**触发条件:**
- 最近 3 个交易日中，`Close < SMA20` 的天数 ≥ 3

**含义:** 趋势死亡，不要接飞刀 — 最强卖出/回避信号

---

## AI 物理动力学分析 (V3.5 扩展)

当 LLMClient 可用时，额外执行 AI 增强分析：

**输入:** 90 天原始 OHLCV JSON 数据

**分析框架:**
1. **运动学 (Kinematics):** 趋势、速度、加速度、动量
2. **动力学 (Dynamics):** 成交量作为质量/惯性，买卖双方力量对比
3. **静力学 (Statics):** 支撑位/阻力位 (地板与天花板)
4. **能量守恒 (VWAP/Deviation):** 过度延伸还是均值回归

**LLM 输出:**
- `CONCLUSION`: Ignition / Broken Trend / Accumulation / Divergence / Volatility Trap / Neutral
- `RECOMMENDATION`: Strong Buy / Buy / Wait / Observe / Sell
- `ANALYSIS`: 用物理学隐喻的详细分析

**信号对齐:** 如果 AI 结论检测到特定信号 (如 "Ignition")，会覆盖/补充技术指标的判定。

---

## 数据流

```
输入:
  - ticker

外部依赖:
  - FMPClient → Historical Daily OHLCV (90 天)
  - LLMClient → AI 物理动力学分析 (可选)

输出:
  - PhysicsData(
      sma_20, current_price,
      relative_volume, daily_range, close_strength,
      days_below_sma20,
      is_accumulation, is_ignition, is_broken_trend, is_high_risk,
      ai_analysis, ai_conclusion, ai_recommendation,
      details
    )
```

---

## 在流水线中的位置

```
[Phase 6: Strategy] → [Phase 7: Physics] → [Phase 8: Tribunal]
```

Physics 的输出直接影响 Phase 8 (Tribunal):
- `is_ignition` → Checklist "Physical Ignition" 项
- `is_broken_trend` → 直接触发 TRAP 判决 (覆盖其他信号)
- `is_accumulation` → 可能触发 ACCUMULATE 判决
- AI 结论作为辅助参考展示在报告中
