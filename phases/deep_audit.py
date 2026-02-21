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
from tools.lang import get_lang_instruction
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
        self._lang_instruction = get_lang_instruction(data)
        
        metrics = DeepAuditData()
        
        # Fetch Data
        income_annual = self.fmp.get_income_statement(ticker, period='annual', limit=5)
        income_quarterly = self.fmp.get_income_statement(ticker, period='quarter', limit=10)
        cash_flow_quarterly = self.fmp.get_cash_flow_statement(ticker, period='quarter', limit=10)
        balance_sheet_quarterly = self.fmp.get_balance_sheet(ticker, period='quarter', limit=5)
        
        # Identity (如果外部未传入，则内部识别，但架构上建议 main 传入或在此处统一)
        if not identifier_data:
            profile = self.fmp.get_profile(ticker)
            identifier_data = self.identify_business_model(data, profile)
            
        model = identifier_data.business_model
        print(f"    - Audit Protocol: {model.value}")
        
        self._analyze_historical_growth(metrics, income_annual, income_quarterly, cash_flow_quarterly)
        self._analyze_segment_specific(ticker, model, metrics, income_quarterly, cash_flow_quarterly, balance_sheet_quarterly)
        cfo_divergence, insider_risk = self._analyze_lie_detector(ticker, metrics, income_quarterly, cash_flow_quarterly)
        self._evaluate_pass_fail(metrics, gatekeeper_data, cfo_divergence, insider_risk)

        return metrics

    def _analyze_historical_growth(self, metrics: DeepAuditData, income_annual: list, income_quarterly: list, cash_flow_quarterly: list) -> None:
        """========== 2. Historical Growth & Hygiene (Legacy Iron Gate) =========="""
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

    def _analyze_segment_specific(self, ticker: str, model: BusinessModel, metrics: DeepAuditData, 
                                  income_quarterly: list, cash_flow_quarterly: list, balance_sheet_quarterly: list) -> None:
        """========== 3. Segment Specific Audit (V3.5) =========="""
        
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

    def _analyze_lie_detector(self, ticker: str, metrics: DeepAuditData, income_quarterly: list, cash_flow_quarterly: list) -> tuple:
        """========== 4. Universal Lie Detector (V3.5) =========="""
        
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
        
        # B. Insider Selling (Institutional-Grade 3-Layer Analysis via FMP)
        insider_risk = False
        insider_tx = self.fmp.get_insider_trading(ticker, limit=100)
        
        if insider_tx:
            insider_risk, insider_score, insider_msg, insider_details = self._analyze_insider_selling(
                ticker, insider_tx
            )
        
        metrics.insider_selling_risk = insider_risk
        metrics.insider_score = insider_score if insider_tx else 0
        metrics.insider_selling_message = insider_msg if insider_tx else None
        metrics.insider_details = insider_details if insider_tx else None
        
        return cfo_divergence, insider_risk

    # ==================== Insider Selling Sub-Methods ====================

    # C-Level titles that represent operators (high weight)
    # Use regex word-boundary patterns to avoid substring collisions (e.g., 'cto' in 'director')
    _C_LEVEL_PATTERNS = [
        r'\bceo\b', r'\bcfo\b', r'\bcoo\b', r'\bcto\b', r'\bcmo\b', r'\bcio\b', r'\bcpo\b',
        r'\bchief\b', r'\bpresident\b', r'\bevp\b', r'\bsvp\b', r'\bfounder\b',
        r'\bexecutive vice president\b', r'\bsenior vice president\b',
        r'\bgeneral counsel\b', r'\btreasurer\b'
    ]
    # Financial investor titles (low weight / ignore)
    _INVESTOR_PATTERNS = [r'\b10%', r'\bowner\b', r'\bdirector\b']

    def _classify_owner_role(self, type_of_owner: str) -> str:
        """
        Layer 1: 角色权重过滤
        Returns 'operator' (high risk) or 'investor' (low risk / ignorable)
        """
        owner_lower = (type_of_owner or '').lower()
        # Check C-Level first
        for pattern in self._C_LEVEL_PATTERNS:
            if re.search(pattern, owner_lower):
                return 'operator'
        # Check investor keywords
        for pattern in self._INVESTOR_PATTERNS:
            if re.search(pattern, owner_lower):
                # Double-check: they might also hold a C-Level role (e.g., "10% Owner, CEO")
                for c_pattern in self._C_LEVEL_PATTERNS:
                    if re.search(c_pattern, owner_lower):
                        return 'operator'
                return 'investor'
        return 'unknown'

    def _calc_disposition_intensity(self, shares_sold: int, shares_owned_after: int) -> float:
        """
        Layer 2: 身家性命占比
        Intensity = Shares_Sold / (Shares_Owned_After + Shares_Sold)
        """
        total = shares_owned_after + shares_sold
        if total <= 0:
            return 0.0
        return shares_sold / total

    def _get_price_return_6m(self, ticker: str) -> float:
        """
        Layer 3: 获取过去 6 个月的股价涨跌幅
        Returns float, e.g. -0.25 means down 25%
        """
        from datetime import datetime, timedelta
        today = datetime.now()
        from_date = (today - timedelta(days=180)).strftime('%Y-%m-%d')
        to_date = today.strftime('%Y-%m-%d')

        prices = self.fmp.get_historical_price_daily(ticker, from_date, to_date)
        if not prices or len(prices) < 2:
            return 0.0

        # prices sorted ascending by date
        oldest_close = prices[0].get('close', 0)
        latest_close = prices[-1].get('close', 0)
        if oldest_close <= 0:
            return 0.0
        return (latest_close - oldest_close) / oldest_close

    def _analyze_insider_selling(self, ticker: str, insider_tx: list) -> tuple:
        """
        机构级内部人售卖分析 (Institutional-Grade Insider Selling Analysis)
        
        Layer 1: 角色权重 — Operator vs Investor
        Layer 2: 抛售力度 — Disposition Intensity
        Layer 3: 价格行为背离 — Selling into Strength vs Weakness
        Final:   LLM Agent — 10b5-1 / Tax / Panic verdict
        
        Returns: (insider_risk: bool, score: int, message: str, details: dict)
        """
        # ---- Filter: only Disposition (sells), exclude M-Exempt (option exercise) ----
        sells = [
            t for t in insider_tx
            if t.get('acquisitionOrDisposition') == 'D'
            and t.get('transactionType') in ('S-Sale', 'S-Sale+OE')
            and t.get('securityName', '').lower().startswith('common stock')
        ]
        
        if not sells:
            print("      ✓ No insider sells detected.")
            return False, 0, None, None
        
        # ===== Layer 1: Role-Weight Filtering =====
        operator_sells = []
        investor_sells = []
        for s in sells:
            role = self._classify_owner_role(s.get('typeOfOwner', ''))
            s['_role'] = role
            if role == 'operator':
                operator_sells.append(s)
            else:
                investor_sells.append(s)
        
        print(f"      [Insider] Total sells: {len(sells)} | Operators: {len(operator_sells)} | Investors/Other: {len(investor_sells)}")
        
        # If only investors (VC/PE exit), low risk
        if not operator_sells:
            print("      ✓ Only investor/VC exits, no operator sells. PASS.")
            return False, 0, "Only VC/PE exits", {
                'total_sells': len(sells),
                'operator_sells': 0,
                'investor_sells': len(investor_sells),
                'verdict': 'PASS - investor exit only'
            }
        
        # Check threshold: need > N operator sells to warrant deep analysis
        if len(operator_sells) <= config.INSIDER_SELL_COUNT_THRESHOLD:
            print(f"      ✓ Operator sells ({len(operator_sells)}) below threshold ({config.INSIDER_SELL_COUNT_THRESHOLD}). PASS.")
            return False, 0, None, None
        
        print(f"      [Insider] {len(operator_sells)} operator sells exceed threshold. Deep analysis...")
        
        # ===== Layer 2: Disposition Intensity ("Skin in the Game") =====
        # Group by person, calculate per-person intensity
        person_intensity = {}
        for s in operator_sells:
            name = s.get('reportingName', 'Unknown')
            shares_sold = abs(s.get('securitiesTransacted', 0))
            shares_after = s.get('securitiesOwned', 0)
            intensity = self._calc_disposition_intensity(shares_sold, shares_after)
            
            if name not in person_intensity:
                person_intensity[name] = {
                    'title': s.get('typeOfOwner', ''),
                    'total_sold': 0,
                    'max_intensity': 0.0,
                    'transactions': 0
                }
            person_intensity[name]['total_sold'] += shares_sold
            person_intensity[name]['max_intensity'] = max(person_intensity[name]['max_intensity'], intensity)
            person_intensity[name]['transactions'] += 1
        
        # Find the worst offender
        max_intensity = 0.0
        worst_person = None
        for name, info in person_intensity.items():
            if info['max_intensity'] > max_intensity:
                max_intensity = info['max_intensity']
                worst_person = name
            print(f"        {name} ({info['title']}): {info['transactions']} sells, "
                  f"max intensity {info['max_intensity']:.1%}")
        
        # Score based on intensity
        intensity_score = 0  # 0=clean
        if max_intensity >= config.INSIDER_INTENSITY_RED_FLAG:
            intensity_score = 3
            print(f"      🚩 CRITICAL: {worst_person} disposed >{config.INSIDER_INTENSITY_RED_FLAG:.0%} of holdings!")
        elif max_intensity >= config.INSIDER_INTENSITY_WARNING:
            intensity_score = 2
            print(f"      ⚠️ WARNING: {worst_person} disposed >{config.INSIDER_INTENSITY_WARNING:.0%} of holdings")
        elif max_intensity >= config.INSIDER_INTENSITY_PASS:
            intensity_score = 1
            print(f"      ✓ Minor: Max intensity {max_intensity:.1%} (asset allocation range)")
        else:
            print(f"      ✓ Negligible: Max intensity {max_intensity:.1%}")
        
        # ===== Layer 3: Price Behavior Divergence =====
        price_return_6m = self._get_price_return_6m(ticker)
        print(f"      [Insider] 6M Price Return: {price_return_6m:.1%}")
        
        selling_into_weakness = False
        if price_return_6m <= config.INSIDER_PRICE_DROP_DANGER and len(operator_sells) > config.INSIDER_SELL_COUNT_THRESHOLD:
            selling_into_weakness = True
            # Bump up score if selling into weakness
            intensity_score = max(intensity_score, 2)
            print(f"      🚩 DANGER: Operators selling while stock down {price_return_6m:.1%}! (Capitulation signal)")
        elif price_return_6m > 0.30:
            # Stock near ATH, selling is more forgivable
            if intensity_score >= 2:
                intensity_score = max(intensity_score - 1, 1)
            print(f"      ✓ Stock up {price_return_6m:.1%} in 6M. Selling is rational profit-taking.")

        # ===== Build context for LLM Agent =====
        # Aggregate data summary for the prompt
        top_sellers = sorted(person_intensity.items(), key=lambda x: x[1]['max_intensity'], reverse=True)[:5]
        sellers_summary = "\n".join([
            f"  - {name} ({info['title']}): {info['transactions']} sells, "
            f"max single-txn intensity {info['max_intensity']:.1%}, total shares sold: {info['total_sold']:,}"
            for name, info in top_sellers
        ])
        
        # ===== Final: LLM Agent Verdict (Search + Judge) =====
        if intensity_score >= 2:
            print(f"      [Insider] Score={intensity_score}. Agent searching for context...")
            query = f"{ticker} insider executive selling reason 10b5-1 tax plan stock sale"
            try:
                results = self.search.search(query, max_results=5, days=90)
                news_context = "\n".join([
                    f"- {r.get('title', '')}: {r.get('content', '')}" for r in results
                ])[:3000] if results else "No relevant news found."
                
                prompt = f"""
                Company {ticker} has significant insider selling activity.
                
                QUANTITATIVE FACTS (from SEC Form 4):
                - 6-Month Price Return: {price_return_6m:.1%}
                - Selling into weakness: {"YES" if selling_into_weakness else "NO"}
                - Top sellers:
                {sellers_summary}
                
                CONTEXT RULES for your judgment:
                1. WHO? Is this a Founder/CEO/CFO selling, or early investor (VC/PE) exiting?
                2. HOW MUCH? Is this a liquidation (>50% of holdings), or nibbling (<5%)?
                3. TIMING? Are they selling after a big run-up (profit taking), or during a decline (capitulation)?
                4. Is there any evidence of a 10b5-1 pre-planned trading plan?
                
                NEWS CONTEXT:
                {news_context}
                
                Based on ALL evidence above, output one of:
                - "PASS - <brief reason>" if routine (10b5-1, tax, option exercise, small %, profit taking after rally)
                - "WARNING - <brief reason>" if ambiguous but not alarming
                - "FAIL - <brief reason>" if panic selling, capitulation, or unexplained large disposal
                
                {self._lang_instruction}
                """
                
                decision = self.llm.analyze_text(
                    prompt, system_prompt="You are an institutional equity analyst specializing in insider trading patterns."
                ).strip()
                
                if decision.upper().startswith("FAIL"):
                    insider_risk = True
                    final_score = max(intensity_score, 3)
                    reason = decision.split("-", 1)[-1].strip() if "-" in decision else "Unexplained insider selling"
                    print(f"      🚩 INSIDER VERDICT: FAIL - {reason}")
                elif decision.upper().startswith("WARNING"):
                    insider_risk = False  # Not a hard fail, but tracked
                    final_score = max(intensity_score, 2)
                    reason = decision.split("-", 1)[-1].strip() if "-" in decision else "Ambiguous insider selling"
                    print(f"      ⚠️ INSIDER VERDICT: WARNING - {reason}")
                else:
                    insider_risk = False
                    final_score = min(intensity_score, 1)
                    reason = decision.split("-", 1)[-1].strip() if "-" in decision else "Routine/10b5-1"
                    print(f"      ✓ INSIDER VERDICT: PASS - {reason}")
                    
            except Exception as e:
                print(f"      [Insider] Agent failed: {e}. Using quantitative score only.")
                insider_risk = intensity_score >= 3
                final_score = intensity_score
                reason = f"Agent failed, quant score={intensity_score}"
        else:
            insider_risk = False
            final_score = intensity_score
            reason = "Below alert threshold"
            print(f"      ✓ INSIDER CLEARED: Score={intensity_score}, no agent needed.")
        
        details = {
            'total_sells': len(sells),
            'operator_sells': len(operator_sells),
            'investor_sells': len(investor_sells),
            'max_intensity': max_intensity,
            'worst_person': worst_person,
            'price_return_6m': price_return_6m,
            'selling_into_weakness': selling_into_weakness,
            'person_breakdown': {name: info for name, info in top_sellers},
            'verdict': reason
        }
        
        return insider_risk, final_score, reason, details

    def _evaluate_pass_fail(self, metrics: DeepAuditData, gatekeeper_data: GatekeeperData, cfo_divergence: bool, insider_risk: bool) -> None:
        """========== 5. Pass/Fail Logic (V3.5 Red Flag System) =========="""
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
                reasons.append("🚩 Low Growth (CAGR/Q-Growth) & No Profit Leverage")
             
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
            msg = metrics.insider_selling_message or ">3 trans"
            reasons.append(f"🚩 Insider Selling Risk ({msg})")
        
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

deepAudit = DeepAudit()  # default clients; main.py passes explicit clients

if __name__ == "__main__":
    from core.data_models import CompanyData, GatekeeperData, MacroMode

    ticker = "AXON"
    print(f"\n{'='*60}")
    print(f"  Deep Audit Standalone Test: {ticker}")
    print(f"{'='*60}\n")

    # 构造最小 CompanyData
    company = CompanyData(
        ticker=ticker,
        gatekeeper=GatekeeperData(
            sector_check_passed=True,
            macro_mode=MacroMode.NEUTRAL,
            passed=True
        )
    )

    audit = DeepAudit()

    # 1) 商业模式识别
    identifier = audit.identify_business_model(company)
    company.identifier = identifier
    print(f"\n  Business Model: {identifier.business_model.value}")
    print(f"  KPIs: {identifier.specific_kpis}")

    # 2) 深度审计
    result = audit.analyze(company)
    company.deep_audit = result

    print(f"\n{'='*60}")
    print(f"  RESULTS")
    print(f"{'='*60}")
    print(f"  Passed:        {result.passed}")
    print(f"  Fail Reason:   {result.fail_reason or 'None'}")
    print(f"  Red Flags:     {result.red_flags}")
    print(f"  Rev CAGR:      {f'{result.revenue_cagr_ny:.1%}' if result.revenue_cagr_ny else 'N/A'}")
    print(f"  EPS CAGR:      {f'{result.eps_cagr_ny:.1%}' if result.eps_cagr_ny else 'N/A'}")
    print(f"  Q/Q Growth:    {f'{result.revenue_growth_current_q:.1%}' if result.revenue_growth_current_q else 'N/A'}")
    print(f"  PEG:           {f'{result.peg_ratio:.2f}' if result.peg_ratio else 'N/A'}")
    print(f"  Rule of 40:    {f'{result.rule_of_40:.1%}' if result.rule_of_40 else 'N/A'}")
    print(f"  SBC/Rev:       {f'{result.sbc_revenue_ratio:.1%}' if result.sbc_revenue_ratio else 'N/A'}")
    print(f"  Insider Risk:  {result.insider_selling_risk} (Score: {result.insider_score}/3)")
    print(f"  Insider Msg:   {result.insider_selling_message or 'Clean'}")
    if result.insider_details:
        d = result.insider_details
        print(f"    Operator Sells: {d.get('operator_sells', 0)}")
        print(f"    Max Intensity:  {d.get('max_intensity', 0):.1%}")
        print(f"    6M Price Ret:   {d.get('price_return_6m', 0):.1%}")
        print(f"    Into Weakness:  {d.get('selling_into_weakness', False)}")
    print(f"{'='*60}\n")
