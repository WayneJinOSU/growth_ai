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
    """Generate V3.5 Report"""
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
    
    content = f"""# MGP V3.5 Singularity Report: {data.ticker}
**Date:** {datetime.now().strftime("%Y-%m-%d")}
**Verdict:** {decision}
**Physics:** {physics_status}
**Price:** ${data.current_price:.2f}

## Executive Summary
{data.tribunal.rationale if data.tribunal else 'N/A'}

## 1. The Gatekeeper (Macro & Iron Rule)
- **Macro Mode:** {data.gatekeeper.macro_mode.value if data.gatekeeper else 'N/A'}
- **Sector Check:** {'✅ Passed' if data.gatekeeper and data.gatekeeper.sector_check_passed else '❌ Failed'}
- **Future 20% Rule:** {'✅ Passed' if data.gatekeeper and data.gatekeeper.future_revenue_cagr_3y and data.gatekeeper.future_revenue_cagr_3y > 0.2 else '⚠️ Warning'}

## 2. Deep Audit (Hygiene)
- **Result:** {'✅ Passed' if data.deep_audit and data.deep_audit.passed else '❌ Failed'}
- **Fail Reason:** {data.deep_audit.fail_reason if data.deep_audit else 'N/A'}
- **Rule of 40:** {f"{data.deep_audit.rule_of_40:.1%}" if data.deep_audit and data.deep_audit.rule_of_40 else 'N/A'}
- **Inventory Health:** {data.deep_audit.inventory_health if data.deep_audit else 'N/A'}
- **Insider Risk:** {'⚠️ DETECTED' if data.deep_audit and data.deep_audit.insider_selling_risk else 'None'}

## 3. Shadow Audit
- **King Makers:** {'✅ Yes' if data.shadow_audit and data.shadow_audit.has_king_maker_clients else 'No'}
- **Organic Growth:** {'✅ Confirmed' if data.shadow_audit and data.shadow_audit.organic_growth_confirmed else 'Unconfirmed'}
- **Fake Tech:** {'⚠️ YES' if data.shadow_audit and data.shadow_audit.is_fake_tech else 'No'}

## 4. Physics (VPA)
- **Ignition:** {'✅ YES' if data.physics and data.physics.is_ignition else 'No'}
- **Accumulation:** {'✅ YES' if data.physics and data.physics.is_accumulation else 'No'}
- **RVol:** {f"{data.physics.relative_volume:.1f}x" if data.physics and data.physics.relative_volume else 'N/A'}

## 5. Valuation & Catalysts
- **Moat:** {data.intelligence.product_moat if data.intelligence else 'N/A'}
- **Valuation:** {data.intelligence.kpi_values.get('macro_valuation_analysis', 'N/A') if data.intelligence else 'N/A'}
- **Catalysts:** {', '.join(data.intelligence.catalysts.upcoming_events) if data.intelligence and data.intelligence.catalysts else 'N/A'}

---
*Generated by MGP V3.5 Singularity Engine*
"""
    return content

def main():
    parser = argparse.ArgumentParser(description="MGP V3.5 Singularity Edition")
    parser.add_argument("--tickers", type=str, default="DUOL", help="Comma-separated tickers")
    parser.add_argument("--force", action="store_true", help="Force deep dive")
    args = parser.parse_args()
    
    tickers = [t.strip().upper() for t in args.tickers.split(",")]
    
    fmp = FMPClient()
    llm = LLMClient()
    search = SearchClient()
    yahoo = YahooClient()
    
    results = []
    
    for ticker in tickers:
        try:
            data = analyze_ticker_v35(ticker, fmp, llm, search, yahoo, args.force)
            results.append(data.model_dump())
            
            # Save Report
            if data.tribunal:
                report = generate_report_content_v35(data)
                filename = f"REPORT_V3.5_{ticker}_{datetime.now().strftime('%Y-%m-%d')}.md"
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
