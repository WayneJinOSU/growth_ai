"""
Mahaney Growth Protocol (MGP) V3.4 - Main Entry Point
======================================================
"反脆弱全景套利"系统 - 针对 $10B-$50B 中大盘成长股

V3.4 流水线:
- Phase 0: Gatekeeper (宏观压力阀 + VIX 熔断 + 行业过滤)
- Phase 1: Iron Gate (财务卫生检查)
- Phase 2: Identifier + Shadow Audit + Polygraph (DNA识别 + 影子审计 + 测谎)
- Phase 3: Intelligence (情报收集 + 宏观调整估值)
- Phase 4: Tribunal (最终审判 + 紧急弹射检测)
"""

import argparse
import json
from datetime import datetime

from phases.gatekeeper import Gatekeeper
from phases.iron_gate import IronGate
from phases.identifier import Identifier
from phases.intelligence import Intelligence
from phases.tribunal import Tribunal

from tools.fmp import FMPClient
from tools.llm import LLMClient
from tools.search import SearchClient
from core.data_models import CompanyData, Decision


def translate_report(llm: LLMClient, report_content: str) -> str:
    """
    使用 AI 将英文报告翻译为中文，保持原有的 Markdown 结构
    """
    prompt = f"""
请将以下投资分析报告翻译成中文。要求：
1. 保持原有的 Markdown 格式结构（标题、列表、分隔线等）
2. 专业术语翻译准确（如 CAGR=复合年均增长率，PEG=市盈率相对盈利增长比率）
3. 数字、股票代码、日期保持原样
4. 翻译要流畅专业，符合金融分析报告的语言风格

原文：
{report_content}

请直接输出翻译后的中文报告，不要添加任何解释说明：
"""

    system_prompt = "你是一位专业的金融翻译，擅长将英文投资研报翻译成地道的中文。"
    translated = llm.analyze_text(prompt, system_prompt)
    return translated.strip()


def analyze_ticker_v34(ticker: str, fmp: FMPClient, llm: LLMClient, search: SearchClient,
                       force_deep_dive: bool = False) -> CompanyData:
    """
    V3.4 完整分析流水线
    """
    print(f"\n{'='*60}")
    print(f"  MGP V3.4 Analysis: {ticker}")
    print(f"{'='*60}")
    
    data = CompanyData(ticker=ticker)

    # 获取基础信息
    quote = fmp.get_quote(ticker)
    profile = fmp.get_profile(ticker)
    if quote:
        data.company_name = quote.get('name')
        data.current_price = quote.get('price')
        data.market_cap = quote.get('marketCap')
    
    print(f"  Company: {data.company_name}")
    print(f"  Price: ${data.current_price:.2f}" if data.current_price else "  Price: N/A")
    print(f"  Market Cap: ${data.market_cap/1e9:.1f}B" if data.market_cap else "  Market Cap: N/A")
    
    # ========== Phase 0: Gatekeeper (V3.4 New) ==========
    print(f"\n[{ticker}] Phase 0: Gatekeeper (V3.4)...")
    gatekeeper = Gatekeeper(fmp, search)
    data.gatekeeper = gatekeeper.analyze(ticker)
    
    if not data.gatekeeper.passed:
        print(f"[{ticker}] ❌ Failed Gatekeeper: {data.gatekeeper.fail_reason}")
        if not force_deep_dive:
            data.error = f"Gatekeeper Failed: {data.gatekeeper.fail_reason}"
            return data
        print(f"[{ticker}] Proceeding despite Gatekeeper failure (Force Mode).")
    else:
        print(f"[{ticker}] ✓ Gatekeeper Passed | Macro: {data.gatekeeper.macro_mode.value}")

    # ========== Phase 1: Iron Gate ==========
    print(f"\n[{ticker}] Phase 1: Iron Gate...")
    ig = IronGate(fmp)
    data.iron_gate = ig.analyze(ticker)

    if not data.iron_gate.passed:
        print(f"[{ticker}] ❌ Failed Iron Gate: {data.iron_gate.fail_reason}")
        if not force_deep_dive:
            data.error = f"Iron Gate Failed: {data.iron_gate.fail_reason}"
            return data
        print(f"[{ticker}] Proceeding despite Iron Gate failure (Force Mode).")
    else:
        print(f"[{ticker}] ✓ Iron Gate Passed")

    # ========== Phase 2: Identifier + Shadow Audit + Polygraph (V3.4) ==========
    print(f"\n[{ticker}] Phase 2: Identifier + Shadow Audit + Polygraph...")
    
    # Initialize Identifier with all clients for V3.4
    ident = Identifier(llm, fmp, search)
    
    # 2a. Business Model Identification
    description = profile['description'] if profile else "Technology company"
    print(f"    - Description length: {len(description)} characters")
    data.identifier = ident.identify(ticker, description)
    print(f"    - Business Model: {data.identifier.business_model.value}")
    
    # 2b. Shadow Audit (V3.4)
    company_name = data.company_name or ticker
    data.shadow_audit = ident.shadow_audit(ticker, company_name)
    
    # 2c. Polygraph (V3.4)
    # 获取季度财务数据用于测谎
    income_quarterly = fmp.get_income_statement(ticker, period='quarter', limit=8)
    cash_flow_quarterly = fmp.get_cash_flow_statement(ticker, period='quarter', limit=8)
    # 使用 Tavily 定向搜索官方新闻稿 (替代 FMP Press Releases 接口)
    press_releases = search.get_press_releases(ticker, company_name, limit=10)
    
    data.polygraph = ident.polygraph(ticker, income_quarterly, cash_flow_quarterly, press_releases)
    
    # 检查测谎结果
    if data.polygraph and not data.polygraph.cash_flow_divergence_check:
        print(f"[{ticker}] ⚠️ Polygraph Warning: Cash Flow Divergence detected!")

    # ========== Phase 3: Intelligence + Macro-Adjusted Valuation (V3.4) ==========
    print(f"\n[{ticker}] Phase 3: Intelligence + Macro Valuation...")
    intel = Intelligence(llm, search, fmp)
    data.intelligence = intel.gather(ticker, data.identifier, data.gatekeeper)
    print(f"    - Intelligence complete. Found {len(data.intelligence.kpi_values)} KPI values.")

    # ========== Phase 4: Tribunal + Emergency Eject (V3.4) ==========
    print(f"\n[{ticker}] Phase 4: The Tribunal (V3.4)...")
    tribunal = Tribunal(llm, fmp)
    
    # 使用 Tavily 搜索最新新闻用于紧急弹射检测
    stock_news = fmp.get_stock_news(ticker, limit=20)
    
    data.tribunal = tribunal.judge(data, news=stock_news)
    
    print(f"\n{'='*60}")
    print(f"  FINAL VERDICT: {data.tribunal.decision.value}")
    print(f"  Confidence: {data.tribunal.confidence.value}")
    print(f"{'='*60}")

    return data


def clean_report_content(text: str) -> str:
    """清洗报告内容，移除冗余标题和过渡性废话"""
    if not text:
        return ""
    
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('#') and ('Analysis' in stripped or 'Summary' in stripped or 'Conclusion' in stripped):
            continue
        if stripped.lower().startswith('based on the provided'):
            continue
        cleaned_lines.append(line)
        
    return '\n'.join(cleaned_lines).strip()


def format_kpis_to_markdown(kpis: dict) -> str:
    """将 KPI 字典转换为 Markdown 表格"""
    if not kpis:
        return "N/A"
    
    table = "| KPI | Value |\n| :--- | :--- |\n"
    for k, v in kpis.items():
        clean_v = str(v).replace('\n', ' ').strip()[:200]
        table += f"| {k} | {clean_v} |\n"
    
    return table


def generate_report_content_v34(data: CompanyData) -> str:
    """生成 V3.4 格式的报告内容"""
    timestamp = datetime.now().strftime("%Y-%m-%d")

    # 安全获取数据
    price_str = f"${data.current_price:.2f}" if data.current_price else "N/A"
    market_cap_str = f"${data.market_cap / 1e9:.2f}B" if data.market_cap else "N/A"
    
    # Iron Gate 数据
    cagr_str = f"{data.iron_gate.revenue_cagr_ny:.1%}" if data.iron_gate and data.iron_gate.revenue_cagr_ny is not None else "N/A"
    q_growth_str = f"{data.iron_gate.revenue_growth_current_q:.1%}" if data.iron_gate and data.iron_gate.revenue_growth_current_q is not None else "N/A"
    peg_str = f"{data.iron_gate.peg_ratio:.2f}" if data.iron_gate and data.iron_gate.peg_ratio else "N/A"
    sbc_str = f"{data.iron_gate.sbc_revenue_ratio:.1%}" if data.iron_gate and data.iron_gate.sbc_revenue_ratio is not None else "N/A"
    
    # Gatekeeper 数据 (V3.4)
    macro_mode = data.gatekeeper.macro_mode.value if data.gatekeeper else "N/A"
    us10y = f"{data.gatekeeper.us10y_yield:.2f}%" if data.gatekeeper and data.gatekeeper.us10y_yield else "N/A"
    vix = f"{data.gatekeeper.vix_value:.1f}" if data.gatekeeper and data.gatekeeper.vix_value else "N/A"
    
    # Shadow Audit 数据 (V3.4)
    fake_tech_status = "⚠️ Warning" if data.shadow_audit and data.shadow_audit.is_fake_tech else "✓ Pass"
    king_maker_status = "✓ Yes" if data.shadow_audit and data.shadow_audit.has_king_maker_clients else "No"
    
    # Polygraph 数据 (V3.4)
    cfo_check = "✓ Pass" if data.polygraph and data.polygraph.cash_flow_divergence_check else "⚠️ DIVERGENCE"
    sandbagging = "✓ Detected (Bullish)" if data.polygraph and data.polygraph.sandbagging_detected else "Not Detected"

    # 清洗各部分文本
    rationale_cleaned = clean_report_content(data.tribunal.rationale) if data.tribunal else "N/A"
    variant_perception = clean_report_content(data.intelligence.catalysts.variant_perception) if data.intelligence and data.intelligence.catalysts else "N/A"
    rnd_effectiveness = clean_report_content(data.intelligence.blue_sky.rnd_effectiveness) if data.intelligence and data.intelligence.blue_sky else "N/A"
    tam_expansion = clean_report_content(data.intelligence.blue_sky.tam_expansion) if data.intelligence and data.intelligence.blue_sky else "N/A"
    
    mgmt_integrity = clean_report_content(data.intelligence.management_integrity) if data.intelligence else "N/A"
    product_moat = clean_report_content(data.intelligence.product_moat) if data.intelligence else "N/A"
    insider_activity = clean_report_content(data.intelligence.insider_activity) if data.intelligence else "N/A"
    dislocation = clean_report_content(data.intelligence.dislocation_context) if data.intelligence else "N/A"
    
    kpi_table = format_kpis_to_markdown(data.intelligence.kpi_values) if data.intelligence else "N/A"

    # 决策图标
    decision_icon = {
        Decision.TACTICAL_SNIPER: "⚔️",
        Decision.STRATEGIC_COMPOUNDER: "🏰",
        Decision.TRAP: "💣",
        Decision.CONVICTION_BUY: "🚀",
        Decision.ACCUMULATE: "📈",
        Decision.SPECULATIVE_BUY: "🎲",
        Decision.VALUE_TRAP: "⚠️",
        Decision.WATCH: "👀",
        Decision.SKIP: "🚫",
    }.get(data.tribunal.decision if data.tribunal else None, "")

    report_content = f"""# MGP V3.4 Analysis: {data.ticker} {decision_icon}
**Date:** {timestamp}
**Verdict:** {data.tribunal.decision.value if data.tribunal else 'N/A'} ({data.tribunal.confidence.value if data.tribunal else 'N/A'} Confidence)
**Price:** {price_str} | **Market Cap:** {market_cap_str}

## Executive Summary
{rationale_cleaned}

---

## 1. Macro Environment (V3.4 Gatekeeper)
| Metric | Value | Status |
| :--- | :--- | :--- |
| **US 10Y Yield** | {us10y} | Macro Mode: **{macro_mode}** |
| **VIX** | {vix} | {"⚠️ PANIC MODE" if data.gatekeeper and data.gatekeeper.vix_value and data.gatekeeper.vix_value > 30 else "Normal"} |
| **Sector Check** | {data.gatekeeper.sector_check_passed if data.gatekeeper else 'N/A'} | {"✓ Whitelisted" if data.gatekeeper and data.gatekeeper.sector_check_passed else "❌ Blacklisted"} |

## 2. Investment Hygiene (Iron Gate)
| Metric | Value | Threshold |
| :--- | :--- | :--- |
| **CAGR** | {cagr_str} | >15-20% |
| **Current Q Growth** | {q_growth_str} | >20% |
| **SBC/Revenue** | {sbc_str} | <20% |
| **PEG Ratio** | {peg_str} | <1.5 (Macro-adjusted) |

## 3. Shadow Audit & Polygraph (V3.4)

### Shadow Audit (影子审计)
| Check | Result |
| :--- | :--- |
| **Fake Tech Detection** | {fake_tech_status} |
| **King Maker Clients** | {king_maker_status} |

**LinkedIn Hiring Analysis:**
{clean_report_content(data.shadow_audit.linkedin_hiring_audit)[:500] if data.shadow_audit and data.shadow_audit.linkedin_hiring_audit else 'N/A'}

**Customer Quality:**
{clean_report_content(data.shadow_audit.customer_quality_audit)[:500] if data.shadow_audit and data.shadow_audit.customer_quality_audit else 'N/A'}

### Polygraph (测谎仪)
| Check | Result |
| :--- | :--- |
| **Cash Flow Divergence** | {cfo_check} |
| **Sandbagging Index** | {sandbagging} |

{data.polygraph.details if data.polygraph and data.polygraph.details else ''}

## 4. The Variant Perception (Why Market is Wrong)
{variant_perception}

## 5. Growth Engine (Blue Sky)

**R&D Effectiveness (Second Curve):**
{rnd_effectiveness}

**TAM Expansion:**
{tam_expansion}

## 6. Valuation & Catalysts

**Dislocation Analysis:**
{dislocation}

**Upcoming Catalysts:**
{', '.join(data.intelligence.catalysts.upcoming_events) if data.intelligence and data.intelligence.catalysts else "N/A"}

## 7. Risk & Soft Power

**Management Integrity:**
{mgmt_integrity}

**Competitive Moat:**
{product_moat}

**Insider Activity:**
{insider_activity}

## 8. Core KPIs
{kpi_table}

## 9. Final Verdict Logic (V3.4)
| Gate | Status |
| :--- | :--- |
| **Macro Gate** | {macro_mode} |
| **Sector Gate** | {"✓ Pass" if data.gatekeeper and data.gatekeeper.sector_check_passed else "❌ Fail"} |
| **Hygiene Gate** | {"✓ Pass" if data.iron_gate and data.iron_gate.passed else "❌ Fail"} |
| **Polygraph Gate** | {"✓ Pass" if data.polygraph and data.polygraph.cash_flow_divergence_check else "⚠️ CFO Divergence"} |
| **Shadow Audit Gate** | {"⚠️ Fake Tech" if data.shadow_audit and data.shadow_audit.is_fake_tech else "✓ Pass"} |

* **Growth Thesis Intact**: {data.tribunal.growth_thesis_intact if data.tribunal else 'N/A'}
* **Valuation Fit**: {data.tribunal.valuation_fit if data.tribunal else 'N/A'}
* **True Discount**: {data.tribunal.is_true_discount if data.tribunal else 'N/A'}
* **Business Model**: {data.identifier.business_model.value if data.identifier else 'N/A'}
* **Bear Case Hook**: {data.identifier.bear_case_hook if data.identifier else 'N/A'}

---
*Generated by MGP V3.4 Anti-Fragile Growth Protocol*
"""
    return report_content


def save_report(data: CompanyData, llm: LLMClient = None, translate: bool = False):
    """保存分析报告"""
    if not data.tribunal:
        print(f"[{data.ticker}] No tribunal decision, skipping report generation.")
        return

    timestamp = datetime.now().strftime("%Y-%m-%d")

    # 生成 V3.4 格式报告
    report_content = generate_report_content_v34(data)

    # 保存英文版
    filename_en = f"REPORT_{data.ticker}_{timestamp}.md"
    with open(filename_en, "w", encoding="utf-8") as f:
        f.write(report_content)
    print(f"Report saved to {filename_en}")

    # 如果需要翻译，生成中文版
    if translate and llm:
        print(f"[{data.ticker}] Translating report to Chinese...")
        translated_content = translate_report(llm, report_content)

        filename_cn = f"REPORT_{data.ticker}_{timestamp}_CN.md"
        with open(filename_cn, "w", encoding="utf-8") as f:
            f.write(translated_content)
        print(f"Chinese report saved to {filename_cn}")


def main():
    parser = argparse.ArgumentParser(description="Mahaney Growth Protocol V3.4 - Anti-Fragile Growth System")
    parser.add_argument("--tickers", type=str, default="DUOL", help="Comma-separated list of tickers")
    parser.add_argument("--force", action="store_true", help="Force deep dive even if gates fail")
    parser.add_argument("--cn", action="store_true", default=True, help="Generate Chinese translated report")
    args = parser.parse_args()

    if not args.tickers:
        print("Please provide tickers using --tickers AAPL,MSFT")
        return

    tickers = [t.strip().upper() for t in args.tickers.split(",")]

    print("\n" + "="*60)
    print("  Mahaney Growth Protocol V3.4")
    print("  'Anti-Fragile Full-Spectrum Arbitrage System'")
    print("  Target: $10B - $50B Mid-Cap Growth Stocks")
    print("="*60)

    fmp = FMPClient()
    llm = LLMClient()
    search = SearchClient()

    results = []

    for ticker in tickers:
        try:
            data = analyze_ticker_v34(ticker, fmp, llm, search, force_deep_dive=args.force)
            results.append(data.model_dump())
            
            if data.tribunal:
                save_report(data, llm=llm, translate=args.cn)
            elif data.error:
                print(f"[{ticker}] Analysis stopped: {data.error}")
                
        except Exception as e:
            print(f"Error analyzing {ticker}: {e}")
            import traceback
            traceback.print_exc()

    with open("results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    print("\nAll analyses complete. Saved to results.json.")


if __name__ == "__main__":
    main()
