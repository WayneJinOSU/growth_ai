"""
Phase 1: The Deep Audit (深度审计) - V3.5 Singularity
=====================================================
替代原 Iron Gate。针对不同商业模式的物理特性，进行"核磁共振"级体检。

核心检查项:
1. 商业模式分类 (Identity - 增强版)
2. 细分领域审计 (NDR, Rule of 40, Book-to-Bill, Inventory, Take Rate)
3. 财务铁律 (CAGR, 减速熔断, SBC 警戒线)
4. 全局测谎仪 (CFO背离, 内部人抛售)
"""
from tools.fmp import FMPClient
from tools.yahoo import YahooClient
from tools.llm import LLMClient
from tools.search import SearchClient
from core.data_models import DeepAuditData, BusinessModel, IdentifierData, GatekeeperData
import config
import re

class DeepAudit:
    """
    深度审计器：MGP V3.5 策略的第一道关卡 (原 Iron Gate 升级版)
    """

    def __init__(self, fmp_client: FMPClient = None, llm_client: LLMClient = None,
                 yahoo_client: YahooClient = None, search_client: SearchClient = None):
        self.fmp = fmp_client or FMPClient()
        self.llm = llm_client or LLMClient()
        self.yahoo = yahoo_client or YahooClient()
        self.search = search_client or SearchClient()

    def _calculate_cagr(self, start_value: float, end_value: float, years: int) -> float:
        if start_value <= 0 or years <= 0:
            return 0.0
        return (end_value / start_value) ** (1 / years) - 1

    def _parse_percentage(self, text: str) -> float | None:
        """Extract a percentage value from LLM output like '120%' or '1.2x' → 1.20"""
        if not text or text.strip().upper() == "N/A":
            return None
        match = re.search(r'([\d]+(?:\.[\d]+)?)\s*%', text)
        if match:
            return float(match.group(1)) / 100.0
        match = re.search(r'([\d]+(?:\.[\d]+)?)\s*x', text, re.IGNORECASE)
        if match:
            return float(match.group(1))
        try:
            val = float(re.search(r'[\d]+(?:\.[\d]+)?', text).group())
            if val > 10:
                return val / 100.0
            return val
        except (AttributeError, ValueError):
            return None

    def _fetch_specific_metric(self, ticker: str, metric_name: str, keywords: list,
                               days: int = 90) -> str:
        """
        Tavily + LLM: 搜索并提取特定非 GAAP 指标 (NDR, RPO, GMV, Book-to-Bill 等)
        """
        kw_str = " ".join(keywords)
        query = f"{ticker} {metric_name} {kw_str} latest quarter earnings results"

        print(f"      [Tavily] Fetching {metric_name}...")
        results = self.search.search(query, max_results=5, days=days)

        if not results:
            print(f"      [Tavily] No results for {metric_name}")
            return "N/A"

        context = "\n---\n".join([
            f"[{i+1}] {r.get('title','')}\n{r.get('content','')}"
            for i, r in enumerate(results)
        ])[:3000]

        prompt = f"""
        Based on the search results below for {ticker}, extract the latest value for: {metric_name}.
        Keywords to look for: {keywords}

        RULES:
        - Return ONLY the value with its unit and the quarter/date, e.g. "120% (Q3 2025)" or "$1.2B (FY2025)".
        - If there are two periods available, include both to show the trend, e.g. "115% (Q2) → 120% (Q3 2025)".
        - If the metric is genuinely not mentioned in the text, return EXACTLY "N/A".
        - Do NOT speculate or calculate. Only extract explicitly stated numbers.

        Search Results:
        {context}
        """
        try:
            value = self.llm.analyze_text(
                prompt, system_prompt="Extract financial metric values precisely. Direct output only."
            ).strip()
            if len(value) > 200:
                value = value[:200]
            return value
        except Exception as e:
            print(f"      [Error] LLM extraction failed for {metric_name}: {e}")
            return "N/A"

    def identify_business_model(self, data, profile: dict = None) -> IdentifierData:
        """
        V3.5 Identity Engine: 确定公司的物理法则
        结合 FMP Profile 和 LLM 语义分析
        """
        ticker = data.ticker
        if profile is None:
            profile = data.company_profile
        print(f"    - Identifying Business Model DNA...")
        
        # 1. 尝试规则判断 (快速路径)
        if profile:
            industry = (profile.get('industry') or "").lower()
            sector = (profile.get('sector') or "").lower()
            desc = (profile.get('description') or "").lower()
            
            # Hardware
            if "semiconductor" in industry or "hardware" in industry or "equipment" in industry:
                return IdentifierData(business_model=BusinessModel.HARDWARE, specific_kpis=["Inventory", "Gross Margin"])
            
            # SaaS (High Prob)
            if "software" in industry and ("subscription" in desc or "saas" in desc):
                return IdentifierData(business_model=BusinessModel.SAAS, specific_kpis=["RPO", "Billings"])
                
        # 2. LLM 判断 (精准路径)
        # 如果规则不明确，或者为了更精准的 KPI
        description = profile.get('description', '') if profile else f"Company {ticker}"
        
        prompt = f"""
        Analyze {ticker} based on: {description[:1000]}...
        
        Classify into ONE V3.5 Business Model:
        - SaaS (Software/Subscription/Cyber)
        - Consumption (Usage-based/Cloud Infra like Snowflake/AWS)
        - Marketplace (Platform/Gig Economy like Uber/Airbnb)
        - Advertising (Ad-driven like Meta/Google)
        - Hardware (Physical/Chips like Nvidia/Apple)
        - Other
        
        Return ONLY the Enum string (e.g. "SaaS").
        """
        
        try:
            model_str = self.llm.analyze_text(prompt, system_prompt="You are a classifier.").strip().upper()
            
            # Map back to Enum
            if "SAAS" in model_str: model = BusinessModel.SAAS
            elif "CONSUMPTION" in model_str: model = BusinessModel.CONSUMPTION
            elif "MARKETPLACE" in model_str: model = BusinessModel.MARKETPLACE
            elif "ADVERTISING" in model_str: model = BusinessModel.ADVERTISING
            elif "HARDWARE" in model_str: model = BusinessModel.HARDWARE
            else: model = BusinessModel.OTHER
            
            return IdentifierData(business_model=model)
            
        except:
            return IdentifierData(business_model=BusinessModel.OTHER)

    def analyze(self, data) -> DeepAuditData:
        """
        执行深度审计
        """
        ticker = data.ticker
        identifier_data = data.identifier
        gatekeeper_data = data.gatekeeper
        print(f"  [Phase 1] Deep Audit for {ticker} (V3.5)...")
        
        metrics = DeepAuditData()
        
        # Fetch Data
        income_annual = self.fmp.get_income_statement(ticker, period='annual', limit=5)
        income_quarterly = self.fmp.get_income_statement(ticker, period='quarter', limit=10)
        cash_flow_quarterly = self.fmp.get_cash_flow_statement(ticker, period='quarter', limit=10)
        balance_sheet_quarterly = self.fmp.get_balance_sheet(ticker, period='quarter', limit=5)
        
        # Identity (如果外部未传入，则内部识别，但架构上建议 main 传入或在此处统一)
        # 为保持接口简洁，这里假设 main 可能会先调用 identify，或者 DeepAudit 自己搞定
        # 既然 DeepAudit 负责"针对不同模式体检"，它需要知道模式。
        if not identifier_data:
            profile = self.fmp.get_profile(ticker)
            identifier_data = self.identify_business_model(data, profile)
            
        model = identifier_data.business_model
        print(f"    - Audit Protocol: {model.value}")
        
        # ========== 2. Historical Growth & Hygiene (Legacy Iron Gate) ==========
        # CAGR (Rev & EPS)
        if income_annual and len(income_annual) > 1:
            try:
                latest_rev = income_annual[0]['revenue']
                old_rev = income_annual[-1]['revenue']
                years = len(income_annual) - 1
                metrics.revenue_cagr_ny = self._calculate_cagr(old_rev, latest_rev, years)
                print(f"      Rev CAGR ({years}y): {metrics.revenue_cagr_ny:.1%}")
                
                # EPS CAGR (V3.5 Enhancement)
                latest_eps = income_annual[0].get('eps', 0)
                old_eps = income_annual[-1].get('eps', 0)
                if old_eps > 0 and latest_eps > 0:
                    metrics.eps_cagr_ny = self._calculate_cagr(old_eps, latest_eps, years)
                    print(f"      EPS CAGR ({years}y): {metrics.eps_cagr_ny:.1%}")
            except: pass
            
        # Quarterly Growth
        if income_quarterly and len(income_quarterly) >= 5:
            curr = income_quarterly[0]['revenue']
            prev = income_quarterly[4]['revenue']
            if prev > 0:
                metrics.revenue_growth_current_q = (curr - prev) / prev
                print(f"      Q Growth: {metrics.revenue_growth_current_q:.1%}")
            
        # V3.5 True Net Dilution Shield (Outstanding Shares)
        if income_annual and len(income_annual) >= 2:
            curr_shares = income_annual[0].get('weightedAverageShsOutDil', 0)
            prev_shares = income_annual[1].get('weightedAverageShsOutDil', 0)
            
            if prev_shares > 0:
                metrics.share_count_growth = (curr_shares - prev_shares) / prev_shares
                print(f"      YoY Dilution: {metrics.share_count_growth:.1%}")
        elif cash_flow_quarterly and income_quarterly:
            # Fallback to SBC ratio if shares not available
            sbc = sum(c.get('stockBasedCompensation', 0) for c in cash_flow_quarterly[:4])
            rev = sum(i.get('revenue', 0) for i in income_quarterly[:4])
            if rev > 0:
                metrics.sbc_revenue_ratio = sbc / rev
                print(f"      SBC/Rev Backup: {metrics.sbc_revenue_ratio:.1%}")
                
        # ========== 3. Segment Specific Audit (V3.5) ==========
        
        # --- A. SaaS / Cyber / AI Software ---
        if model == BusinessModel.SAAS:
            print("      [SaaS Audit] Extracting NDR & RPO via Tavily...")

            ndr_raw = self._fetch_specific_metric(
                ticker, "Net Dollar Retention",
                ["NDR", "net retention", "dollar-based net retention", "DBNR", "net revenue retention"]
            )
            ndr_val = self._parse_percentage(ndr_raw)
            if ndr_val is not None:
                metrics.ndr = ndr_val
                status = "✓ Strong" if ndr_val >= config.NDR_THRESHOLD else "⚠️ Weak"
                print(f"      NDR: {ndr_raw} → {ndr_val:.0%} ({status})")
            else:
                print(f"      NDR: {ndr_raw}")

            rpo_raw = self._fetch_specific_metric(
                ticker, "Remaining Performance Obligations growth",
                ["RPO", "remaining performance obligations", "backlog", "RPO growth"]
            )
            rpo_val = self._parse_percentage(rpo_raw)
            if rpo_val is not None:
                metrics.rpo_growth = rpo_val
                print(f"      RPO Growth: {rpo_raw} → {rpo_val:.0%}")
            else:
                print(f"      RPO Growth: {rpo_raw}")

        # --- PEG Ratio (from FMP ratios-ttm) ---
        try:
            ratios_ttm = self.fmp.get_ratios_ttm(ticker)
            if ratios_ttm:
                peg_val = ratios_ttm.get('priceToEarningsGrowthRatioTTM')
                if peg_val is not None and peg_val > 0:
                    metrics.peg_ratio = peg_val
                    print(f"      PEG Ratio (TTM): {peg_val:.2f}")
        except Exception as e:
            print(f"      [Warning] PEG Ratio fetch failed: {e}")

        # --- B. Consumption / Usage ---
        # Rule of 40: Rev Growth + FCF Margin
        if income_quarterly and cash_flow_quarterly:
            fcf = cash_flow_quarterly[0].get('freeCashFlow', 0)
            rev = income_quarterly[0].get('revenue', 1)
            fcf_margin = fcf / rev
            growth = metrics.revenue_growth_current_q or 0
            metrics.rule_of_40 = growth + fcf_margin
            
            if model in [BusinessModel.SAAS, BusinessModel.CONSUMPTION]:
                print(f"      Rule of 40: {metrics.rule_of_40:.1%}")
        
        # --- C. Hard Tech (Semi / Hardware) ---
        if model == BusinessModel.HARDWARE:
            # Inventory Death Cross: Inventory Days Rising + Gross Margin Falling
            if balance_sheet_quarterly and len(balance_sheet_quarterly) >= 2 and income_quarterly:
                inv_curr = balance_sheet_quarterly[0].get('inventory', 0)
                cogs_curr = income_quarterly[0].get('costOfRevenue', 1)
                inv_days_curr = (inv_curr / cogs_curr) * 90 if cogs_curr else 0
                
                inv_prev = balance_sheet_quarterly[1].get('inventory', 0)
                cogs_prev = income_quarterly[1].get('costOfRevenue', 1)
                inv_days_prev = (inv_prev / cogs_prev) * 90 if cogs_prev else 0
                
                gm_curr = (income_quarterly[0]['revenue'] - cogs_curr) / income_quarterly[0]['revenue']
                gm_prev = (income_quarterly[1]['revenue'] - cogs_prev) / income_quarterly[1]['revenue']
                
                print(f"      Inventory Days: {inv_days_prev:.1f} -> {inv_days_curr:.1f}")
                print(f"      Gross Margin: {gm_prev:.1%} -> {gm_curr:.1%}")
                
                if inv_days_curr > inv_days_prev * 1.1 and gm_curr < gm_prev:
                     metrics.inventory_health = "DEATH CROSS"
                     print("      ⚠️ INVENTORY DEATH CROSS DETECTED")
                else:
                     metrics.inventory_health = "Healthy"

            # Book-to-Bill Ratio (supply/demand signal)
            print("      [Hardware Audit] Extracting Book-to-Bill via Tavily...")
            btb_raw = self._fetch_specific_metric(
                ticker, "Book-to-Bill ratio",
                ["book-to-bill", "book to bill", "bookings", "new orders", "backlog", "order intake"]
            )
            btb_val = self._parse_percentage(btb_raw)
            if btb_val is not None:
                metrics.book_to_bill = btb_val
                status = "✓ Demand > Supply" if btb_val > 1.0 else "⚠️ Supply > Demand"
                print(f"      Book-to-Bill: {btb_raw} → {btb_val:.2f}x ({status})")
            else:
                print(f"      Book-to-Bill: {btb_raw}")

        # --- D. Platform / Marketplace ---
        if model == BusinessModel.MARKETPLACE:
            print("      [Marketplace Audit] Extracting Take Rate & GMV via Tavily...")

            take_rate_raw = self._fetch_specific_metric(
                ticker, "Take Rate trend",
                ["take rate", "monetization rate", "commission rate", "GMV", "gross merchandise value",
                 "gross booking value", "GTV"]
            )
            if take_rate_raw and take_rate_raw.strip().upper() != "N/A":
                metrics.take_rate_trend = take_rate_raw
                tr_lower = take_rate_raw.lower()
                if ("↑" in tr_lower or "increase" in tr_lower or "grew" in tr_lower) and \
                   ("↓" in tr_lower or "decline" in tr_lower or "decrease" in tr_lower):
                    metrics.take_rate_trend = f"⚠️ TAKE RATE TRAP: {take_rate_raw}"
                    print(f"      ⚠️ Take Rate Trap Signal: {take_rate_raw}")
                else:
                    print(f"      Take Rate: {take_rate_raw}")
            else:
                print(f"      Take Rate: {take_rate_raw}")

        # ========== 4. Universal Lie Detector (V3.5) ==========
        
        # A. CFO Divergence (NI vs CFO)
        cfo_divergence = False
        if income_quarterly and cash_flow_quarterly and len(income_quarterly)>=3 and len(cash_flow_quarterly)>=3:
            # V3.5: Require TTM or consecutive 2 quarters
            ni_curr = income_quarterly[0]['netIncome']
            ni_prev_1 = income_quarterly[1]['netIncome']
            ni_prev_2 = income_quarterly[2]['netIncome']
            cfo_curr = cash_flow_quarterly[0]['operatingCashFlow']
            cfo_prev_1 = cash_flow_quarterly[1]['operatingCashFlow']
            cfo_prev_2 = cash_flow_quarterly[2]['operatingCashFlow']
            
            # Check consecutive divergence
            div_q1 = ni_prev_1 > 0 and (ni_curr - ni_prev_1)/ni_prev_1 > 0.20 and cfo_curr < cfo_prev_1
            div_q2 = ni_prev_2 > 0 and (ni_prev_1 - ni_prev_2)/ni_prev_2 > 0.20 and cfo_prev_1 < cfo_prev_2
            
            if div_q1 and div_q2:
                cfo_divergence = True
                print("      ⚠️ CFO DIVERGENCE: Consecutive NI Spiked but CFO Dropped")
            
            # Or TTM divergence
            ni_ttm = sum(i['netIncome'] for i in income_quarterly[:4]) if len(income_quarterly)>=8 else 0
            ni_prev_ttm = sum(i['netIncome'] for i in income_quarterly[4:8]) if len(income_quarterly)>=8 else 0
            cfo_ttm = sum(c['operatingCashFlow'] for c in cash_flow_quarterly[:4]) if len(cash_flow_quarterly)>=8 else 0
            cfo_prev_ttm = sum(c['operatingCashFlow'] for c in cash_flow_quarterly[4:8]) if len(cash_flow_quarterly)>=8 else 0
            
            if ni_prev_ttm > 0 and (ni_ttm - ni_prev_ttm)/ni_prev_ttm > 0.20 and cfo_ttm < cfo_prev_ttm:
                cfo_divergence = True
                print("      ⚠️ CFO DIVERGENCE: TTM NI Grew >20% but CFO Declined")
        
        # B. Insider Selling (Yahoo)
        insider_risk = False
        insider_tx = self.yahoo.get_insider_roster(ticker)
        if insider_tx:
            sells = [t for t in insider_tx if 'Sale' in t.get('transaction', '') or 'Sell' in t.get('transaction', '')]
            if len(sells) > 3: 
                insider_risk = True
                print(f"      ⚠️ INSIDER RISK: {len(sells)} recent sell transactions")
        
        metrics.insider_selling_risk = insider_risk
        
        # ========== 5. Pass/Fail Logic (V3.5 Red Flag System) ==========
        passed = True
        reasons = []
        red_flags = 0
        
        # 1. Growth Check (Integrate Phase 0 Gatekeeper rules)
        # Check Gatekeeper's findings
        cagr_issue = gatekeeper_data and not gatekeeper_data.cagr_passed
        q_growth_issue = metrics.revenue_growth_current_q is not None and metrics.revenue_growth_current_q < config.GROWTH_THRESHOLD_QUARTER
        
        if cagr_issue or q_growth_issue:
            # Rule of 40 Exemption for SaaS/Consumption or high EPS growth
            rule40_ok = metrics.rule_of_40 and metrics.rule_of_40 > 0.40
            eps_ok = metrics.eps_cagr_ny and metrics.eps_cagr_ny > 0.20
            
            if rule40_ok or eps_ok:
                print("      ✓ Growth Exemption Activated (Rule of 40 / EPS leverage)")
            else:
                red_flags += 1
                reasons.append(f"🚩 Low Growth (CAGR/Q-Growth) & No Profit Leverage")
             
        # 2. SBC / Dilution Check
        if metrics.share_count_growth and metrics.share_count_growth > 0.05:
            red_flags += 1
            reasons.append("🚩 High Net Dilution (>5% YoY)")
        elif not metrics.share_count_growth and metrics.sbc_revenue_ratio and metrics.sbc_revenue_ratio > config.SBC_THRESHOLD_KILL:
            red_flags += 1
            reasons.append("🚩 Excessive SBC")
             
        # 3. Lie Detector
        if cfo_divergence:
            red_flags += 1
            reasons.append("🚩 CFO Divergence")
             
        if insider_risk:
            red_flags += 1
            reasons.append("🚩 Insider Selling Risk (>3 trans)")
        
        if metrics.inventory_health == "DEATH CROSS":
            red_flags += 2  # Critical failure
            reasons.append("🚩🚩 Inventory Death Cross")

        metrics.red_flags = red_flags
        
        if red_flags >= 2:
            passed = False
            metrics.fail_reason = " | ".join(reasons)
        else:
            if red_flags == 1:
                metrics.fail_reason = "Warning: " + reasons[0]
            else:
                metrics.fail_reason = None
        
        metrics.passed = passed
        
        if passed:
            if red_flags > 0:
                print(f"    - Deep Audit PASSED (with Warnings: {metrics.fail_reason})")
            else:
                print("    - Deep Audit PASSED")
        else:
            print(f"    - Deep Audit FAILED (Red Flags >= 2): {metrics.fail_reason}")

        return metrics

deepAudit = DeepAudit()  # default clients; main.py passes explicit clients