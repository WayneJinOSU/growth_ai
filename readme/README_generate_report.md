# Report Generator (报告生成器)

**文件:** `generate_report.py`
**函数:** `generate_report_content_v35(data: CompanyData) -> str`
**定位:** 将 CompanyData 中所有 Phase 的结果组装成一份完整的 Markdown 投资报告。

---

## 核心理念

> 报告不做任何新的分析，它只是一面"镜子"— 忠实地将各个 Phase 产出的数据以人类可读的形式呈现出来。

---

## 报告结构 (章节顺序)

| 章节 | 对应 Phase | 内容 |
|------|-----------|------|
| **Header** | — | Ticker, Date, Verdict, Strategic Definition, Physics Signal, Price |
| **Executive Summary** | Phase 8 | Tribunal 生成的 3-4 句话总结 |
| **Phase 0: Gatekeeper** | Phase 0 | Macro Mode, US10Y, VIX, Sector Check, 20% Rule |
| **Phase 1: Deep Audit** | Phase 1 | Pass/Fail + 详细指标表格 (CAGR, SBC, Rule of 40, Inventory 等) |
| **Phase 2: Shadow Audit** | Phase 2 | King Makers, Organic Growth, Fake Tech + 各模块详情 |
| **Phase 3: Intelligence** | Phase 3 | Management Integrity, Competitive Moat, Insider Activity |
| **Phase 4: Blue Sky** | Phase 4 | TAM Expansion, R&D Second Curve |
| **Phase 5: Catalysts** | Phase 5 | Thematic Wave + Strength, Hard Events 列表, Catalyst Analysis |
| **Phase 6: Strategy** | Phase 6 | Valuation Scrub, Fortress Test, Blue Sky Re-Rating, Executive Matrix 表格 |
| **Phase 7: Physics** | Phase 7 | 技术指标表格 + Signal Analysis 表格 + AI Physical Dynamics (如有) |
| **Phase 8: Tribunal** | Phase 8 | 60-Second Checklist (6 Gates 可视化) + Macro-Adjusted Valuation |
| **References** | 全局 | 去重后的引用源列表，格式 `[ID] [Title](URL)` |
| **Appendix** | — | 核心术语表 (CAGR, NDR, RPO, PEG, Sandbagging, Ignition 等) |

---

## 关键实现细节

### 状态图标映射

| 条件 | 图标 |
|------|------|
| Physics: Ignition | 🚀 IGNITION |
| Physics: Accumulation | 🔋 ACCUMULATION |
| Physics: Broken Trend | ⚠️ BROKEN TREND |
| Checklist: Pass | ✅ |
| Checklist: Fail | ❌ |
| Insider Selling Risk | ⚠️ YES |

### 引用去重

使用 `seen_urls` set 对全局 references 进行 URL 级别去重，避免同一来源被重复列出。

### 空值处理

每个章节均处理数据缺失的情况：
- `data.deep_audit` 为 None → 显示 "Failed" 或 "N/A"
- 数值为 None → 显示 "N/A" 而非报错
- 使用大量 `if data.xxx:` 防御性检查

---

## 数据流

```
输入:
  - data: CompanyData (包含所有 Phase 的结果)

外部依赖:
  - 无 (纯数据格式化)

输出:
  - str — 完整的 Markdown 格式报告文本
```

---

## 在流水线中的位置

```
[Phase 8: Tribunal] → [generate_report] → 写入文件
                                         → report/REPORT_V3.5_{ticker}_{date}.md
```

Report Generator 是流水线的最后一步。`main.py` 在获得 Tribunal 判决后调用此函数，将报告写入 `report/` 目录。
