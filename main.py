"""
Mahaney Growth Protocol (MGP) V3.5 - The Blue Sky Edition
==========================================================
中大盘成长股"全维度战略"作战系统

流水线 (V3.5 Blue Sky Pipeline):
1. Phase 0: Gatekeeper (门槛熔断)
2. Phase 1: Deep Audit (深度审计)
3. Phase 2: Shadow Audit (影子验证)
4. Phase 3: Intelligence (软性情报)
5. Phase 4: Blue Sky (蓝天展望 - 第二曲线)
6. Phase 5: Catalysts (势能与催化)
7. Phase 6: Strategy (战略定价)
8. Phase 7: Physics (量价物理学)
9. Phase 8: Tribunal (最终审判)
"""

import argparse
import json
import os
from datetime import datetime

from phases.gatekeeper import Gatekeeper
from phases.deep_audit import DeepAudit
from phases.shadow_audit import ShadowAudit
from phases.intelligence import Intelligence
from phases.catalysts import CatalystsAnalyzer
from phases.strategy import StrategyAnalyzer
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
    print(f"  MGP V3.5 Blue Sky Analysis: {ticker}")
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
    
    is_mega_cap = data.market_cap and data.market_cap > 150_000_000_000
    if not data.gatekeeper.passed:
        print(f"[{ticker}] ❌ Gatekeeper Failed: {data.gatekeeper.fail_reason}")
        if is_mega_cap:
            print(f"[{ticker}] ⚡ Mega Cap detected: Bypassing early exit to continue analysis...")
        elif not force_deep_dive:
            data.error = f"Gatekeeper Failed: {data.gatekeeper.fail_reason}"
            return data
        else:
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
        if is_mega_cap:
            print(f"[{ticker}] ⚡ Mega Cap detected: Bypassing early exit to continue analysis...")
        elif not force_deep_dive:
             data.error = f"Deep Audit Failed: {data.deep_audit.fail_reason}"
             return data
        else:
            print(f"[{ticker}] Force Mode Active - Proceeding...")

    # ========== Phase 2: Shadow Audit ==========
    print(f"\n[{ticker}] Phase 2: Shadow Audit...")
    shadow = ShadowAudit(search, fmp, llm)
    data.shadow_audit = shadow.audit(ticker, data.company_name, data.identifier.business_model, data.references)
    
    # ========== Phase 3 & 4: Intelligence & Blue Sky ==========
    print(f"\n[{ticker}] Phase 3 & 4: Intelligence & Blue Sky...")
    intel = Intelligence(llm, search, fmp)
    data.intelligence = intel.gather(ticker, data.identifier, data.gatekeeper, data.references)

    # ========== Phase 5: Catalysts & Waves ==========
    print(f"\n[{ticker}] Phase 5: Catalysts & Waves...")
    catalysts_analyzer = CatalystsAnalyzer(llm, search)
    catalyst_data = catalysts_analyzer.analyze(ticker, data.company_name, data.references)
    # Merge into intelligence.catalysts
    if data.intelligence:
        data.intelligence.catalysts = catalyst_data

    # ========== Phase 6: Strategic Pricing ==========
    print(f"\n[{ticker}] Phase 6: Strategic Pricing...")
    strategy = StrategyAnalyzer()
    data.strategic_pricing = strategy.analyze(data, catalyst_data)
    print(f"    - Strategic Definition: {data.strategic_pricing.strategic_definition.value if data.strategic_pricing.strategic_definition else 'N/A'}")

    # ========== Phase 7: Physics (VPA) ==========
    print(f"\n[{ticker}] Phase 7: Physics (VPA)...")
    physics = Physics(fmp, llm)
    data.physics = physics.analyze(ticker)

    # ========== Phase 8: Tribunal ==========
    print(f"\n[{ticker}] Phase 8: Final Tribunal...")
    tribunal = Tribunal(llm)
    data.tribunal = tribunal.judge(data, data.strategic_pricing)
    
    print(f"\n{'='*60}")
    print(f"  FINAL VERDICT: {data.tribunal.decision.value}")
    print(f"  Confidence: {data.tribunal.confidence.value}")
    print(f"{'='*60}")

    return data

def generate_report_content_v35(data: CompanyData) -> str:
    """Generate V3.5 Blue Sky Report - Enhanced with detailed analysis"""
    decision = data.tribunal.decision.value if data.tribunal else "N/A"
    
    # Strategic Definition
    strategic_def = ""
    if data.strategic_pricing and data.strategic_pricing.strategic_definition:
        strategic_def = data.strategic_pricing.strategic_definition.value
    
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
"""
    
    # Build Blue Sky Details (Phase 4)
    blue_sky_details = ""
    if data.intelligence and data.intelligence.blue_sky:
        bs = data.intelligence.blue_sky
        blue_sky_details = f"""
### TAM Explosion Logic
{bs.tam_expansion or "N/A"}

### Second Growth Curve (R&D Effectiveness)
{bs.rnd_effectiveness or "N/A"}
"""

    # Build Catalysts & Waves Details (Phase 5)
    catalysts_details = ""
    if data.intelligence and data.intelligence.catalysts:
        cat = data.intelligence.catalysts
        thematic_wave = cat.thematic_waves or "None identified"
        wave_strength = cat.wave_strength or "N/A"
        events = ", ".join(cat.upcoming_events) if cat.upcoming_events else "N/A"
        catalysts_details = f"""
### Primary: Thematic Wave (全行业势能)
**Wave:** {thematic_wave}
**Strength:** {wave_strength}

### Secondary: Hard Events
**Upcoming Events:** {events}

**Analysis:**
{cat.catalyst_analysis or "N/A"}
"""

    # Build Strategic Pricing Details (Phase 6)
    strategy_details = ""
    if data.strategic_pricing:
        sp = data.strategic_pricing
        strategy_details = f"""
### Step 1: Valuation Scrub
{sp.adjustment_reason or "No adjustment"}

### Step 2: Fortress Test (Tier Level)
**Tier:** {sp.tier_level.value if sp.tier_level else "N/A"}
**Rationale:** {sp.tier_rationale or "N/A"}

### Step 3: Blue Sky Re-Rating
**Triggered:** {"✅ Yes (PEG limit relaxed to 2.5)" if sp.blue_sky_triggered else "No"}
**PEG Limit:** {sp.peg_limit}

### Step 4: Executive Matrix
| Dimension | Value |
|-----------|-------|
| Catalyst Strength | {sp.catalyst_strength or "N/A"} |
| Valuation Status | {sp.valuation_status or "N/A"} |
| **Strategic Definition** | **{sp.strategic_definition.value if sp.strategic_definition else "N/A"}** |
| Action | {sp.action_instruction or "N/A"} |
"""

    # Build Physics Details (Phase 7)
    physics_details = ""
    if data.physics:
        p = data.physics
        physics_details = f"""
### Technical Indicators
| Indicator | Value | Condition |
|-----------|-------|-----------|
| Current Price | ${(p.current_price if p.current_price else 0):.2f} | - |
| SMA 20 | ${(p.sma_20 if p.sma_20 else 0):.2f} | 生命线 (Life Line) |
| Relative Volume | {f"{p.relative_volume:.1f}x" if p.relative_volume else "N/A"} | Vol / Avg Vol 20 |
| Daily Range | {f"{p.daily_range*100:.1f}%" if p.daily_range else "N/A"} | (High - Low) / Close |
| Close Strength | {f"{p.close_strength:.1%}" if p.close_strength else "N/A"} | (Close - Low) / (High - Low) |
| Price vs SMA20 | {"Above ✅" if p.current_price and p.sma_20 and p.current_price > p.sma_20 else "Below ⚠️"} | Trend |

### Signal Analysis
| Form | Feature | Meaning | Status |
|------|---------|---------|--------|
| 📦 Accumulation | Range < 2% + RVol > 1.5 | Quiet Accumulation | {"✅ DETECTED" if p.is_accumulation else "NOT MET"} |
| 🚀 Ignition | Price > SMA20 + RVol > 2.0 + Strong Close | Momentum Ignition | {"✅ DETECTED" if p.is_ignition else "NOT MET"} |
| 📉 Broken Trend | Close < SMA20 for 3+ days | Trend Death | {"⚠️ YES" if p.is_broken_trend else "NO"} |
"""
        
        if p.ai_analysis:
            physics_details += f"""
### 🌌 AI Physical Dynamics Analysis
**Conclusion:** {p.ai_conclusion}
**Recommendation:** {p.ai_recommendation}

{p.ai_analysis}
"""
    
    # Build Macro Valuation
    macro_val = ""
    if data.intelligence and data.intelligence.kpi_values:
        macro_val = data.intelligence.kpi_values.get('macro_valuation_analysis', '')

    # Build Tribunal Checklist
    tribunal_checklist_md = ""
    if data.tribunal and data.tribunal.checklist_results:
        checklist = data.tribunal.checklist_results
        
        # Define display mapping
        display_map = {
            "risk_fuse": "Risk Fuse (VIX < 30)",
            "audit_passed": "Audit Passed (Deep Audit)",
            "blue_sky": "Blue Sky Confirmed (Second Curve/TAM)",
            "strategic_match": "Strategic Match (Tier 1/2 or Cheap)",
            "wave_resonance": "Wave Resonance (Thematic Wave)",
            "physical_ignition": "Physical Ignition (Price > SMA20 + RVol)"
        }
        
        checklist_lines = []
        for k, passed in checklist.items():
            icon = "✅" if passed else "❌"
            label = display_map.get(k, k.replace("_", " ").title())
            checklist_lines.append(f"- [{icon}] **{label}**")
            
        tribunal_checklist_md = "\n".join(checklist_lines)
    else:
        tribunal_checklist_md = "Checklist data not available."


    # Build References Section
    references_md = ""
    if data.references:
        ref_lines = []
        # Deduplicate by URL
        seen_urls = set()
        for ref in data.references:
            if ref.url not in seen_urls:
                seen_urls.add(ref.url)
                title = ref.title.replace('\n', ' ').strip()
                ref_lines.append(f"- [{ref.id}] [{title}]({ref.url})")
        references_md = "\n".join(ref_lines)
    else:
        references_md = "No external references cited."


    content = f"""# MGP V3.5 Blue Sky Report: {data.ticker}
**Date:** {datetime.now().strftime("%Y-%m-%d")}
**Verdict:** {decision}
**Strategic Definition:** {strategic_def or "N/A"}
**Physics:** {physics_status}
**Price:** ${(data.current_price if data.current_price else 0):.2f}

---

## Executive Summary
{data.tribunal.rationale if data.tribunal else 'N/A'}

---

## Phase 0: The Gatekeeper (门槛熔断)
- **Macro Mode:** {data.gatekeeper.macro_mode.value if data.gatekeeper else 'N/A'}
- **US 10Y Yield:** {f"{data.gatekeeper.us10y_yield:.2f}%" if data.gatekeeper and data.gatekeeper.us10y_yield else 'N/A'}
- **VIX:** {f"{data.gatekeeper.vix_value:.1f}" if data.gatekeeper and data.gatekeeper.vix_value else 'N/A'}
- **Sector Check:** {'✅ Passed' if data.gatekeeper and data.gatekeeper.sector_check_passed else '❌ Failed'}
- **Future 20% Rule:** {'✅ Passed' if data.gatekeeper and data.gatekeeper.future_revenue_cagr_3y and data.gatekeeper.future_revenue_cagr_3y > 0.2 else '⚠️ Warning'}

---

## Phase 1: Deep Audit (深度审计)
- **Result:** {'✅ Passed' if data.deep_audit and data.deep_audit.passed else '❌ Failed'}
- **Fail Reason:** {data.deep_audit.fail_reason if data.deep_audit and data.deep_audit.fail_reason else 'None'}
{deep_audit_details}

---

## Phase 2: Shadow Audit (影子验证)
- **King Makers:** {'✅ Yes' if data.shadow_audit and data.shadow_audit.has_king_maker_clients else 'No'}
- **Organic Growth:** {'✅ Confirmed' if data.shadow_audit and data.shadow_audit.organic_growth_confirmed else 'Unconfirmed'}
- **Fake Tech:** {'⚠️ YES' if data.shadow_audit and data.shadow_audit.is_fake_tech else 'No'}
{shadow_audit_details}

---

## Phase 3: Intelligence (软性情报)
{intelligence_details}

---

## Phase 4: Blue Sky (蓝天展望)
{blue_sky_details}

---

## Phase 5: Catalysts & Waves (势能与催化)
{catalysts_details}

---

## Phase 6: Strategic Pricing (战略定价)
{strategy_details}

---

## Phase 7: Physics VPA (量价物理学)
- **Signal:** {physics_status}
{physics_details}

---

## Phase 8: Final Tribunal (最终审判)

### 60-Second Checklist
{tribunal_checklist_md}

### Macro-Adjusted Valuation
{macro_val or "N/A"}

---

## 🔗 References & Sources
{references_md}

---

## 📚 Appendix: Core Terminology

| Term | Definition |
|------|------------|
| **CAGR** | Compound Annual Growth Rate (年均复合增长率) |
| **NDR** | Net Dollar Retention (净收入留存率) |
| **RPO** | Remaining Performance Obligations (剩余履约义务 - 未来收入) |
| **PEG** | PE / Growth Rate (市盈率相对盈利增长比率) |
| **Sandbagging** | Management strategy of hiding real potential (扮猪吃虎) |
| **Ignition** | Volume-backed breakout (点火 - 伴随巨大成交量的突破) |
| **SMA20** | 20-Day Simple Moving Average (20日均线 - 生命线) |
| **RVol** | Relative Volume = Today's Vol / 20-Day Avg Vol |

---
*Generated by MGP V3.5 Blue Sky Engine*
"""
    return content

def main():
    parser = argparse.ArgumentParser(description="MGP V3.5 Singularity Edition")
    parser.add_argument("--tickers", type=str, default="INTC", help="Comma-separated tickers")
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
