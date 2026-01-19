"""
Phase 1: Financial Forensics (财务侦探) - V3.7 Armored Sniper
=============================================================
在无法获取管理层录音的情况下，通过"财务指纹"反推"是造不出来，还是卖不出去"。

V3.7 核心检查项 ("好瓶颈"的财务指纹):
1. 库存周转测试 (Inventory Check) - 周转率稳定 = 产品仍受欢迎
2. 资本开支脉冲 (Capex Pulse) - 营收不涨 + Capex 暴涨 = 产能爬坡信号
3. 定价权测试 (Pricing Power) - 毛利率稳定 = 无需打折
4. 护城河锁定 (Moat Lock-in) - 客户在困境期会跑吗？

数据源: FMP Income Statement, FMP Balance Sheet, FMP Cash Flow
"""

from typing import List, Optional, Dict
from tools.llm import LLMClient
from tools.fmp import FMPClient
from tools.search import SearchClient
from core.data_models import (
    IdentifierData, ForensicsData, BusinessModel, MoatStrength,
    ShadowAuditData, PolygraphData
)


class Identifier:
    """
    V3.7 财务侦探：MGP 策略的第一道关卡 (Financial Forensics)
    
    职责：
    - 识别商业模式和特异性 KPI
    - 执行 V3.7 财务指纹检查 (库存、Capex、毛利率)
    - 评估护城河强度 (Moat Lock-in)
    """
    
    # 库存周转率容差 (-10%)
    INVENTORY_TURNOVER_TOLERANCE = -0.10
    
    # 毛利率最大跌幅 (3%)
    GROSS_MARGIN_MAX_DROP = 0.03
    
    # 高护城河行业
    HIGH_MOAT_KEYWORDS = [
        "SaaS", "Software", "Pharmaceuticals", "Biotechnology",
        "Semiconductor", "Medical Device", "Enterprise Software"
    ]
    
    # 低护城河行业
    LOW_MOAT_KEYWORDS = [
        "Consumer", "Retail", "Apparel", "Hardware", "Smartphone",
        "Restaurants", "Fashion"
    ]

    def __init__(self, llm_client: LLMClient, fmp_client: FMPClient = None, search_client: SearchClient = None):
        self.llm = llm_client
        self.fmp = fmp_client
        self.search = search_client

    def _calculate_inventory_turnover(self, income_data: List[Dict], balance_data: List[Dict]) -> tuple[Optional[float], Optional[float]]:
        """
        计算库存周转率
        
        公式: Inventory Turnover = COGS / Average Inventory
        
        Returns:
            (current_turnover, 3yr_avg_turnover)
        """
        if not income_data or not balance_data or len(income_data) < 1 or len(balance_data) < 2:
            return None, None
        
        try:
            # 当前年度
            cogs_current = abs(income_data[0].get('costOfRevenue', 0))
            inv_current = balance_data[0].get('inventory', 0)
            inv_prev = balance_data[1].get('inventory', 0) if len(balance_data) > 1 else inv_current
            
            if inv_current <= 0 and inv_prev <= 0:
                # 无库存的公司 (如纯软件)，跳过此检查
                return None, None
            
            avg_inv_current = (inv_current + inv_prev) / 2
            turnover_current = cogs_current / avg_inv_current if avg_inv_current > 0 else None
            
            # 计算 3 年平均
            if len(income_data) >= 3 and len(balance_data) >= 4:
                turnovers = []
                for i in range(min(3, len(income_data) - 1)):
                    cogs = abs(income_data[i].get('costOfRevenue', 0))
                    inv_i = balance_data[i].get('inventory', 0)
                    inv_i1 = balance_data[i + 1].get('inventory', 0)
                    avg_inv = (inv_i + inv_i1) / 2
                    if avg_inv > 0:
                        turnovers.append(cogs / avg_inv)
                
                avg_turnover = sum(turnovers) / len(turnovers) if turnovers else None
            else:
                avg_turnover = turnover_current
            
            return turnover_current, avg_turnover
        except Exception as e:
            print(f"      [Warning] Inventory turnover calculation failed: {e}")
            return None, None

    def _calculate_capex_pulse(self, income_data: List[Dict], cashflow_data: List[Dict]) -> tuple[Optional[float], Optional[float]]:
        """
        计算 Capex/Revenue 比率
        
        V3.7 信号: 营收不涨 + Capex 暴涨 = 产能爬坡信号
        
        Returns:
            (current_ratio, 3yr_avg_ratio)
        """
        if not income_data or not cashflow_data:
            return None, None
        
        try:
            # 当前年度
            capex_current = abs(cashflow_data[0].get('capitalExpenditure', 0))
            rev_current = income_data[0].get('revenue', 0)
            
            ratio_current = capex_current / rev_current if rev_current > 0 else None
            
            # 计算 3 年平均
            if len(income_data) >= 3 and len(cashflow_data) >= 3:
                ratios = []
                for i in range(min(3, len(income_data))):
                    capex = abs(cashflow_data[i].get('capitalExpenditure', 0)) if i < len(cashflow_data) else 0
                    rev = income_data[i].get('revenue', 0)
                    if rev > 0:
                        ratios.append(capex / rev)
                
                avg_ratio = sum(ratios) / len(ratios) if ratios else None
            else:
                avg_ratio = ratio_current
            
            return ratio_current, avg_ratio
        except Exception as e:
            print(f"      [Warning] Capex pulse calculation failed: {e}")
            return None, None

    def _check_pricing_power(self, income_data: List[Dict]) -> tuple[Optional[float], Optional[float], Optional[float]]:
        """
        检查定价权 (毛利率稳定性)
        
        V3.7 规则: 毛利率跌幅 < 3%
        
        Returns:
            (current_gm, prev_year_gm, change)
        """
        if not income_data or len(income_data) < 2:
            return None, None, None
        
        try:
            # 当前年度毛利率
            rev_current = income_data[0].get('revenue', 0)
            gp_current = income_data[0].get('grossProfit', 0)
            gm_current = gp_current / rev_current if rev_current > 0 else None
            
            # 去年毛利率
            rev_prev = income_data[1].get('revenue', 0)
            gp_prev = income_data[1].get('grossProfit', 0)
            gm_prev = gp_prev / rev_prev if rev_prev > 0 else None
            
            # 变化
            change = (gm_current - gm_prev) if gm_current and gm_prev else None
            
            return gm_current, gm_prev, change
        except Exception as e:
            print(f"      [Warning] Pricing power check failed: {e}")
            return None, None, None

    def _assess_moat_strength(self, sector: str, industry: str, business_model: BusinessModel) -> tuple[MoatStrength, str]:
        """
        评估护城河强度
        
        V3.7 规则: 在困境期，客户会跑吗？
        - SaaS/医药: 跑不掉 (Switching Cost 高)
        - 手机/服装: 容易跑
        
        Returns:
            (moat_strength, assessment)
        """
        combined = f"{sector} {industry} {business_model.value}".lower()
        
        # 高护城河
        for keyword in self.HIGH_MOAT_KEYWORDS:
            if keyword.lower() in combined:
                return MoatStrength.HIGH, f"High switching cost: {keyword} - customers unlikely to leave during bottleneck"
        
        # 低护城河
        for keyword in self.LOW_MOAT_KEYWORDS:
            if keyword.lower() in combined:
                return MoatStrength.LOW, f"Low switching cost: {keyword} - customers may switch easily"
        
        return MoatStrength.MEDIUM, "Medium switching cost - requires further analysis"

    def identify(self, ticker: str, company_description: str, sector: str = "", industry: str = "") -> IdentifierData:
        """
        V3.7 财务侦探 + 商业模式识别
        
        Args:
            ticker: 股票代码
            company_description: 公司描述
            sector: 行业大类 (来自 Gatekeeper)
            industry: 细分行业 (来自 Gatekeeper)
            
        Returns:
            IdentifierData: 包含商业模式识别和财务侦探结果
        """
        print(f"  [Phase 1] Financial Forensics for {ticker}...")
        
        # ========== 1. 商业模式识别 (LLM) ==========
        print("    - Identifying business model...")
        business_model = self._identify_business_model(ticker, company_description)
        
        # ========== 2. 获取财务数据 ==========
        if not self.fmp:
            print("      [Warning] FMP client not available, skipping financial forensics")
            return IdentifierData(
                business_model=business_model.business_model,
                specific_kpis=business_model.specific_kpis,
                bear_case_hook=business_model.bear_case_hook
            )
        
        print("    - Fetching financial data for forensics...")
        income_annual = self.fmp.get_income_statement(ticker, period='annual', limit=5)
        balance_annual = self.fmp.get_balance_sheet(ticker, period='annual', limit=5)
        cashflow_annual = self.fmp.get_cash_flow_statement(ticker, period='annual', limit=5)
        
        # 初始化 Forensics 数据
        forensics = ForensicsData()
        
        # ========== 3. 库存周转测试 ==========
        print("    - Indicator A: Inventory Turnover Test...")
        inv_current, inv_avg = self._calculate_inventory_turnover(income_annual, balance_annual)
        forensics.inventory_turnover_current = inv_current
        forensics.inventory_turnover_3y_avg = inv_avg
        
        if inv_current is not None and inv_avg is not None:
            change_pct = (inv_current - inv_avg) / inv_avg if inv_avg > 0 else 0
            forensics.inventory_check_passed = change_pct >= self.INVENTORY_TURNOVER_TOLERANCE
            print(f"      Current: {inv_current:.2f} | 3Y Avg: {inv_avg:.2f} | Change: {change_pct:+.1%}")
            print(f"      Result: {'PASS (demand intact)' if forensics.inventory_check_passed else 'FAIL (demand collapse)'}")
        else:
            # 无库存公司 (如软件)，默认通过
            forensics.inventory_check_passed = True
            print("      N/A (inventory-less business model)")
        
        # ========== 4. 资本开支脉冲 ==========
        print("    - Indicator B: Capex Pulse...")
        capex_current, capex_avg = self._calculate_capex_pulse(income_annual, cashflow_annual)
        forensics.capex_revenue_current = capex_current
        forensics.capex_revenue_3y_avg = capex_avg
        
        if capex_current is not None and capex_avg is not None:
            # 正信号: 当前 Capex/Rev > 3Y Avg
            forensics.capex_pulse_positive = capex_current > capex_avg
            print(f"      Current Capex/Rev: {capex_current:.1%} | 3Y Avg: {capex_avg:.1%}")
            print(f"      Result: {'POSITIVE (capacity expansion)' if forensics.capex_pulse_positive else 'NEUTRAL'}")
        else:
            print("      N/A (insufficient data)")
        
        # ========== 5. 定价权测试 ==========
        print("    - Indicator C: Pricing Power Test...")
        gm_current, gm_prev, gm_change = self._check_pricing_power(income_annual)
        forensics.gross_margin_current = gm_current
        forensics.gross_margin_prev_year = gm_prev
        forensics.gross_margin_change = gm_change
        
        if gm_change is not None:
            forensics.pricing_power_intact = gm_change >= -self.GROSS_MARGIN_MAX_DROP
            print(f"      Current GM: {gm_current:.1%} | Prev Year: {gm_prev:.1%} | Change: {gm_change:+.1%}")
            print(f"      Result: {'PASS (pricing power intact)' if forensics.pricing_power_intact else 'FAIL (pricing power lost)'}")
        else:
            forensics.pricing_power_intact = True
            print("      N/A (insufficient data)")
        
        # ========== 6. 护城河锁定 ==========
        print("    - Moat Lock-in Assessment...")
        moat_strength, moat_assessment = self._assess_moat_strength(sector, industry, business_model.business_model)
        forensics.moat_strength = moat_strength
        forensics.moat_assessment = moat_assessment
        print(f"      Moat Strength: {moat_strength.value}")
        print(f"      Assessment: {moat_assessment}")
        
        # ========== 7. 综合判断 ==========
        # V3.7 必须满足: 库存通过 + 定价权通过
        # Capex 脉冲为加分项
        forensics.passed = forensics.inventory_check_passed and forensics.pricing_power_intact
        
        if not forensics.passed:
            reasons = []
            if not forensics.inventory_check_passed:
                reasons.append("Inventory turnover crashed (demand collapse)")
            if not forensics.pricing_power_intact:
                reasons.append("Gross margin declined >3% (pricing power lost)")
            forensics.fail_reason = "; ".join(reasons)
        
        if forensics.passed:
            print(f"    - Financial Forensics PASSED for {ticker}")
        else:
            print(f"    - Financial Forensics FAILED: {forensics.fail_reason}")
        
        return IdentifierData(
            business_model=business_model.business_model,
            specific_kpis=business_model.specific_kpis,
            bear_case_hook=business_model.bear_case_hook,
            forensics=forensics
        )

    def _identify_business_model(self, ticker: str, company_description: str) -> IdentifierData:
        """原有的商业模式识别功能 (LLM)"""
        prompt = f"""
        Analyze the company {ticker} based on this description: {company_description}

        Classify it into one of these business models:
        - SaaS (Subscription, Cloud Software)
        - Consumption (Usage-based, Cloud Infrastructure)
        - Marketplace (Two-sided platform, Gig Economy)
        - Advertising (Ad-driven, Social Media)
        - Hardware (Physical devices)
        - Pharma (Pharmaceutical, Biotech)
        - Semiconductor (Chips, Semiconductor Equipment)
        - Other

        Then, list 3 specific idiosyncratic KPIs (Key Performance Indicators) that are critical for this specific business model.
        Examples:
        - SaaS: NDR (Net Dollar Retention), RPO (Remaining Performance Obligations), ARR
        - Consumption: Net Revenue Retention, Usage Growth
        - Marketplace: GMV, Take Rate
        - Pharma: Pipeline Value, Approval Rate, Patent Cliff
        - Semiconductor: Utilization Rate, ASP Trend, Inventory Days

        Also identify the "Bear Case Hook" - the most likely reason this company would fail or is failing.
        """

        system_prompt = "You are a senior equity research analyst specializing in growth stocks."

        result = self.llm.extract_structured_data(prompt, IdentifierData, system_prompt)

        if not result:
            print(f"      [Warning] LLM failed to identify {ticker}. Using fallback.")
            return IdentifierData(
                business_model=BusinessModel.OTHER,
                specific_kpis=["Revenue Growth"],
                bear_case_hook="Unknown"
            )

        print(f"      Business Model: {result.business_model.value}")
        print(f"      Target KPIs: {result.specific_kpis}")
        print(f"      Bear Case Hook: {result.bear_case_hook}")
        return result

    # ========== Legacy V3.4 Methods (保留兼容性) ==========

    def shadow_audit(self, ticker: str, company_name: str) -> ShadowAuditData:
        """V3.4 影子指标验证 (保留兼容性)"""
        print(f"    - [V3.4] Shadow Audit for {ticker}...")
        
        if not self.search:
            print("      [Warning] SearchClient not available, skipping shadow audit.")
            return ShadowAuditData()
        
        linkedin_result = None
        customer_result = None
        is_fake_tech = False
        has_king_maker = False
        
        # LinkedIn 人才流向审计
        print("      Checking LinkedIn hiring patterns...")
        try:
            linkedin_query = f"{company_name} {ticker} hiring AI machine learning engineers LinkedIn jobs 2024 2025"
            linkedin_results = self.search.search(linkedin_query, max_results=3)
            
            if linkedin_results:
                linkedin_content = "\n".join([r.get('content', '')[:500] for r in linkedin_results])
                
                analysis_prompt = f"""
                Based on these search results about {company_name} ({ticker}) hiring:
                
                {linkedin_content}
                
                Analyze:
                1. Is this company actively hiring for next-gen technology roles (AI/ML, LLM, Cloud, etc.)?
                2. Does the hiring pattern suggest genuine technology investment or just marketing hype?
                
                Conclude with either:
                - "GENUINE_TECH_INVESTMENT" if hiring patterns suggest real R&D
                - "POTENTIAL_FAKE_TECH" if the company claims tech innovation but isn't hiring for it
                - "INCONCLUSIVE" if insufficient data
                """
                
                linkedin_result = self.llm.analyze_text(analysis_prompt, 
                    system_prompt="You are a tech industry analyst specializing in talent acquisition patterns.")
                
                if linkedin_result:
                    is_fake_tech = "POTENTIAL_FAKE_TECH" in linkedin_result.upper()
                    print(f"      LinkedIn Audit: {'⚠️ Potential Fake Tech' if is_fake_tech else '✓ Tech hiring looks genuine'}")
        except Exception as e:
            print(f"      [Warning] LinkedIn audit failed: {e}")
            linkedin_result = f"Error: {e}"
        
        # 客户含金量审计
        print("      Checking customer quality (King Makers)...")
        try:
            customer_query = f"{company_name} {ticker} major customers clients Apple Microsoft Amazon Nvidia Google partnership"
            customer_results = self.search.search(customer_query, max_results=3)
            
            if customer_results:
                customer_content = "\n".join([r.get('content', '')[:500] for r in customer_results])
                
                analysis_prompt = f"""
                Based on these search results about {company_name} ({ticker}) customers:
                
                {customer_content}
                
                Analyze:
                1. Does this company have any "King Maker" customers (Apple, Microsoft, Amazon, Google, Nvidia)?
                2. Are these partnerships significant (revenue contribution, strategic importance)?
                
                Conclude with either:
                - "HAS_KING_MAKERS" if the company has significant partnerships with tech giants
                - "NO_KING_MAKERS" if no evidence of major tech giant customers
                - "INCONCLUSIVE" if insufficient data
                """
                
                customer_result = self.llm.analyze_text(analysis_prompt,
                    system_prompt="You are a B2B sales analyst specializing in enterprise customer relationships.")
                
                if customer_result:
                    has_king_maker = "HAS_KING_MAKERS" in customer_result.upper()
                    print(f"      Customer Audit: {'✓ Has King Maker clients' if has_king_maker else 'No major tech giant clients detected'}")
        except Exception as e:
            print(f"      [Warning] Customer audit failed: {e}")
            customer_result = f"Error: {e}"
        
        return ShadowAuditData(
            linkedin_hiring_audit=linkedin_result,
            customer_quality_audit=customer_result,
            is_fake_tech=is_fake_tech,
            has_king_maker_clients=has_king_maker
        )

    def polygraph(self, ticker: str, income_quarterly: List[Dict], cash_flow_quarterly: List[Dict], 
                  press_releases: List[Dict] = None) -> PolygraphData:
        """V3.4 财务背离测谎仪 (保留兼容性)"""
        print(f"    - [V3.4] Polygraph Analysis for {ticker}...")
        
        cfo_check_passed = True
        sandbagging_detected = False
        details_parts = []
        
        # 现金流背离检测
        print("      Checking Cash Flow Divergence...")
        try:
            if income_quarterly and cash_flow_quarterly and len(income_quarterly) >= 4 and len(cash_flow_quarterly) >= 4:
                ni_q0 = income_quarterly[0].get('netIncome', 0)
                ni_q1 = income_quarterly[1].get('netIncome', 0)
                cfo_q0 = cash_flow_quarterly[0].get('operatingCashFlow', 0)
                cfo_q1 = cash_flow_quarterly[1].get('operatingCashFlow', 0)
                
                ni_change = (ni_q0 - ni_q1) / abs(ni_q1) if ni_q1 != 0 else 0
                cfo_change = (cfo_q0 - cfo_q1) / abs(cfo_q1) if cfo_q1 != 0 else 0
                
                if ni_change > 0.20 and cfo_change < 0.05:
                    cfo_check_passed = False
                    details_parts.append(f"⚠️ CFO Divergence: NI +{ni_change:.1%} but CFO {cfo_change:+.1%}")
                    print(f"      ⚠️ RED FLAG: Net Income grew {ni_change:.1%} but CFO only {cfo_change:+.1%}")
                else:
                    details_parts.append(f"✓ CFO aligned: NI {ni_change:+.1%}, CFO {cfo_change:+.1%}")
                    print("      ✓ Cash Flow aligned with Net Income")
            else:
                details_parts.append("Insufficient data for CFO check")
                print("      [Warning] Insufficient quarterly data for CFO divergence check")
        except Exception as e:
            details_parts.append(f"CFO check error: {e}")
            print(f"      [Warning] CFO divergence check failed: {e}")
        
        return PolygraphData(
            cash_flow_divergence_check=cfo_check_passed,
            sandbagging_detected=sandbagging_detected,
            details=" | ".join(details_parts) if details_parts else None
        )
