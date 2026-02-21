from core.data_models import CompanyData
from datetime import datetime

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

        # Insider Analysis Sub-Section
        insider_status = "No" 
        if da.insider_selling_risk:
            insider_status = "🚩 RED FLAG"
        elif da.insider_score >= 2:
            insider_status = "⚠️ WARNING"
        elif da.insider_score == 1:
            insider_status = "✓ Minor"
        
        insider_sub = ""
        if da.insider_details:
            d = da.insider_details
            insider_sub = f"""
#### Insider Selling Breakdown (Institutional-Grade)
| Dimension | Value |
|-----------|-------|
| Total Sells (Form 4) | {d.get('total_sells', 'N/A')} |
| Operator (C-Level) Sells | {d.get('operator_sells', 'N/A')} |
| Investor (VC/PE/Director) Sells | {d.get('investor_sells', 'N/A')} |
| Max Disposition Intensity | {f"{d['max_intensity']:.1%}" if d.get('max_intensity') is not None else 'N/A'} |
| Worst Offender | {d.get('worst_person', 'N/A')} |
| 6M Price Return | {f"{d['price_return_6m']:.1%}" if d.get('price_return_6m') is not None else 'N/A'} |
| Selling into Weakness | {"🚩 YES" if d.get('selling_into_weakness') else "No"} |
| **LLM Verdict** | **{d.get('verdict', 'N/A')}** |
"""
        elif da.insider_selling_message:
            insider_sub = f"\n> **Insider Note:** {da.insider_selling_message}\n"
        
        deep_audit_details = f"""
### Detailed Metrics
| Metric | Value | Formula/Source |
|--------|-------|----------------|
| Revenue CAGR (N-Year) | {f"{da.revenue_cagr_ny:.1%}" if da.revenue_cagr_ny is not None else "N/A"} | (Latest Rev / Oldest Rev)^(1/N) - 1 |
| EPS CAGR (N-Year) | {f"{da.eps_cagr_ny:.1%}" if da.eps_cagr_ny is not None else "N/A"} | (Latest EPS / Oldest EPS)^(1/N) - 1 |
| Q/Q Revenue Growth | {f"{da.revenue_growth_current_q:.1%}" if da.revenue_growth_current_q is not None else "N/A"} | (Current Q Rev - YoY Q Rev) / YoY Q Rev |
| PEG Ratio (TTM) | {f"{da.peg_ratio:.2f}" if da.peg_ratio is not None else "N/A"} | FMP Ratios TTM |
| SBC / Revenue | {f"{da.sbc_revenue_ratio:.1%}" if da.sbc_revenue_ratio is not None else "N/A"} | TTM SBC / TTM Revenue |
| Net Dilution (YoY) | {f"{da.share_count_growth:.1%}" if da.share_count_growth is not None else "N/A"} | Diluted Shares YoY Change |
| Rule of 40 | {f"{da.rule_of_40:.1%}" if da.rule_of_40 is not None else "N/A"} | Rev Growth + FCF Margin |
| NDR | {f"{da.ndr:.0%}" if da.ndr is not None else "N/A"} | SaaS Net Dollar Retention |
| RPO Growth | {f"{da.rpo_growth:.0%}" if da.rpo_growth is not None else "N/A"} | SaaS RPO YoY |
| Inventory Health | {da.inventory_health or "N/A"} | Inv Days trend vs Gross Margin |
| Book-to-Bill | {f"{da.book_to_bill:.2f}x" if da.book_to_bill is not None else "N/A"} | Hardware demand signal |
| Take Rate Trend | {da.take_rate_trend or "N/A"} | Marketplace monetization |
| Insider Selling | {insider_status} (Score: {da.insider_score}/3) | FMP SEC Form 4 + 3-Layer Analysis |
| Red Flags Total | {da.red_flags} | ≥ 2 = FAIL |
{insider_sub}"""

    
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
        
        # KPI Values sub-section
        kpi_md = ""
        if intel.kpi_values:
            kpi_lines = [f"| {k} | {v} |" for k, v in intel.kpi_values.items()]
            kpi_md = "\n### Key Performance Indicators\n| KPI | Value |\n|-----|-------|\n" + "\n".join(kpi_lines)
        
        intelligence_details = f"""
### Management Integrity
{intel.management_integrity or "N/A"}

### Competitive Moat
{intel.product_moat or "N/A"}

### Insider Activity
{intel.insider_activity or "N/A"}

### Dislocation Context
{intel.dislocation_context or "N/A"}
{kpi_md}
"""
    
    # Build Blue Sky Details (Phase 4)
    blue_sky_details = ""
    if data.blue_sky_phase and data.blue_sky_phase.blue_sky:
        bs = data.blue_sky_phase.blue_sky
        blue_sky_details = f"""
### TAM Explosion Logic
{bs.tam_expansion or "N/A"}

### Second Growth Curve (R&D Effectiveness)
{bs.rnd_effectiveness or "N/A"}

- **Strong Second Curve Confirmed:** {"✅ Yes" if bs.is_strong_second_curve else "No"}
"""

    # Build Catalysts & Waves Details (Phase 5)
    catalysts_details = ""
    if data.catalysts:
        cat = data.catalysts
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

### Supplementary Signals
- **Variant Perception:** {cat.variant_perception or "N/A"}
- **Coattail Effect:** {cat.coattail_effect or "N/A"}
"""

    # Build Strategic Pricing Details (Phase 6)
    strategy_details = ""
    if data.strategic_pricing:
        sp = data.strategic_pricing
        strategy_details = f"""
### Step 1: Valuation Scrub
- **Adjusted PE:** {f"{sp.adjusted_pe:.1f}" if sp.adjusted_pe is not None else "N/A"}
- **Reason:** {sp.adjustment_reason or "No adjustment"}

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
| SMA 50 | ${(p.sma_50 if p.sma_50 else 0):.2f} | 中期趋势线 |
| SMA 200 | ${(p.sma_200 if p.sma_200 else 0):.2f} | 长期趋势线 |
| Relative Volume | {f"{p.relative_volume:.1f}x" if p.relative_volume else "N/A"} | Vol / Avg Vol 20 |
| Daily Range | {f"{p.daily_range*100:.1f}%" if p.daily_range else "N/A"} | (High - Low) / Close |
| Close Strength | {f"{p.close_strength:.1%}" if p.close_strength else "N/A"} | (Close - Low) / (High - Low) |
| Price vs SMA20 | {"Above ✅" if p.current_price and p.sma_20 and p.current_price > p.sma_20 else "Below ⚠️"} | Trend |
| Days Below SMA20 | {p.days_below_sma20} | 连续跌破天数 |
| Days Below SMA50 | {p.days_below_sma50} | 连续跌破天数 |

### Signal Analysis
| Form | Feature | Meaning | Status |
|------|---------|---------|--------|
| 📦 Accumulation | Range < 2% + RVol > 1.5 | Quiet Accumulation | {"✅ DETECTED" if p.is_accumulation else "NOT MET"} |
| 🚀 Ignition | Price > SMA20 + RVol > 2.0 + Strong Close | Momentum Ignition | {"✅ DETECTED" if p.is_ignition else "NOT MET"} |
| 📉 Broken Trend | Close < SMA50 for 3+ days | Trend Death | {"⚠️ YES" if p.is_broken_trend else "NO"} |
| ⚡ High Risk | High RVol on down days | Institutional Dumping | {"⚠️ YES" if p.is_high_risk else "NO"} |
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
    if data.blue_sky_phase and data.blue_sky_phase.macro_valuation_analysis:
        macro_val = data.blue_sky_phase.macro_valuation_analysis

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


    content = f"""# MGP V3.5 Blue Sky Report: {data.ticker}{f" — {data.company_name}" if data.company_name else ""}
**Date:** {datetime.now().strftime("%Y-%m-%d")}
**Verdict:** {decision} ({data.tribunal.confidence.value if data.tribunal else "N/A"} Confidence)
**Strategic Definition:** {strategic_def or "N/A"}
**Physics:** {physics_status}
**Price:** ${(data.current_price if data.current_price else 0):.2f} | **Market Cap:** {f"${data.market_cap/1e9:.1f}B" if data.market_cap else "N/A"}

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

### Core Judgments
| Dimension | Result |
|-----------|--------|
| Growth Thesis Intact | {"✅ Yes" if data.tribunal and data.tribunal.growth_thesis_intact else "❌ No"} |
| Valuation Fit | {"✅ Yes" if data.tribunal and data.tribunal.valuation_fit else "❌ No"} |
| True Discount | {"✅ Yes" if data.tribunal and data.tribunal.is_true_discount else "❌ No"} |

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

if __name__ == "__main__":
    print(datetime.now().strftime("%Y-%m-%d"))