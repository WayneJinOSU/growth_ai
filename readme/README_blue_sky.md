# Phase 4: Blue Sky & Valuation (蓝天展望 & 估值)

**文件:** `blue_sky.py`
**类:** `BlueSkyAnalyzer`
**定位:** 评估公司的"第二增长曲线"潜力，并根据宏观环境动态调整估值模型。

---

## 核心理念

> 一家公司值不值得给溢价，取决于它有没有"蓝天" — 即超越当前业务边界的增长想象空间。Blue Sky 回答两个问题：(1) 有没有第二曲线？(2) 当前宏观环境下，应该给什么倍数？

---

## 两大核心功能

### 功能 1: Blue Sky Analysis — R&D 效能 & TAM 扩张

#### R&D 效能分析 (`rnd_effectiveness`)

**核心问题:** 公司的研发投入是"进攻性 R&D" (如 Amazon 发明 AWS) 还是仅仅维护现有产品？

**逻辑:**
1. 搜索: `{ticker} R&D investment areas new product expansion TAM analysis` (365 天)
2. LLM 分析是否存在明确的"第二增长曲线"
3. 要求列出具体项目、投资金额、预期上线时间

#### TAM 扩张分析 (`tam_expansion`)

**核心问题:** 管理层有没有成功跨行业扩展的历史？TAM 是静态的还是动态的？

**逻辑:**
1. 复用同一批搜索结果
2. LLM 分析 TAM 扩展证据 (新地域、新客户群体、新应用场景)

**输出:** `BlueSkyData(rnd_effectiveness, tam_expansion)`

### 功能 2: Macro-Adjusted Valuation — 宏观动态估值

**核心问题:** 同样一家公司，在不同宏观环境下应该给不同的 PE 倍数。

#### 宏观 PE 调整矩阵

| MacroMode | Bear PE | Target PE | Bull PE | PEG 上限 |
|-----------|---------|-----------|---------|----------|
| `LOOSE` (宽松) | 20x | 30x | 45x | 2.0 |
| `NEUTRAL` (中性) | 18x | 25x | 35x | 1.5 |
| `TIGHT` (紧缩) | 15x | 20x | 25x | 1.2 |

#### 估值计算逻辑

1. 从 FMP 获取当前 Price 和 PE (TTM)
2. 反推 EPS = Price / PE
3. 用宏观调整后的 PE 倍数计算三档目标价:
   - Bear Case = EPS × Bear PE
   - Target = EPS × Target PE
   - Bull Case = EPS × Bull PE
4. 判断当前价格所处区间:
   - < Bear Price → **STRONG BUY ZONE**
   - Bear ~ Target → **BUY ZONE**
   - Target ~ Bull → **HOLD ZONE**
   - > Bull Price → **SELL ZONE**

---

## 数据流

```
输入:
  - ticker
  - gatekeeper_data (来自 Phase 0，含 macro_mode)
  - references (全局引用列表)
  - deep_search (bool)

外部依赖:
  - LLMClient → R&D / TAM 分析
  - SearchClient → 新闻搜索
  - FMPClient → Quote (Price), Ratios (PE TTM)
  - DeepSearchClient → 深度搜索 (可选)

输出:
  - BlueSkyPhaseData(
      blue_sky: BlueSkyData(rnd_effectiveness, tam_expansion),
      macro_valuation_analysis: str  # 完整估值分析文本
    )
```

---

## 在流水线中的位置

```
[Phase 3: Intelligence] → [Phase 4: Blue Sky] → [Phase 5: Catalysts]
```

Blue Sky 的输出直接影响：
- Phase 6 (Strategy): `rnd_effectiveness` / `tam_expansion` 中的关键词触发 Blue Sky Re-Rating，将 PEG 上限从 2.0 放宽到 2.5
- Phase 8 (Tribunal): `blue_sky` 数据用于 Checklist 的"蓝天确认"项
- Report: 估值三档目标价展示在 Macro-Adjusted Valuation 章节
