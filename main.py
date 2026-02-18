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
from tools.deep_search import DeepSearchClient
from core.data_models import CompanyData
from phases.generate_report import generate_report_content_v35

def analyze_ticker_v35(ticker: str, fmp: FMPClient, llm: LLMClient, search: SearchClient, yahoo: YahooClient,
                       deep: DeepSearchClient, force_deep_dive: bool = False, deep_search: bool = False) -> CompanyData:
    
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
    
    # ========== Phase 3: Intelligence & Blue Sky ==========
    print(f"\n[{ticker}] Phase 3: Intelligence & Blue Sky...")
    
    # Deep Search Integration in Intelligence
    # Pass deep_client to Intelligence
    intel = Intelligence(llm, search, fmp, deep)
    data.intelligence = intel.gather(ticker, data.identifier, data.gatekeeper, data.references, deep_search=deep_search)

    # ========== Phase 5: Catalysts & Waves ==========
    print(f"\n[{ticker}] Phase 5: Catalysts & Waves...")
    catalysts_analyzer = CatalystsAnalyzer(llm, search, deep)
    catalyst_data = catalysts_analyzer.analyze(ticker, data.company_name, data.references, deep_search=deep_search)
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



def main():
    parser = argparse.ArgumentParser(description="MGP V3.5 Singularity Edition")
    parser.add_argument("--tickers", type=str, default="INTC", help="Comma-separated tickers")
    parser.add_argument("--force", action="store_true", help="Force deep dive")
    parser.add_argument("--scan_mid_cap", default=False,  action="store_true", help="Scan for Mid-Cap (10B-50B) stocks using FMP Screener")
    parser.add_argument("--deep_search", "-d", action="store_true", default=False, help="Enable Deep Search Mode (4-module intelligence system)")
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
    
    # Singletons
    deep_client = DeepSearchClient(search, llm)
    
    for ticker in tickers:
        try:
            data = analyze_ticker_v35(ticker, fmp, llm, search, yahoo, deep_client, args.force, args.deep_search)
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
