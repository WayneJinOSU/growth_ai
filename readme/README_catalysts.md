# Phase 5: Catalysts & Waves (势能与催化)

**文件:** `catalysts.py`
**类:** `CatalystsAnalyzer`
**定位:** 识别推动股价运动的"力"— 区分宏观需求浪潮 (一级催化) 和微观事件 (二级催化)。

---

## 核心理念

> V3.5 的关键修正：**宏观需求 (Macro Need) > 微观事件 (Micro Events)**。一家公司即使没有即将发布的财报，但如果身处不可逆的行业浪潮中，它的势能远大于一个孤立的利好事件。

---

## 三大分析模块

### 模块 1: 一级催化 — 全行业势能 (Thematic Waves)

**核心问题:** 公司是否骑在一个不需要看财报就能感知到的"不可逆刚需"浪潮上？

#### 预定义浪潮模板

| 浪潮 ID | 触发信号 | 受益领域 | 描述 |
|---------|---------|---------|------|
| `labor_shortage_ai` | 劳动力短缺、招聘危机 | AI 自动化、机器人 | 劳动力短缺 → AI 刚需 |
| `geopolitical_defense` | 国防预算、地缘冲突 | 国防、网络安全 | 地缘政治 → 预算溢出 |
| `cloud_migration` | 云迁移、数字化转型 | 云基础设施、SaaS | 云迁移 → 基础设施需求 |
| `ai_infrastructure` | AI 基础设施、GPU 需求 | 半导体、数据中心 | AI 热潮 → 算力瓶颈 |
| `regulatory_compliance` | 监管合规、数据隐私 | GRC 软件、身份管理 | 合规浪潮 → 合规支出 |

**逻辑:**
1. Deep Search (可选): 生成搜索矩阵捕捉宏观浪潮、技术拐点、政策利好
2. 常规搜索: `{company_name} macro tailwind industry trend demand driver recent`
3. LLM 输出结构化结果:
   ```
   WAVE: [浪潮名称或 None]
   STRENGTH: [High / Medium / Low / None]
   RATIONALE: [解释 + 引用]
   ```
4. Strength 标准化映射: `High` / `Medium` / `Low`

**输出:** `thematic_waves` (str), `wave_strength` (str)

### 模块 2: 二级催化 — 硬事件 (Hard Events)

**核心问题:** 未来 6 个月有哪些具体的验证节点？

**逻辑:**
1. 通过 `get_press_releases` 获取官方公告
2. LLM 识别两类事件:
   - **Recently Triggered**: 过去 30 天内的高影响事件 (仍在驱动价格)
   - **Upcoming**: 未来 6 个月的催化事件
3. 事件类型: 财报发布、产品发布/换代、投资者日
4. 每个事件必须附带具体日期或季度
5. 二次 LLM 调用分析催化事件的影响力和预期市场反应

**输出:** `upcoming_events` (list[str]), `catalyst_analysis` (str)

### 模块 3: 预期差 (Variant Perception)

**核心问题:** 华尔街共识与另类数据/现实之间是否存在偏差？

**逻辑:**
1. 搜索: `{ticker} wall street consensus vs reality KPI tracking`
2. LLM 识别市场可能错误定价的方向
3. 要求"挑衅但有数据支撑"的分析风格

**输出:** `variant_perception` (str)

---

## 数据流

```
输入:
  - ticker, company_name
  - references (全局引用列表)
  - deep_search (bool)

外部依赖:
  - LLMClient → 浪潮识别、事件分析、预期差判断
  - SearchClient → 新闻搜索、新闻稿
  - DeepSearchClient → 深度搜索矩阵 (可选)

输出:
  - CatalystData(
      thematic_waves,     # str — 主要浪潮描述
      wave_strength,      # str — "High" / "Medium" / "Low"
      upcoming_events,    # list[str] — 催化事件列表
      catalyst_analysis,  # str — 事件影响分析
      variant_perception  # str — 预期差分析
    )
```

---

## 在流水线中的位置

```
[Phase 4: Blue Sky] → [Phase 5: Catalysts] → [Phase 6: Strategy]
```

Catalysts 的输出直接影响：
- Phase 6 (Strategy): `wave_strength` 和 `upcoming_events` 决定 Catalyst Strength (High/Low)，这是 Executive Matrix 的核心输入之一
- Phase 8 (Tribunal): `wave_strength` 用于 Checklist 的"势能共振"项
- Report: 完整展示在 Catalysts & Waves 章节
