# Deep Search Client (深度搜索指挥官) — Search 2.0

**文件:** `tools/deep_search.py`
**类:** `DeepSearchClient`
**定位:** 独立于 `SearchClient` 的 4 模块智能情报系统。由各 Phase 按需调用，提供定制化的深度搜索能力。

---

## 核心理念

> 普通搜索是"广撒网"，Deep Search 是"定点爆破"。它不只是搜索，而是一个完整的**情报作战链**: 由 LLM 制定搜索策略 → 锁定特定域名执行 → 自动检测信息缺口并补搜 → 最终进行自我对抗验证。

---

## 架构概览

```
DeepSearchClient
├── Module 1: Matrix Generator  (LLM → 搜索指令矩阵)
├── Module 2: Execution          (Tavily → 域名锁定搜索)
├── Module 3: Echo Loop          (LLM → 差距分析 + 补搜循环)
└── Module 4: Adversarial        (LLM → 红蓝对抗验证) [暂未启用]
```

---

## 域名双维度体系

搜索域名由两个正交维度控制，在执行时**取并集**叠加：

### 维度 1: 情报意图 (`DOMAIN_GROUPS`) — "想找什么性质的信息"

| 分组 | 域名 | 适用场景 |
|------|------|---------|
| `HARD_INTEL` | sec.gov, annualreports.com, investor.* | 官方 SEC 文件、年报、投资者关系 |
| `SOFT_INTEL` | reddit.com, teamblind.com, glassdoor.com, trustradius.com | 员工吐槽、内部消息、用户口碑 |
| `EXPERT_INTEL` | stackoverflow.com, github.com, ycombinator.com | 技术实力、开源贡献、行业讨论 |
| `SHORT_SELLER` | muddywatersresearch.com, citronresearch.com, seekingalpha.com | 做空报告、负面分析 |
| `LEGAL` | sec.gov, law360.com, reuters.com, justice.gov | 法律诉讼、SEC 调查 |

### 维度 2: 商业模式 (`DOMAIN_BY_MODEL`) — "该类公司的硬证据在哪"

| 商业模式 | 域名 | 适用场景 |
|---------|------|---------|
| `SaaS` | g2.com, gartner.com, trustradius.com | 企业软件评测、行业报告 |
| `Consumption` | aws.amazon.com, azuremarketplace.microsoft.com, cloud.google.com | 云市场上架情况、用量定价 |
| `Marketplace` | trustpilot.com, reddit.com | 卖家/买家真实评价 |
| `Advertising` | business.tiktok.com | 广告主工具、CPM 趋势 |
| `Hardware` | fccid.io, ifixit.com, digikey.com | FCC 认证、拆解报告、元器件供应 |
| `Gov_B2G` | sam.gov, fpds.gov, usaspending.gov, ted.europa.eu | 政府合同、采购记录 |

### 叠加逻辑

`execute_matrix` 接受可选的 `business_model` 参数。执行搜索时：

```
最终域名 = DOMAIN_GROUPS[intent_group] ∪ DOMAIN_BY_MODEL[business_model]
```

例如，对一家 SaaS 公司搜索 `SOFT_INTEL`：
- 基础域名: reddit.com, teamblind.com, glassdoor.com, trustradius.com
- 叠加 SaaS: g2.com, gartner.com
- 最终: reddit.com, teamblind.com, glassdoor.com, trustradius.com, g2.com, gartner.com

---

## 四大模块详解

### Module 1: Matrix Generator (搜索矩阵生成器)

**入口:** `generate_search_matrix(ticker, company_name, phase_objective)`

**逻辑:**
1. 接收来自各 Phase 的**具体任务目标** (如 "验证假科技和造王者客户")
2. 将目标 + 域名分组规则 + 当前日期注入 Prompt
3. LLM 生成 5-8 条针对性搜索指令，每条指定 query 和 domain_group
4. 输出格式:
   ```json
   [
     {"query": "Intel fake tech fraud accusation", "domain_group": "SOFT_INTEL"},
     {"query": "Intel 10-K major customers revenue", "domain_group": "HARD_INTEL"}
   ]
   ```

**关键规则:**
- 不搜通用信息，只搜能直接验证目标的证据
- 使用"假设已发生"的搜索词 (如搜 "fraud accusation" 而非 "is it fraud")

**Fallback:** LLM 调用失败时，根据目标关键词 (财务/假科技/行业) 使用预设的后备矩阵。

**调用方:** Phase 2 (Shadow Audit), Phase 3 (Intelligence), Phase 5 (Catalysts)

---

### Module 2: Execution (执行模块)

**入口:** `execute_matrix(matrix, business_model=None)`

**逻辑:**
1. 遍历矩阵中的每条搜索指令
2. 根据 `domain_group` 获取情报意图域名列表
3. 如果传入了 `business_model`，将对应的行业域名叠加 (取并集)
4. 调用 Tavily `search_depth="advanced"` + `include_domains` 进行域名锁定搜索
5. 每条指令最多返回 4 条结果
6. 按 URL 去重
7. 为每条结果标记 `source_group` 和原始 `query`
8. 生成带 `[ID]` 编号的格式化上下文字符串 (供 LLM 后续使用)

**Fallback:** Tavily 域名锁定失败时，降级为通用搜索。

**返回:**
- `results`: `List[Dict]` — 原始搜索结果
- `context`: `str` — 格式化文本 (含 [ID] 编号)

---

### Module 3: Echo Loop (回音循环)

**入口:** `run_echo_loop(ticker, initial_results)`

**专用于:** Phase 3 (Intelligence) 的财务数据补全

**必填字段检查列表 (Davis Protocol):**
- Revenue Growth
- Net Dollar Retention (NDR)
- Customer Acquisition Cost (CAC)
- Churn Rate
- FCF Margin
- Management Changes
- Insider Activity
- Competitive Position

**逻辑 (最多 2 轮循环):**
1. 将初始搜索结果构建为上下文
2. **差距分析** (`_identify_gaps`): LLM 判断上下文中缺失哪些必填字段
3. 对每个缺失字段生成补充搜索 query
4. 执行补搜 (每个 gap 最多 2 条结果)
5. 将补搜结果追加到上下文中
6. 重复直到无缺口或达到循环上限

**返回:**
- `extracted_data`: `Dict` — 各字段的搜索状态
- `full_context`: `str` — 完整的上下文 (含补搜内容)

---

### Module 4: Adversarial Review (红蓝对抗) [暂未启用]

**入口:** `adversarial_review(ticker, bullish_thesis)`

**专用于:** Phase 8 (Tribunal) — 目前已在 Tribunal 侧注释掉

**逻辑:**
1. 接收看多论点 (bullish thesis)
2. LLM 生成 3 条攻击性搜索 query (查找欺诈、会计违规、法律纠纷)
3. 在 `LEGAL` 域名组中执行搜索
4. 结果中包含 "fraud" / "investigation" / "lawsuit" → 标记为红旗
5. 有红旗 → `passed: False`，无红旗 → `passed: True`

**Fallback 攻击 queries:**
- `{ticker} fraud investigation`
- `{ticker} accounting scandal`
- `{ticker} short seller report`

---

## 工具函数

### `_clean_json(text)`

从 LLM 响应中清理 JSON：移除 markdown 代码块标记 (` ```json `) 并 strip。

---

## 数据流

```
输入:
  - ticker, company_name, phase_objective (由各 Phase 传入)

内部依赖:
  - SearchClient → Tavily API (域名锁定搜索)
  - LLMClient → Gemini (矩阵生成、差距分析、攻击 query 生成)

输出:
  - Matrix: List[Dict] — 搜索指令矩阵
  - Results: List[Dict] — 搜索结果 (含 url, title, content, source_group)
  - Context: str — 格式化文本 (供 Phase 内 LLM 使用)
  - Adversarial: Dict — {passed: bool, red_flags: list}
```

---

## 各 Phase 的调用方式

| Phase | 调用模块 | 用途 |
|-------|---------|------|
| Phase 2: Shadow Audit | Module 1 + 2 | Fake Tech 验证、King Maker 搜索 |
| Phase 3: Intelligence | Module 1 + 2 + 3 | 财务数据深度采集 + Echo Loop 补漏 |
| Phase 5: Catalysts | Module 1 + 2 | 宏观浪潮、技术拐点、政策利好搜索 |
| Phase 8: Tribunal | Module 4 | 红蓝对抗验证 (暂未启用) |

---

## 使用示例

```python
deep = DeepSearchClient()

# 1. 生成搜索矩阵
matrix = deep.generate_search_matrix("INTC", "Intel", "验证假科技和造王者客户")

# 2. 执行搜索 (传入 business_model 叠加行业专属域名)
results, context = deep.execute_matrix(matrix, business_model="Hardware")

# 3. Echo Loop 补漏 (Phase 3 专用)
extracted, enriched_context = deep.run_echo_loop("INTC", results)
```
