"""
Mahaney Growth Protocol (MGP) V3.5 - The Singularity Edition
============================================================
中大盘成长股"反脆弱全景套利"系统

流水线 (V3.5 Pipeline):
1. Phase 0: Gatekeeper (宏观压力阀 + 行业黑名单 + 20%未来铁律)
2. Phase 1: Deep Audit (深度审计 - 商业模式分层 + 测谎仪 + 身份识别)
3. Phase 2: Shadow Audit (影子验证 - King Makers / Organic / Fake Tech)
4. Phase 3: Intelligence (软实力 - 管理层/护城河/内幕交易)
5. Phase 4: Valuation & Catalysts (蓝天分析 + 催化剂)
6. Phase 5: Physics (量价物理学 - Ignition / Accumulation)
7. Phase 6: Tribunal (最终审判 - 60秒核对清单)
"""

import argparse
import json
import os
from datetime import datetime

from phases.gatekeeper import Gatekeeper
from phases.deep_audit import DeepAudit
from phases.shadow_audit import ShadowAudit
from phases.intelligence import Intelligence
from phases.physics import Physics
from phases.tribunal import Tribunal

from tools.fmp import FMPClient
from tools.llm import LLMClient
from tools.search import SearchClient
from tools.yahoo import YahooClient
from core.data_models import CompanyData

def analyze_ticker_v35(ticker: str, fmp: FMPClient, llm: LLMClient, search: SearchClient, yahoo: YahooClient,
                       force_deep_dive: bool = False) -> CompanyData:
    
    print(f"\n{'='*60}")
    print(f"  MGP V3.5 Singularity Analysis: {ticker}")
    print(f"{'='*60}")
    
    data = CompanyData(ticker=ticker)
    
    # Basic Info
    quote = fmp.get_quote(ticker)
    profile = fmp.get_profile(ticker)
    if quote:
        data.company_name = quote.get('name')
        data.current_price = quote.get('price')
        data.market_cap = quote.get('marketCap')
    
    print(f"  Company: {data.company_name}")
    print(f"  Price: ${data.current_price:.2f}" if data.current_price else "  Price: N/A")
    
    # ========== Phase 0: Gatekeeper ==========
    print(f"\n[{ticker}] Phase 0: Gatekeeper...")
    gatekeeper = Gatekeeper(fmp, search, yahoo)
    data.gatekeeper = gatekeeper.analyze(ticker)
    
    if not data.gatekeeper.passed:
        print(f"[{ticker}] ❌ Gatekeeper Failed: {data.gatekeeper.fail_reason}")
        if not force_deep_dive:
            data.error = f"Gatekeeper Failed: {data.gatekeeper.fail_reason}"
            return data
        print(f"[{ticker}] Force Mode Active - Proceeding...")

    # ========== Phase 1: Deep Audit & Identity ==========
    print(f"\n[{ticker}] Phase 1: Deep Audit & Identity...")
    deep_audit = DeepAudit(fmp, llm, yahoo)
    
    # 1a. Identity
    data.identifier = deep_audit.identify_business_model(ticker, profile)
    print(f"    - Business Model: {data.identifier.business_model.value}")
    
    # 1b. Audit
    data.deep_audit = deep_audit.analyze(ticker, data.identifier)
    
    if not data.deep_audit.passed:
        print(f"[{ticker}] ❌ Deep Audit Failed: {data.deep_audit.fail_reason}")
        if not force_deep_dive:
             data.error = f"Deep Audit Failed: {data.deep_audit.fail_reason}"
             return data
        print(f"[{ticker}] Force Mode Active - Proceeding...")

    # ========== Phase 2: Shadow Audit ==========
    print(f"\n[{ticker}] Phase 2: Shadow Audit...")
    shadow = ShadowAudit(search, fmp, llm)
    data.shadow_audit = shadow.audit(ticker, data.company_name, data.identifier.business_model)
    
    # ========== Phase 3 & 4: Intelligence & Valuation ==========
    print(f"\n[{ticker}] Phase 3 & 4: Intelligence & Valuation...")
    intel = Intelligence(llm, search, fmp)
    data.intelligence = intel.gather(ticker, data.identifier, data.gatekeeper)

    # ========== Phase 5: Physics (VPA) ==========
    print(f"\n[{ticker}] Phase 5: Physics (VPA)...")
    physics = Physics(fmp)
    data.physics = physics.analyze(ticker)

    # ========== Phase 6: Tribunal ==========
    print(f"\n[{ticker}] Phase 6: Final Tribunal...")
    tribunal = Tribunal(llm)
    data.tribunal = tribunal.judge(data)
    
    print(f"\n{'='*60}")
    print(f"  FINAL VERDICT: {data.tribunal.decision.value}")
    print(f"  Confidence: {data.tribunal.confidence.value}")
    print(f"{'='*60}")

    return data

def generate_report_content_v35(data: CompanyData) -> str:
    """Generate V3.5 Report - Enhanced with detailed analysis"""
    decision = data.tribunal.decision.value if data.tribunal else "N/A"
    
    # Physics Icons
    physics_status = "Neutral"
    if data.physics:
        if data.physics.is_ignition:
            physics_status = "🚀 IGNITION"
        elif data.physics.is_accumulation:
            physics_status = "🔋 ACCUMULATION"
        elif data.physics.is_broken_trend:
            physics_status = "⚠️ BROKEN TREND"
    
    # Build Deep Audit Details
    deep_audit_details = ""
    if data.deep_audit:
        da = data.deep_audit
        deep_audit_details = f"""
### Detailed Metrics
| Metric | Value | Formula/Source |
|--------|-------|----------------|
| Revenue CAGR (N-Year) | {f"{da.revenue_cagr_ny:.1%}" if da.revenue_cagr_ny else "N/A"} | (Latest Rev / Oldest Rev)^(1/N) - 1 |
| Q/Q Revenue Growth | {f"{da.revenue_growth_current_q:.1%}" if da.revenue_growth_current_q else "N/A"} | (Current Q Rev - YoY Q Rev) / YoY Q Rev |
| SBC / Revenue | {f"{da.sbc_revenue_ratio:.1%}" if da.sbc_revenue_ratio else "N/A"} | TTM SBC / TTM Revenue |
| Rule of 40 | {f"{da.rule_of_40:.1%}" if da.rule_of_40 else "N/A"} | Rev Growth + FCF Margin |
| Inventory Health | {da.inventory_health or "N/A"} | Inv Days trend vs Gross Margin |
| Insider Selling Risk | {"⚠️ YES" if da.insider_selling_risk else "No"} | Yahoo Finance Insider TX |
"""
    
    # Build Shadow Audit Details
    shadow_audit_details = ""
    if data.shadow_audit:
        sa = data.shadow_audit
        shadow_audit_details = f"""
### Logic & Evidence
- **LinkedIn Hiring Audit:** {sa.linkedin_hiring_audit or "Not checked"}
- **Customer Quality:** {sa.customer_quality_audit or "Not checked"}
- **Marketing Efficiency:** {sa.marketing_efficiency or "Not checked"}
- **App Store Rank:** {sa.app_store_rank or "Not checked"}
- **Sandbagging:** {sa.sandbagging_details or "Not checked"}
"""
    
    # Build Physics Details
    physics_details = ""
    if data.physics:
        p = data.physics
        physics_details = f"""
### Technical Indicators
| Indicator | Value | Condition |
|-----------|-------|-----------|
| Current Price | ${(p.current_price if p.current_price else 0):.2f} | - |
| SMA 20 | ${(p.sma_20 if p.sma_20 else 0):.2f} | Life Line |
| Relative Volume | {f"{p.relative_volume:.1f}x" if p.relative_volume else "N/A"} | Vol / Avg Vol 20 |
| Price vs SMA20 | {"Above ✅" if p.current_price and p.sma_20 and p.current_price > p.sma_20 else "Below ⚠️"} | Trend |

### Signal Analysis
- **Ignition Criteria:** Price > SMA20 + RVol > 2.0 + Strong Close (>0.7) → {"MET ✅" if p.is_ignition else "NOT MET"}
- **Accumulation Criteria:** Range < 2% + RVol > 1.5 → {"MET ✅" if p.is_accumulation else "NOT MET"}
- **Broken Trend:** Close < SMA20 for 3 days → {"YES ⚠️" if p.is_broken_trend else "NO"}
"""
    
    # Build Intelligence Details
    intelligence_details = ""
    if data.intelligence:
        intel = data.intelligence
        intelligence_details = f"""
### Management Integrity
{intel.management_integrity or "N/A"}

### Competitive Moat
{intel.product_moat or "N/A"}

### Insider Activity
{intel.insider_activity or "N/A"}

### Price Dislocation Context
{intel.dislocation_context or "N/A"}
"""
    
    # Build Blue Sky & Catalysts
    valuation_details = ""
    if data.intelligence:
        intel = data.intelligence
        blue_sky = intel.blue_sky
        catalysts = intel.catalysts
        macro_val = intel.kpi_values.get('macro_valuation_analysis', 'N/A')
        
        rnd_eff = blue_sky.rnd_effectiveness if blue_sky else "N/A"
        tam_exp = blue_sky.tam_expansion if blue_sky else "N/A"
        events = ", ".join(catalysts.upcoming_events) if catalysts and catalysts.upcoming_events else "N/A"
        cat_analysis = catalysts.catalyst_analysis if catalysts and catalysts.catalyst_analysis else "N/A"
        variant = catalysts.variant_perception if catalysts else "N/A"
        
        valuation_details = f"""
### Macro-Adjusted Valuation
{macro_val}

### Blue Sky Analysis
**R&D Effectiveness (Second Curve):**
{rnd_eff}

**TAM Expansion:**
{tam_exp}

### Catalysts
**Upcoming Events:** {events}

**Event Analysis:**
{cat_analysis}

**Variant Perception:**
{variant}
"""
    
    content = f"""# MGP V3.5 Singularity Report: {data.ticker}
**Date:** {datetime.now().strftime("%Y-%m-%d")}
**Verdict:** {decision}
**Physics:** {physics_status}
**Price:** ${(data.current_price if data.current_price else 0):.2f}

---

## Executive Summary
{data.tribunal.rationale if data.tribunal else 'N/A'}

---

## 1. The Gatekeeper (Macro & Iron Rule)
- **Macro Mode:** {data.gatekeeper.macro_mode.value if data.gatekeeper else 'N/A'}
- **US 10Y Yield:** {f"{data.gatekeeper.us10y_yield:.2f}%" if data.gatekeeper and data.gatekeeper.us10y_yield else 'N/A'}
- **VIX:** {f"{data.gatekeeper.vix_value:.1f}" if data.gatekeeper and data.gatekeeper.vix_value else 'N/A'}
- **Sector Check:** {'✅ Passed' if data.gatekeeper and data.gatekeeper.sector_check_passed else '❌ Failed'}
- **Future 20% Rule:** {'✅ Passed' if data.gatekeeper and data.gatekeeper.future_revenue_cagr_3y and data.gatekeeper.future_revenue_cagr_3y > 0.2 else '⚠️ Warning'}

---

## 2. Deep Audit (Hygiene)
- **Result:** {'✅ Passed' if data.deep_audit and data.deep_audit.passed else '❌ Failed'}
- **Fail Reason:** {data.deep_audit.fail_reason if data.deep_audit and data.deep_audit.fail_reason else 'None'}
{deep_audit_details}

---

## 3. Shadow Audit
- **King Makers:** {'✅ Yes' if data.shadow_audit and data.shadow_audit.has_king_maker_clients else 'No'}
- **Organic Growth:** {'✅ Confirmed' if data.shadow_audit and data.shadow_audit.organic_growth_confirmed else 'Unconfirmed'}
- **Fake Tech:** {'⚠️ YES' if data.shadow_audit and data.shadow_audit.is_fake_tech else 'No'}
{shadow_audit_details}

---

## 4. Physics (VPA)
- **Signal:** {physics_status}
- **Ignition:** {'✅ YES' if data.physics and data.physics.is_ignition else 'No'}
- **Accumulation:** {'✅ YES' if data.physics and data.physics.is_accumulation else 'No'}
{physics_details}

---

## 5. Intelligence & Soft Factors
{intelligence_details}

---

## 6. Valuation & Catalysts
{valuation_details}

---
*Generated by MGP V3.5 Singularity Engine*
"""
    return content

def main():
    parser = argparse.ArgumentParser(description="MGP V3.5 Singularity Edition")
    parser.add_argument("--tickers", type=str, default="AXON", help="Comma-separated tickers")
    parser.add_argument("--force", action="store_true", help="Force deep dive")
    parser.add_argument("--scan_mid_cap", default=False,  action="store_true", help="Scan for Mid-Cap (10B-50B) stocks using FMP Screener")
    parser.add_argument("--limit", type=int, default=50, help="Limit number of stocks to analyze from screener")
    args = parser.parse_args()
    
    fmp = FMPClient()
    llm = LLMClient()
    search = SearchClient()
    yahoo = YahooClient()
    
    if args.scan_mid_cap:
        print(f"\n{'='*60}")
        print("  Running Mid-Cap Scanner (10B - 50B) - Excluding Funds/ETFs...")
        print(f"{'='*60}")
        
        # 10B to 50B
        min_cap = 10_000_000_000
        max_cap = 50_000_000_000
        
        screener_results = fmp.get_stock_screener(
            market_cap_more_than=min_cap,
            market_cap_lower_than=max_cap,
            exchange="NASDAQ,NYSE",
            limit=args.limit * 2 # Fetch a bit more to be safe, though limit param does limit result size
        )
        
        if not screener_results:
            print("No stocks found matching criteria.")
            return

        print(f"Found {len(screener_results)} candidates. Processing top {args.limit}...")
        
        tickers = [item['symbol'] for item in screener_results][:args.limit]
        print(f"Targets: {', '.join(tickers)}")
        
    else:
        tickers = [t.strip().upper() for t in args.tickers.split(",")]
    
    results = []
    
    for ticker in tickers:
        try:
            data = analyze_ticker_v35(ticker, fmp, llm, search, yahoo, args.force)
            results.append(data.model_dump())
            
            # Save Report
            if data.tribunal:
                report = generate_report_content_v35(data)
                
                # Ensure report directory exists
                report_dir = "report"
                if not os.path.exists(report_dir):
                    os.makedirs(report_dir)
                    
                filename = f"{report_dir}/REPORT_V3.5_{ticker}_{datetime.now().strftime('%Y-%m-%d')}.md"
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(report)
                print(f"Saved report to {filename}")
                
        except Exception as e:
            print(f"Error analyzing {ticker}: {e}")
            import traceback
            traceback.print_exc()
            
    with open("results_v35.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)

if __name__ == "__main__":
    main()
