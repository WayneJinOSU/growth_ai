import argparse
import json
from datetime import datetime
from typing import List

from phases.iron_gate import IronGate
from phases.identifier import Identifier
from phases.intelligence import Intelligence
from phases.tribunal import Tribunal

from tools.fmp import FMPClient
from tools.llm import LLMClient
from tools.search import SearchClient
from core.data_models import CompanyData, AnalysisReport


def translate_report(llm: LLMClient, report_content: str) -> str:
    """
    使用 AI 将英文报告翻译为中文，保持原有的 Markdown 结构

    Args:
        llm: LLM 客户端
        report_content: 英文报告内容

    Returns:
        中文报告内容
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


def analyze_ticker(ticker: str, fmp: FMPClient, llm: LLMClient, search: SearchClient,
                   force_deep_dive: bool = False) -> CompanyData:
    print(f"\n--- Analyzing {ticker} ---")
    data = CompanyData(ticker=ticker)

    # Phase 1: Iron Gate
    print(f"[{ticker}] Phase 1: Iron Gate...")
    ig = IronGate(fmp)
    data.iron_gate = ig.analyze(ticker)

    quote = fmp.get_quote(ticker)
    if quote:
        data.company_name = quote.get('name')
        data.current_price = quote.get('price')
        data.market_cap = quote.get('marketCap')

    if not data.iron_gate.passed:
        print(f"[{ticker}] Failed Iron Gate: {data.iron_gate.fail_reason}")
        if not force_deep_dive:
            return data
        print(f"[{ticker}] Proceeding despite Iron Gate failure (Force Mode).")

    # Phase 2: Identifier
    print(f"[{ticker}] Phase 2: Identifier...")
    ident = Identifier(llm)
    # We need a description. FMP profile has description.
    profile = fmp.get_profile(ticker)
    description = profile['description'] if profile else "Technology company"

    data.identifier = ident.identify(ticker, description)
    print(f"[{ticker}] Identified as {data.identifier.business_model} with KPIs: {data.identifier.specific_kpis}")

    # Phase 3: Intelligence
    print(f"[{ticker}] Phase 3: Saturated Intelligence...")
    intel = Intelligence(llm, search)
    data.intelligence = intel.gather(ticker, data.identifier)

    # Phase 4: Tribunal
    print(f"[{ticker}] Phase 4: The Tribunal...")
    tribunal = Tribunal(llm)
    data.tribunal = tribunal.judge(data)
    print(f"[{ticker}] Verdict: {data.tribunal.decision} ({data.tribunal.confidence})")

    return data


def generate_report_content(data: CompanyData) -> str:
    """
    生成报告内容字符串

    Args:
        data: 公司分析数据

    Returns:
        Markdown 格式的报告内容
    """
    timestamp = datetime.now().strftime("%Y-%m-%d")

    # 安全获取可能为 None 的值
    price_str = f"${data.current_price:.2f}" if data.current_price else "N/A"
    market_cap_str = f"${data.market_cap / 1e9:.2f}B" if data.market_cap else "N/A"
    cagr_str = f"{data.iron_gate.revenue_cagr_5y:.1%}" if data.iron_gate.revenue_cagr_5y is not None else "N/A"
    q_growth_str = f"{data.iron_gate.revenue_growth_current_q:.1%}" if data.iron_gate.revenue_growth_current_q is not None else "N/A"
    peg_str = f"{data.iron_gate.peg_ratio:.2f}" if data.iron_gate.peg_ratio else "N/A"
    margin_slope_str = f"{data.iron_gate.gross_margin_slope:.4f}" if data.iron_gate.gross_margin_slope is not None else "N/A"
    opex_str = "Passed" if data.iron_gate.operating_leverage else (
        "Failed" if data.iron_gate.operating_leverage is False else "N/A")

    sbc_str = f"{data.iron_gate.sbc_revenue_ratio:.1%}" if data.iron_gate.sbc_revenue_ratio is not None else "N/A"
    dilution_check_str = "Passed" if data.iron_gate.dilution_shield_passed else "Failed"

    report_content = f"""# MGP V3.2 Analysis: {data.ticker}
**Date:** {timestamp}
**Verdict:** {data.tribunal.decision.value} ({data.tribunal.confidence.value} Confidence)
**Price:** {price_str} | **Market Cap:** {market_cap_str}

## Executive Summary
{data.tribunal.rationale}

---

## Phase 1: The Iron Gate & Hygiene
* **Status**: {"Passed" if data.iron_gate.passed else "Failed"}
* **CAGR**: {cagr_str}
* **Current Q Growth**: {q_growth_str}
* **SBC/Rev Ratio**: {sbc_str} (Threshold: <20%)
* **Dilution Shield**: {dilution_check_str}
* **PEG Ratio**: {peg_str}
* **Gross Margin Slope**: {margin_slope_str}

## Phase 2: DNA & KPIs
* **Business Model**: {data.identifier.business_model.value}
* **Key KPIs**: {', '.join(data.identifier.specific_kpis)}
* **Bear Case Hook**: {data.identifier.bear_case_hook}

## Phase 3: Blue Sky & Intelligence
### Blue Sky (Option Value)
* **R&D Effectiveness**: {data.intelligence.blue_sky.rnd_effectiveness if data.intelligence.blue_sky else "N/A"}
* **TAM Expansion**: {data.intelligence.blue_sky.tam_expansion if data.intelligence.blue_sky else "N/A"}

### Catalyst Calendar
* **Upcoming Events**: {', '.join(data.intelligence.catalysts.upcoming_events) if data.intelligence.catalysts else "N/A"}
* **Variant Perception**: {data.intelligence.catalysts.variant_perception if data.intelligence.catalysts else "N/A"}

### Core Intelligence
* **KPI Performance**:
{json.dumps(data.intelligence.kpi_values, indent=2)}

* **Management**: {data.intelligence.management_integrity}
* **Moat**: {data.intelligence.product_moat}
* **Insider Activity**: {data.intelligence.insider_activity}
* **Dislocation**: {data.intelligence.dislocation_context}

## Phase 4: Tribunal Logic
* **Growth Thesis Intact**: {data.tribunal.growth_thesis_intact}
* **Valuation Fit**: {data.tribunal.valuation_fit}
* **True Discount**: {data.tribunal.is_true_discount}

---
*Generated by MGP V3.2 Auto-Analyst*
"""
    return report_content


def save_report(data: CompanyData, llm: LLMClient = None, translate: bool = False):
    """
    保存分析报告

    Args:
        data: 公司分析数据
        llm: LLM 客户端 (翻译时需要)
        translate: 是否生成中文翻译版本
    """
    if not data.tribunal:
        return

    timestamp = datetime.now().strftime("%Y-%m-%d")

    # 生成英文报告
    report_content = generate_report_content(data)

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
    parser = argparse.ArgumentParser(description="Mahaney Growth Protocol V3.0")
    parser.add_argument("--tickers", type=str, default="DUOL", help="Comma-separated list of tickers")
    parser.add_argument("--force", action="store_true", help="Force deep dive even if Iron Gate fails")
    parser.add_argument("--cn", action="store_true", default=True,  help="Generate Chinese translated report")
    args = parser.parse_args()

    if not args.tickers:
        print("Please provide tickers using --tickers AAPL,MSFT")
        return

    tickers = [t.strip().upper() for t in args.tickers.split(",")]

    fmp = FMPClient()
    llm = LLMClient()
    search = SearchClient()

    results = []

    for ticker in tickers:
        try:
            data = analyze_ticker(ticker, fmp, llm, search, force_deep_dive=args.force)
            results.append(data.model_dump())
            if data.tribunal:
                save_report(data, llm=llm, translate=args.cn)
        except Exception as e:
            print(f"Error analyzing {ticker}: {e}")
            import traceback
            traceback.print_exc()

    with open("results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print("All analyses complete. Saved to results.json.")


if __name__ == "__main__":
    main()
