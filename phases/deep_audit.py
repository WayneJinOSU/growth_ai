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
from core.data_models import DeepAuditData, BusinessModel, IdentifierData
import config

class DeepAudit:
    """
    深度审计器：MGP V3.5 策略的第一道关卡 (原 Iron Gate 升级版)
    """

    def __init__(self, fmp_client: FMPClient, llm_client: LLMClient, yahoo_client: YahooClient = None):
        self.fmp = fmp_client
        self.llm = llm_client
        self.yahoo = yahoo_client or YahooClient()

    def _calculate_cagr(self, start_value: float, end_value: float, years: int) -> float:
        if start_value <= 0 or years <= 0:
            return 0.0
        return (end_value / start_value) ** (1 / years) - 1

    def identify_business_model(self, ticker: str, profile: dict) -> IdentifierData:
        """
        V3.5 Identity Engine: 确定公司的物理法则
        结合 FMP Profile 和 LLM 语义分析
        """
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

    def analyze(self, ticker: str, identifier_data: IdentifierData = None) -> DeepAuditData:
        """
        执行深度审计
        """
        print(f"  [Phase 1] Deep Audit for {ticker} (V3.5)...")
        
        metrics = DeepAuditData()
        
        # Fetch Data
        income_annual = self.fmp.get_income_statement(ticker, period='annual', limit=5)
        income_quarterly = self.fmp.get_income_statement(ticker, period='quarter', limit=10)
        cash_flow_quarterly = self.fmp.get_cash_flow_statement(ticker, period='quarter', limit=5)
        balance_sheet_quarterly = self.fmp.get_balance_sheet(ticker, period='quarter', limit=5)
        
        # Identity (如果外部未传入，则内部识别，但架构上建议 main 传入或在此处统一)
        # 为保持接口简洁，这里假设 main 可能会先调用 identify，或者 DeepAudit 自己搞定
        # 既然 DeepAudit 负责"针对不同模式体检"，它需要知道模式。
        if not identifier_data:
            profile = self.fmp.get_profile(ticker)
            identifier_data = self.identify_business_model(ticker, profile)
            
        model = identifier_data.business_model
        print(f"    - Audit Protocol: {model.value}")
        
        # ========== 2. Historical Growth & Hygiene (Legacy Iron Gate) ==========
        # CAGR
        if income_annual and len(income_annual) > 1:
            try:
                latest = income_annual[0]['revenue']
                old = income_annual[-1]['revenue']
                years = len(income_annual) - 1
                metrics.revenue_cagr_ny = self._calculate_cagr(old, latest, years)
                print(f"      CAGR ({years}y): {metrics.revenue_cagr_ny:.1%}")
            except: pass
            
        # Quarterly Growth
        if income_quarterly and len(income_quarterly) >= 5:
            curr = income_quarterly[0]['revenue']
            prev = income_quarterly[4]['revenue']
            metrics.revenue_growth_current_q = (curr - prev) / prev
            print(f"      Q Growth: {metrics.revenue_growth_current_q:.1%}")
            
        # SBC Check (Dilution Shield)
        if cash_flow_quarterly and income_quarterly:
            sbc = sum(c.get('stockBasedCompensation', 0) for c in cash_flow_quarterly[:4])
            rev = sum(i.get('revenue', 0) for i in income_quarterly[:4])
            if rev > 0:
                metrics.sbc_revenue_ratio = sbc / rev
                print(f"      SBC/Rev: {metrics.sbc_revenue_ratio:.1%}")
                
        # ========== 3. Segment Specific Audit (V3.5) ==========
        
        # --- A. SaaS / Cyber / AI Software ---
        if model == BusinessModel.SAAS:
            # NDR Check (via LLM inference from Earnings Call/Reports usually, here we approximate or skip if no data)
            pass

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
        
        # --- D. Platform / Marketplace ---
        if model == BusinessModel.MARKETPLACE:
            pass

        # ========== 4. Universal Lie Detector (V3.5) ==========
        
        # A. CFO Divergence (NI vs CFO)
        cfo_divergence = False
        if income_quarterly and cash_flow_quarterly and len(income_quarterly)>=2:
            ni_curr = income_quarterly[0]['netIncome']
            ni_prev = income_quarterly[1]['netIncome']
            cfo_curr = cash_flow_quarterly[0]['operatingCashFlow']
            cfo_prev = cash_flow_quarterly[1]['operatingCashFlow']
            
            # If NI grew > 20% but CFO declined
            if ni_prev > 0 and (ni_curr - ni_prev)/ni_prev > 0.20:
                if cfo_curr < cfo_prev:
                    cfo_divergence = True
                    print("      ⚠️ CFO DIVERGENCE: NI Spiked but CFO Dropped")
        
        # B. Insider Selling (Yahoo)
        insider_risk = False
        insider_tx = self.yahoo.get_insider_roster(ticker)
        if insider_tx:
            sells = [t for t in insider_tx if 'Sale' in t.get('transaction', '') or 'Sell' in t.get('transaction', '')]
            if len(sells) > 3: 
                insider_risk = True
                print(f"      ⚠️ INSIDER RISK: {len(sells)} recent sell transactions")
        
        metrics.insider_selling_risk = insider_risk
        
        # ========== 5. Pass/Fail Logic ==========
        passed = True
        reasons = []
        
        # 1. Growth Check
        if (metrics.revenue_growth_current_q and metrics.revenue_growth_current_q < config.GROWTH_THRESHOLD_QUARTER):
             passed = False
             reasons.append("Low Growth")
             
        # 2. SBC Check
        if metrics.sbc_revenue_ratio and metrics.sbc_revenue_ratio > config.SBC_THRESHOLD_KILL:
             passed = False
             reasons.append("Excessive SBC")
             
        # 3. Lie Detector
        if cfo_divergence:
             passed = False
             reasons.append("CFO Divergence")
        
        if metrics.inventory_health == "DEATH CROSS":
             passed = False
             reasons.append("Inventory Death Cross")

        metrics.passed = passed
        metrics.fail_reason = ", ".join(reasons) if reasons else None
        
        if passed:
            print("    - Deep Audit PASSED")
        else:
            print(f"    - Deep Audit FAILED: {metrics.fail_reason}")

        return metrics
