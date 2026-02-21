# Report Generator (报告生成器)

**文件:** `generate_report.py`
**函数:** `generate_report_content_v35(data: CompanyData, lang: str = "en") -> str`
**定位:** 将 CompanyData 中所有 Phase 的结果组装成一份完整的 Markdown 投资报告，支持中英双语输出。

---

## 核心理念

> 报告不做任何新的分析，它只是一面"镜子"— 忠实地将各个 Phase 产出的数据以人类可读的形式呈现出来。

---

## 🌐 双语系统 (Bilingual)

### 使用方式

```bash
python main.py --tickers AXON --lang zh   # 中文报告
python main.py --tickers AXON --lang en   # 英文报告 (默认)
```

### 实现架构

```
config.py REPORT_LANGUAGE          → 默认语言 ("en" | "zh")
main.py --lang                     → CLI 覆盖, 写入 CompanyData.report_language
tools/lang.py                      → get_lang_instruction(data) → LLM prompt 语言指令
phases/*.py                        → 叙事性 LLM prompt 末尾注入语言指令
phases/generate_report.py          → _L("key", lang) 双语标签查找
```

### 标签系统 `_L(key, lang)`

所有报告标题和子标题通过 `_LABELS` 字典统一管理：

```python
_LABELS = {
    "exec_summary":    {"en": "Executive Summary",    "zh": "执行摘要"},
    "mgmt_integrity":  {"en": "Management Integrity", "zh": "管理层诚信"},
    "competitive_moat": {"en": "Competitive Moat",    "zh": "竞争护城河"},
    ...
}

def _L(key: str, lang: str) -> str:
    """Get label in given language, fallback to English."""
```

### LLM 语言注入策略

| 类型 | 注入语言指令? | 原因 |
|:-----|:-------------|:-----|
| 叙事性 LLM 输出 (管理层分析, 护城河, 催化分析) | ✅ YES | 报告中可读的叙述文字 |
| JSON 分类器 (商业模式, Fake Tech, Sandbagging) | ❌ NO | 输出枚举值必须英文以保证解析 |
| 数据提取 (KPI 数值) | ❌ NO | 精确数值提取不受语言影响 |

语言指令由 `tools/lang.py` 统一提供，各 Phase 文件 `from tools.lang import get_lang_instruction`。

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
  - lang: str ("en" | "zh") — 报告语言

外部依赖:
  - tools/lang.py → get_lang_instruction() (供各 Phase 使用)

输出:
  - str — 完整的 Markdown 格式报告文本 (中文或英文)
```

---

## 在流水线中的位置

```
[Phase 8: Tribunal] → [generate_report(lang)] → 写入文件
                                                → report/REPORT_V3.5_{ticker}_{date}.md
```

Report Generator 是流水线的最后一步。`main.py` 在获得 Tribunal 判决后调用此函数，将报告写入 `report/` 目录。

