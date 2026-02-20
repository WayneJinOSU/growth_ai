# Phase 2: The Shadow Audit (影子验证)

**文件:** `shadow_audit.py`
**类:** `ShadowAudit`
**定位:** 在财务数据之外，通过"影子指标"验证公司的真实市场地位。

---

## 核心理念

> 财务报表只告诉你过去，Shadow Audit 通过招聘、客户质量、营销效率等非财务信号，验证"这家公司的生意是不是真的好"。

---

## 四大审计模块

### 模块 1: Fake Tech Detection (假科技检测)

**适用范围:** 所有声称是 Tech 的公司

**逻辑:**
1. 搜索公司在 LinkedIn / 招聘网站的职位信息
2. 如果启用 Deep Search，额外生成搜索矩阵覆盖研发团队规模、核心技术壁垒
3. LLM 分析招聘岗位结构：
   - `REAL_TECH` — 大量招聘 AI/ML/Engineering → 真科技
   - `FAKE_TECH` — 主要招 Sales/Marketing → 假科技 (伪装成科技公司的销售公司)
   - `INCONCLUSIVE` — 数据不足
4. LLM 失败时降级为关键词匹配 Fallback

**输出:** `is_fake_tech` (bool), `linkedin_hiring_audit` (str)

### 模块 2: King Maker Validation (造王者验证) — Path A

**适用范围:** B2B / SaaS / Hardware / Consumption

**逻辑:**
1. 搜索公司与科技巨头 (Apple, Microsoft, Nvidia, Amazon, Google, Meta, Tesla) 及政府/国防机构的合作关系
2. LLM 分析是否存在实质性的"造王者"客户关系
3. LLM 失败时降级为关键词 Fallback

**核心判断:** 有巨头客户背书 → 护城河可信度大幅提升

**输出:** `has_king_maker_clients` (bool), `customer_quality_audit` (str)

### 模块 3: Organic Growth Validation (自然增长验证) — Path B (V3.5 增强)

**适用范围:** B2C / Marketplace / Advertising / **SaaS** (V3.5 新增)

**逻辑:**
1. 拉取 3 年年度 Income Statement
2. 计算 S&M (Sales & Marketing) 占营收比例的变化趋势：
   - S&M% 持平或下降 + 营收增长 → `organic_growth_confirmed = True`
   - S&M% 上升 → 进入 SaaS 豁免检查
3. **V3.5 SaaS 效率豁免：** 对于 SaaS 公司，如果 S&M 绝对支出增加但**营收增速 > S&M 增速**，视为"高效扩张"而非"买来的增长"
4. 补充检查 App Store 排名 (搜索模拟)

**输出:** `organic_growth_confirmed` (bool), `marketing_efficiency` (str)

### 模块 4: Sandbagging Detection (管理层沙袋检测)

**适用范围:** 所有公司

**逻辑:**
1. 通过 `get_press_releases` 获取最近 5 条官方公告/财报
2. LLM 分析管理层是否有"扮猪吃虎"行为：
   - 保守指引但实际持续 Beat & Raise
   - 强劲 RPO/Backlog 但对外口径谨慎
3. 结果: `SANDBAGGING_DETECTED` (看涨信号) / `NO_SANDBAGGING` / `INCONCLUSIVE`

**输出:** `sandbagging_detected` (bool), `sandbagging_details` (str)

---

## 路径选择逻辑

```
所有公司 → 模块 1 (Fake Tech)
         → 模块 4 (Sandbagging)

B2B/SaaS/HW → 模块 2 (King Makers) — Path A
B2C/Marketplace/SaaS → 模块 3 (Organic Growth) — Path B  # V3.5: SaaS 同时走 Path A + B
```

---

## 数据流

```
输入:
  - ticker, company_name
  - business_model (来自 Phase 1 的 IdentifierData)
  - references (全局引用列表，累加)
  - deep_search (bool)

外部依赖:
  - SearchClient → 招聘信息搜索、新闻稿、App Store
  - FMPClient → Income Statement (S&M 效率)
  - LLMClient → Fake Tech 判定、King Maker 验证、Sandbagging 检测
  - DeepSearchClient → 深度搜索矩阵 (可选)

输出:
  - ShadowAuditData(
      linkedin_hiring_audit, is_fake_tech,
      has_king_maker_clients, customer_quality_audit,
      organic_growth_confirmed, marketing_efficiency,
      sandbagging_detected, sandbagging_details,
      app_store_rank
    )
```

---

## 在流水线中的位置

```
[Phase 1: Deep Audit] → [Phase 2: Shadow Audit] → [Phase 3: Intelligence]
```

Shadow Audit 不设硬性 Pass/Fail，但其输出直接影响：
- Phase 6 (Strategy): `has_king_maker_clients` (B2B) 或 `organic_growth_confirmed` + `app_store_rank` (B2C) 决定 Tier 1 vs Tier 2/3
- Phase 6 (Strategy): `sandbagging_detected` 触发估值折价
- Phase 8 (Tribunal): `is_fake_tech` 可能导致降级
