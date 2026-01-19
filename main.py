"""
Mahaney Growth Protocol (MGP) V3.7 - Main Entry Point
======================================================
"装甲狙击手" (The Armored Sniper) - 针对 $50B+ 大市值行业赢家

V3.7 流水线:
- Phase 0: Gatekeeper (血统验证 - 市值 > $50B + 行业白/黑名单 + 赢家历史)
- Phase 1: Identifier (财务侦探 - 库存周转 + Capex脉冲 + 定价权 + 护城河)
- Phase 2: Iron Gate (财务装甲 - 毛利率熔断 + 债务窒息线 + 稀释墙)
- Phase 3: Valuation (估值弹簧 - Forward PE + PEG + 历史PE Z-Score)
- Phase 4: Intelligence (催化剂侦测 + 时空约束)
- Phase 5: Tribunal (最终审判)

适用场景: 市值 > $50B 的行业赢家，因内生性、可修复的问题导致股价暴跌
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
from tools.yfinance_client import YFinanceClient
from core.data_models import CompanyData, Decision


def translate_report(llm: LLMClient, report_content: str) -> str:
    """使用 AI 将英文报告翻译为中文，保持原有的 Markdown 结构"""
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


def analyze_ticker_v37(ticker: str, fmp: FMPClient, llm: LLMClient, search: SearchClient, yf: YFinanceClient,
                       force_deep_dive: bool = False) -> CompanyData:
    """
    V3.7 "装甲狙击手" 完整分析流水线
    """
    print(f"\n{'='*60}")
    print(f"  MGP V3.7 'Armored Sniper' Analysis: {ticker}")
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
    
    # ========== Phase 0: Pedigree Check (V3.7) ==========
    print(f"\n[{ticker}] Phase 0: Pedigree Check (V3.7)...")
    gatekeeper = Gatekeeper(fmp, search, yf)
    data.gatekeeper = gatekeeper.analyze(ticker)
    
    if not data.gatekeeper.passed:
        print(f"[{ticker}] ❌ Failed Pedigree Check: {data.gatekeeper.fail_reason}")
        if not force_deep_dive:
            data.error = f"Pedigree Failed: {data.gatekeeper.fail_reason}"
            return data
        print(f"[{ticker}] Proceeding despite Pedigree failure (Force Mode).")
    else:
        pedigree = data.gatekeeper.pedigree
        print(f"[{ticker}] ✓ Pedigree Passed | Market Cap: ${pedigree.market_cap/1e9:.1f}B | Sector: {pedigree.sector}")

    # ========== Phase 1: Financial Forensics (V3.7) ==========
    print(f"\n[{ticker}] Phase 1: Financial Forensics (V3.7)...")
    ident = Identifier(llm, fmp, search)
    
    description = profile.get('description', 'Company') if profile else "Company"
    sector = data.gatekeeper.pedigree.sector if data.gatekeeper and data.gatekeeper.pedigree else ""
    industry = data.gatekeeper.pedigree.industry if data.gatekeeper and data.gatekeeper.pedigree else ""
    
    data.identifier = ident.identify(ticker, description, sector, industry)
    
    if data.identifier.forensics and not data.identifier.forensics.passed:
        print(f"[{ticker}] ❌ Failed Financial Forensics: {data.identifier.forensics.fail_reason}")
        if not force_deep_dive:
            data.error = f"Forensics Failed: {data.identifier.forensics.fail_reason}"
            return data
        print(f"[{ticker}] Proceeding despite Forensics failure (Force Mode).")
    else:
        print(f"[{ticker}] ✓ Financial Forensics Passed")

    # ========== Phase 2: Financial Armor (V3.7) ==========
    print(f"\n[{ticker}] Phase 2: Financial Armor (V3.7)...")
    ig = IronGate(fmp, yf)
    data.iron_gate = ig.analyze(ticker, data.market_cap)

    if not data.iron_gate.passed:
        print(f"[{ticker}] ❌ Failed Financial Armor: {data.iron_gate.fail_reason}")
        if not force_deep_dive:
            data.error = f"Armor Failed: {data.iron_gate.fail_reason}"
            return data
        print(f"[{ticker}] Proceeding despite Armor failure (Force Mode).")
    else:
        print(f"[{ticker}] ✓ Financial Armor Passed")

    # ========== Phase 3: Valuation Spring (V3.7) ==========
    print(f"\n[{ticker}] Phase 3: Valuation Spring (V3.7)...")
    tribunal = Tribunal(llm, fmp, yf)
    data.valuation = tribunal.analyze_valuation(ticker)
    
    if data.valuation.buy_signal_triggered:
        print(f"[{ticker}] ✓ Buy Signal Triggered")
    else:
        print(f"[{ticker}] ⚠️ No Buy Signal - Valuation not at ideal entry")

    # ========== Phase 4: Intelligence + Catalysts (V3.7) ==========
    print(f"\n[{ticker}] Phase 4: Intelligence + Catalysts (V3.7)...")
    intel = Intelligence(llm, search, fmp)
    data.intelligence = intel.gather(ticker, data.identifier, data.gatekeeper)
    
    if data.intelligence.constraints and data.intelligence.constraints.has_near_term_catalyst:
        print(f"[{ticker}] ✓ Near-term catalyst detected")
    else:
        print(f"[{ticker}] ⚠️ No clear near-term catalyst")

    # ========== Phase 5: Final Tribunal (V3.7) ==========
    print(f"\n[{ticker}] Phase 5: Final Tribunal (V3.7)...")
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
        if k == "macro_valuation_analysis":
            continue  # Skip large analysis block
        clean_v = str(v).replace('\n', ' ').strip()[:200]
        table += f"| {k} | {clean_v} |\n"
    
    return table


def generate_report_content_v37(data: CompanyData) -> str:
    """生成 V3.7 格式的报告内容"""
    timestamp = datetime.now().strftime("%Y-%m-%d")

    # 安全获取数据
    price_str = f"${data.current_price:.2f}" if data.current_price else "N/A"
    market_cap_str = f"${data.market_cap / 1e9:.2f}B" if data.market_cap else "N/A"
    
    # Pedigree 数据
    pedigree = data.gatekeeper.pedigree if data.gatekeeper and data.gatekeeper.pedigree else None
    sector_str = pedigree.sector if pedigree else "N/A"
    industry_str = pedigree.industry if pedigree else "N/A"
    cagr_10y_str = f"{pedigree.revenue_cagr_10y:.1%}" if pedigree and pedigree.revenue_cagr_10y else "N/A"
    
    # Forensics 数据
    forensics = data.identifier.forensics if data.identifier and data.identifier.forensics else None
    inv_turnover = f"{forensics.inventory_turnover_current:.2f}" if forensics and forensics.inventory_turnover_current else "N/A"
    capex_pulse = "✓ Positive" if forensics and forensics.capex_pulse_positive else "Neutral"
    pricing_power = "✓ Intact" if forensics and forensics.pricing_power_intact else "⚠️ Weakening"
    moat_strength = forensics.moat_strength.value if forensics else "N/A"
    
    # Armor 数据
    armor = data.iron_gate
    gm_safe = "✓ Safe" if armor and armor.gross_margin_safe else "⚠️ Warning"
    gm_change = f"{armor.gross_margin_yoy_change_bps:+.0f} bps" if armor and armor.gross_margin_yoy_change_bps else "N/A"
    debt_safe = "✓ Safe" if armor and armor.debt_safe else "⚠️ High"
    nd_ebitda = f"{armor.net_debt_to_ebitda:.2f}x" if armor and armor.net_debt_to_ebitda else "N/A"
    dilution_safe = "✓ Safe" if armor and armor.dilution_safe else "⚠️ High"
    dilution_rate = f"{armor.sbc_dilution_rate:.2%}" if armor and armor.sbc_dilution_rate else "N/A"
    
    # Valuation 数据
    val = data.valuation
    forward_pe = f"{val.forward_pe:.1f}x" if val and val.forward_pe else "N/A"
    forward_pe_signal = "✓ BUY SIGNAL" if val and val.forward_pe_signal else "No signal"
    peg_ratio = f"{val.peg_ratio:.2f}" if val and val.peg_ratio else "N/A"
    peg_signal = "✓ BONUS" if val and val.peg_signal else "No bonus"
    pe_zscore = f"{val.pe_z_score:.2f}" if val and val.pe_z_score else "N/A"
    
    # Catalysts 数据
    catalysts = data.intelligence.catalysts if data.intelligence and data.intelligence.catalysts else None
    catalyst_keywords = ", ".join(catalysts.catalyst_keywords_found[:5]) if catalysts and catalysts.catalyst_keywords_found else "None found"
    catalyst_within_12m = "✓ Yes" if catalysts and catalysts.catalyst_within_12m else "No"
    upcoming_events = ", ".join(catalysts.upcoming_events[:3]) if catalysts and catalysts.upcoming_events else "N/A"
    
    # 清洗各部分文本
    rationale_cleaned = clean_report_content(data.tribunal.rationale) if data.tribunal else "N/A"
    
    # Intelligence 数据
    variant_perception = clean_report_content(data.intelligence.catalysts.variant_perception) if data.intelligence and data.intelligence.catalysts else "N/A"
    rnd_effectiveness = clean_report_content(data.intelligence.blue_sky.rnd_effectiveness) if data.intelligence and data.intelligence.blue_sky else "N/A"
    tam_expansion = clean_report_content(data.intelligence.blue_sky.tam_expansion) if data.intelligence and data.intelligence.blue_sky else "N/A"
    mgmt_integrity = clean_report_content(data.intelligence.management_integrity) if data.intelligence else "N/A"
    product_moat = clean_report_content(data.intelligence.product_moat) if data.intelligence else "N/A"
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

    report_content = f"""# MGP V3.7 "Armored Sniper" Analysis: {data.ticker} {decision_icon}
**Date:** {timestamp}
**Verdict:** {data.tribunal.decision.value if data.tribunal else 'N/A'} ({data.tribunal.confidence.value if data.tribunal else 'N/A'} Confidence)
**Price:** {price_str} | **Market Cap:** {market_cap_str}

## Executive Summary
{rationale_cleaned}

---

## 1. Pedigree Check (血统验证)
| Metric | Value | Status |
| :--- | :--- | :--- |
| **Market Cap** | {market_cap_str} | {"✓ >$50B" if data.market_cap and data.market_cap > 50e9 else "⚠️ <$50B"} |
| **Sector** | {sector_str} | {"✓ Whitelisted" if pedigree and pedigree.sector_passed else "❌ Blacklisted"} |
| **Industry** | {industry_str} | |
| **10Y Revenue CAGR** | {cagr_10y_str} | {"✓ Winner" if pedigree and pedigree.is_industry_winner else "⚠️ Declining"} |

## 2. Financial Forensics (财务侦探)
| Indicator | Value | Signal |
| :--- | :--- | :--- |
| **Inventory Turnover** | {inv_turnover} | {"✓ Stable" if forensics and forensics.inventory_check_passed else "⚠️ Crashed"} |
| **Capex Pulse** | {f"{forensics.capex_revenue_current:.1%}" if forensics and forensics.capex_revenue_current else 'N/A'} | {capex_pulse} |
| **Pricing Power** | {f"{forensics.gross_margin_current:.1%}" if forensics and forensics.gross_margin_current else 'N/A'} GM | {pricing_power} |
| **Moat Strength** | {moat_strength} | {forensics.moat_assessment[:50] if forensics and forensics.moat_assessment else ''} |

## 3. Financial Armor (财务装甲)
| Iron Rule | Value | Status |
| :--- | :--- | :--- |
| **Gross Margin Safety** | {gm_change} YoY | {gm_safe} (< 300bps drop) |
| **Debt Safety** | {nd_ebitda} Net Debt/EBITDA | {debt_safe} (< 3.0x) |
| **Dilution Safety** | {dilution_rate} annual | {dilution_safe} (< 3%) |

## 4. Valuation Spring (估值弹簧)
| Metric | Value | Signal |
| :--- | :--- | :--- |
| **Forward PE** | {forward_pe} | {forward_pe_signal} (< 20x) |
| **PEG Ratio** | {peg_ratio} | {peg_signal} (< 0.6) |
| **PE Z-Score** | {pe_zscore} | {"✓ Historical Low" if val and val.historical_pe_signal else "Normal"} |
| **Buy Signal** | | {"✓ TRIGGERED" if val and val.buy_signal_triggered else "Not triggered"} |

## 5. Catalyst Detection (催化剂侦测)
| Check | Result |
| :--- | :--- |
| **Keywords Found** | {catalyst_keywords} |
| **Within 12 Months** | {catalyst_within_12m} |
| **Upcoming Events** | {upcoming_events} |

## 6. The Variant Perception (为什么市场错了)
{variant_perception}

## 7. Growth Engine (Blue Sky)

**R&D Effectiveness (Second Curve):**
{rnd_effectiveness}

**TAM Expansion:**
{tam_expansion}

## 8. Dislocation Analysis
{dislocation}

## 9. Risk & Soft Power

**Management Integrity:**
{mgmt_integrity}

**Competitive Moat:**
{product_moat}

## 10. Core KPIs
{kpi_table}

## 11. Final Verdict Logic
| Gate | Status |
| :--- | :--- |
| **Pedigree Gate** | {"✓ Pass" if pedigree and pedigree.passed else "❌ Fail"} |
| **Forensics Gate** | {"✓ Pass" if forensics and forensics.passed else "❌ Fail"} |
| **Armor Gate** | {"✓ Pass" if armor and armor.passed else "❌ Fail"} |
| **Valuation Gate** | {"✓ Buy Signal" if val and val.buy_signal_triggered else "⚠️ No Signal"} |
| **Catalyst Gate** | {"✓ Catalyst Found" if catalysts and catalysts.catalyst_within_12m else "⚠️ No Catalyst"} |

* **Growth Thesis Intact**: {data.tribunal.growth_thesis_intact if data.tribunal else 'N/A'}
* **Valuation Fit**: {data.tribunal.valuation_fit if data.tribunal else 'N/A'}
* **True Discount (Temporary Bottleneck)**: {data.tribunal.is_true_discount if data.tribunal else 'N/A'}
* **Business Model**: {data.identifier.business_model.value if data.identifier else 'N/A'}
* **Bear Case Hook**: {data.identifier.bear_case_hook if data.identifier else 'N/A'}

---
*Generated by MGP V3.7 "Armored Sniper" Protocol*
*Target: $50B+ Industry Winners with Temporary, Fixable Bottlenecks*
"""
    return report_content


def save_report(data: CompanyData, llm: LLMClient = None, translate: bool = False):
    """保存分析报告"""
    if not data.tribunal:
        print(f"[{data.ticker}] No tribunal decision, skipping report generation.")
        return

    timestamp = datetime.now().strftime("%Y-%m-%d")

    # 生成 V3.7 格式报告
    report_content = generate_report_content_v37(data)

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
    parser = argparse.ArgumentParser(description="Mahaney Growth Protocol V3.7 - Armored Sniper")
    parser.add_argument("--tickers", type=str, default="NVO", help="Comma-separated list of tickers")
    parser.add_argument("--force", action="store_true", help="Force deep dive even if gates fail")
    parser.add_argument("--cn", action="store_true", default=True, help="Generate Chinese translated report")
    args = parser.parse_args()

    if not args.tickers:
        print("Please provide tickers using --tickers NVO,NVDA")
        return

    tickers = [t.strip().upper() for t in args.tickers.split(",")]

    print("\n" + "="*60)
    print("  Mahaney Growth Protocol V3.7")
    print("  'Armored Sniper' - 装甲狙击手")
    print("  Target: $50B+ Industry Winners with Temporary Bottlenecks")
    print("="*60)

    fmp = FMPClient()
    llm = LLMClient()
    search = SearchClient()
    yf = YFinanceClient()

    results = []

    for ticker in tickers:
        try:
            data = analyze_ticker_v37(ticker, fmp, llm, search, yf, force_deep_dive=args.force)
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
