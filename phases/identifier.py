"""
Phase 2: The Identifier (DNA 识别) + V3.4 Shadow Audit & Polygraph
===================================================================
识别商业模式、锁定特异性 KPI，并执行 V3.4 的影子审计与测谎检测。

核心功能:
1. 商业模式分类 (SaaS, Consumption, Marketplace, etc.)
2. KPI 锁定 (NDR, GMV, RPO 等)
3. [V3.4] 影子审计 - LinkedIn 招聘验证、客户质量审计
4. [V3.4] 测谎仪 - 现金流背离检测、沙袋指数检测
"""

from typing import List, Optional, Dict
from tools.llm import LLMClient
from tools.fmp import FMPClient
from tools.search import SearchClient
from core.data_models import IdentifierData, BusinessModel, ShadowAuditData, PolygraphData


class Identifier:
    """
    DNA 识别器：MGP 策略的第二道关卡
    
    V3.4 扩展职责：
    - 识别商业模式和特异性 KPI
    - 影子审计：验证技术实力和客户质量
    - 测谎仪：检测财务造假和沙袋行为
    """

    def __init__(self, llm_client: LLMClient, fmp_client: FMPClient = None, search_client: SearchClient = None):
        self.llm = llm_client
        self.fmp = fmp_client
        self.search = search_client

    def identify(self, ticker: str, company_description: str) -> IdentifierData:
        """原有的商业模式识别功能"""
        prompt = f"""
        Analyze the company {ticker} based on this description: {company_description}

        Classify it into one of these business models:
        - SaaS (Subscription, Cloud Software)
        - Consumption (Usage-based, Cloud Infrastructure)
        - Marketplace (Two-sided platform, Gig Economy)
        - Advertising (Ad-driven, Social Media)
        - Hardware (Physical devices)
        - Other

        Then, list 3 specific idiosyncratic KPIs (Key Performance Indicators) that are critical for this specific business model.
        Examples:
        - SaaS: NDR (Net Dollar Retention), RPO (Remaining Performance Obligations), ARR
        - Consumption: Net Revenue Retention, Usage Growth
        - Marketplace: GMV, Take Rate
        - Advertising: DAU/MAU, ARPPU, CPM/CPC

        Also identify the "Bear Case Hook" - the most likely reason this company would fail or is failing.
        """

        system_prompt = "You are a senior equity research analyst specializing in growth stocks."

        result = self.llm.extract_structured_data(prompt, IdentifierData, system_prompt)

        if not result:
            # Fallback
            print(f"      [Warning] LLM failed to identify {ticker}. Using fallback.")
            return IdentifierData(business_model=BusinessModel.OTHER, specific_kpis=["Revenue Growth"],
                                  bear_case_hook="Unknown")

        print(f"      Business Model: {result.business_model.value}")
        print(f"      Target KPIs: {result.specific_kpis}")
        print(f"      Bear Case Hook: {result.bear_case_hook}")
        return result

    # ========== V3.4 Shadow Audit (影子审计) ==========

    def shadow_audit(self, ticker: str, company_name: str) -> ShadowAuditData:
        """
        V3.4 影子指标验证
        
        1. LinkedIn 人才流向审计 - 检查是否在招聘下一代技术人才
        2. 客户含金量审计 - 检查是否有 King Maker 级别客户
        
        Args:
            ticker: 股票代码
            company_name: 公司名称
            
        Returns:
            ShadowAuditData: 影子审计结果
        """
        print(f"    - [V3.4] Shadow Audit for {ticker}...")
        
        if not self.search:
            print("      [Warning] SearchClient not available, skipping shadow audit.")
            return ShadowAuditData()
        
        linkedin_result = None
        customer_result = None
        is_fake_tech = False
        has_king_maker = False
        
        # ========== 1. LinkedIn 人才流向审计 ==========
        print("      Checking LinkedIn hiring patterns...")
        try:
            # 搜索公司招聘信息
            linkedin_query = f"{company_name} {ticker} hiring AI machine learning engineers LinkedIn jobs 2024 2025"
            linkedin_results = self.search.search(linkedin_query, max_results=3)
            
            if linkedin_results:
                # 使用 LLM 分析招聘信息
                linkedin_content = "\n".join([r.get('content', '')[:500] for r in linkedin_results])
                
                analysis_prompt = f"""
                Based on these search results about {company_name} ({ticker}) hiring:
                
                {linkedin_content}
                
                Analyze:
                1. Is this company actively hiring for next-gen technology roles (AI/ML, LLM, Cloud, etc.)?
                2. Does the hiring pattern suggest genuine technology investment or just marketing hype?
                
                Provide a brief assessment (2-3 sentences) and conclude with either:
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
        
        # ========== 2. 客户含金量审计 ==========
        print("      Checking customer quality (King Makers)...")
        try:
            # 搜索公司主要客户
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
                
                Provide a brief assessment (2-3 sentences) and conclude with either:
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

    # ========== V3.4 Polygraph (测谎仪) ==========

    def polygraph(self, ticker: str, income_quarterly: List[Dict], cash_flow_quarterly: List[Dict], 
                  press_releases: List[Dict] = None) -> PolygraphData:
        """
        V3.4 财务背离测谎仪
        
        1. 现金流背离检测 - Net Income vs Operating Cash Flow
        2. 沙袋指数检测 - 管理层指引 vs 实际表现
        
        Args:
            ticker: 股票代码
            income_quarterly: 季度利润表数据
            cash_flow_quarterly: 季度现金流量表数据
            press_releases: 新闻稿数据 (用于沙袋检测)
            
        Returns:
            PolygraphData: 测谎结果
        """
        print(f"    - [V3.4] Polygraph Analysis for {ticker}...")
        
        cfo_check_passed = True
        sandbagging_detected = False
        details_parts = []
        
        # ========== 1. 现金流背离检测 (CFO Red Flag) ==========
        print("      Checking Cash Flow Divergence...")
        try:
            if income_quarterly and cash_flow_quarterly and len(income_quarterly) >= 4 and len(cash_flow_quarterly) >= 4:
                # 比较最近 2 个季度的 Net Income 和 Operating Cash Flow 趋势
                # 规则: 如果 Net Income 大增但 CFO 持平或下降 -> 红旗
                
                # 最近两个季度
                ni_q0 = income_quarterly[0].get('netIncome', 0)
                ni_q1 = income_quarterly[1].get('netIncome', 0)
                cfo_q0 = cash_flow_quarterly[0].get('operatingCashFlow', 0)
                cfo_q1 = cash_flow_quarterly[1].get('operatingCashFlow', 0)
                
                # 计算变化率
                ni_change = (ni_q0 - ni_q1) / abs(ni_q1) if ni_q1 != 0 else 0
                cfo_change = (cfo_q0 - cfo_q1) / abs(cfo_q1) if cfo_q1 != 0 else 0
                
                # 红旗条件: Net Income 增长 > 20% 但 CFO 下降或持平 (< 5%)
                if ni_change > 0.20 and cfo_change < 0.05:
                    cfo_check_passed = False
                    details_parts.append(f"⚠️ CFO Divergence: NI +{ni_change:.1%} but CFO {cfo_change:+.1%}")
                    print(f"      ⚠️ RED FLAG: Net Income grew {ni_change:.1%} but CFO only {cfo_change:+.1%}")
                else:
                    details_parts.append(f"✓ CFO aligned: NI {ni_change:+.1%}, CFO {cfo_change:+.1%}")
                    print(f"      ✓ Cash Flow aligned with Net Income")
            else:
                details_parts.append("Insufficient data for CFO check")
                print("      [Warning] Insufficient quarterly data for CFO divergence check")
        except Exception as e:
            details_parts.append(f"CFO check error: {e}")
            print(f"      [Warning] CFO divergence check failed: {e}")
        
        # ========== 2. 沙袋指数检测 (Sandbagging Detection) ==========
        print("      Checking for Sandbagging patterns...")
        try:
            if press_releases and len(press_releases) > 0 and self.llm:
                # 分析新闻稿中的管理层指引
                press_content = "\n---\n".join([
                    f"Date: {pr.get('publishedDate', 'N/A')}\nTitle: {pr.get('title', '')}\n{pr.get('text', '')[:300]}"
                    for pr in press_releases[:5]
                ])
                
                sandbagging_prompt = f"""
                Analyze these recent press releases from {ticker}:
                
                {press_content}
                
                Look for signs of "Sandbagging" - when management deliberately sets low expectations:
                1. Did management recently lower guidance or provide conservative outlook?
                2. Are there signs of "beat and raise" patterns in recent quarters?
                3. Is there evidence of strong underlying metrics (RPO, bookings, backlog) despite cautious guidance?
                
                Conclude with:
                - "SANDBAGGING_DETECTED" if management appears to be setting low expectations (bullish signal for investors)
                - "NO_SANDBAGGING" if guidance appears straightforward
                - "INCONCLUSIVE" if insufficient data
                """
                
                sandbagging_result = self.llm.analyze_text(sandbagging_prompt,
                    system_prompt="You are a Wall Street analyst specializing in management communication patterns.")
                
                if sandbagging_result:
                    sandbagging_detected = "SANDBAGGING_DETECTED" in sandbagging_result.upper()
                    if sandbagging_detected:
                        details_parts.append("✓ Sandbagging detected - potential buy opportunity")
                        print("      ✓ Sandbagging detected - management setting low bar (bullish)")
                    else:
                        details_parts.append("No sandbagging pattern detected")
                        print("      No sandbagging pattern detected")
            else:
                details_parts.append("No press releases available for sandbagging analysis")
                print("      [Info] No press releases available for sandbagging analysis")
        except Exception as e:
            details_parts.append(f"Sandbagging check error: {e}")
            print(f"      [Warning] Sandbagging detection failed: {e}")
        
        return PolygraphData(
            cash_flow_divergence_check=cfo_check_passed,
            sandbagging_detected=sandbagging_detected,
            details=" | ".join(details_parts) if details_parts else None
        )