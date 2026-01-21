"""
Phase 2: The Shadow Audit (影子验证) - V3.5 Singularity
=======================================================
独立模块。在财务数据之外，通过"影子指标"验证生意的真实地位。

核心功能:
1. Path A (B2B/Hard Tech): King Makers 验证 (巨头客户背书)
2. Path B (B2C/Platform): Organic Growth 验证 (S&M% 效率分析)
3. Fake Tech Audit: LinkedIn 招聘验证 (Tavily Search)
"""

from tools.search import SearchClient
from tools.fmp import FMPClient
from tools.llm import LLMClient
from core.data_models import ShadowAuditData, BusinessModel

class ShadowAudit:
    """
    影子验证器：负责非财务数据的侧面验证
    """

    def __init__(self, search_client: SearchClient, fmp_client: FMPClient, llm_client: LLMClient):
        self.search = search_client
        self.fmp = fmp_client
        self.llm = llm_client

    def audit(self, ticker: str, company_name: str, business_model: BusinessModel) -> ShadowAuditData:
        print(f"  [Phase 2] Shadow Audit for {ticker} (V3.5)...")
        
        data = ShadowAuditData()
        
        # ========== 1. Fake Tech Detection (LinkedIn Audit) ==========
        # 适用于所有声称是 Tech 的公司
        print("    - Checking LinkedIn Hiring (Fake Tech Audit)...")
        # 逻辑：如果是真科技公司，应该在招 AI/ML/Engineering 人才，而不是只招 Sales/Marketing
        query_hiring = f"{company_name} {ticker} hiring careers AI engineer machine learning data scientist"
        if self.search:
            results = self.search.search(query_hiring, max_results=3)
            if results:
                content = "\n".join([r.get('content', '')[:300] for r in results])
                
                # 简单规则：如果有 AI/ML/Engineer 关键词 -> Pass
                # 这里可以用 LLM 增强，为节省成本先用关键词
                tech_keywords = ["engineer", "developer", "data scientist", "machine learning", " ai ", "r&d"]
                is_hiring_tech = any(k in content.lower() for k in tech_keywords)
                
                if is_hiring_tech:
                    data.linkedin_hiring_audit = "Active Tech Hiring Detected"
                    print("      ✓ Tech Hiring Active")
                else:
                    # 如果找不到，可能是 False Positive，也可能是真 Fake Tech
                    # 标记为 Warning
                    data.is_fake_tech = True 
                    data.linkedin_hiring_audit = "No significant tech hiring found (Warning)"
                    print("      ⚠️ Potential Fake Tech: No visible tech hiring")
        
        # ========== 2. Path A: King Maker Validation ==========
        # 适用于 B2B, Hardware, SaaS
        if business_model in [BusinessModel.SAAS, BusinessModel.HARDWARE, BusinessModel.CONSUMPTION, BusinessModel.OTHER]:
            print("    - [Path A] Checking for King Makers...")
            if self.search:
                query_client = f"{company_name} {ticker} major customers partners Apple Microsoft Nvidia Amazon Google government contract"
                results = self.search.search(query_client, max_results=3)
                
                if results:
                    content = "\n".join([r.get('content', '') for r in results])
                    king_makers = ["apple", "microsoft", "nvidia", "amazon", "google", "meta", "tesla", "government", "defense"]
                    
                    found_kings = [k for k in king_makers if k in content.lower()]
                    
                    if found_kings:
                        data.has_king_maker_clients = True
                        data.customer_quality_audit = f"King Makers found: {', '.join(found_kings)}"
                        print(f"      ✓ King Makers: {', '.join(found_kings)}")
                    else:
                        data.customer_quality_audit = "No King Makers detected in public search"
                        print("      No King Makers detected")

        # ========== 3. Path B: Organic Growth Validation ==========
        # 适用于 B2C, Marketplace, App
        if business_model in [BusinessModel.MARKETPLACE, BusinessModel.ADVERTISING, BusinessModel.OTHER]:
            print("    - [Path B] Checking for Organic Growth (S&M Efficiency)...")
            income = self.fmp.get_income_statement(ticker, period='annual', limit=3)
            
            if income and len(income) >= 2:
                sm_curr = income[0].get('sellingAndMarketingExpenses', 0)
                rev_curr = income[0].get('revenue', 1)
                sm_ratio_curr = sm_curr / rev_curr
                
                sm_prev = income[1].get('sellingAndMarketingExpenses', 0)
                rev_prev = income[1].get('revenue', 1)
                sm_ratio_prev = sm_prev / rev_prev
                
                print(f"      S&M % Rev: {sm_ratio_prev:.1%} -> {sm_ratio_curr:.1%}")
                
                # 判定：S&M% 下降或持平 (+1%容忍)，且营收增长 -> 自然增长
                # 如果 S&M% 暴涨，说明增长是买来的
                if sm_ratio_curr <= (sm_ratio_prev + 0.01) and rev_curr > rev_prev:
                    data.organic_growth_confirmed = True
                    data.marketing_efficiency = "Efficient (Organic)"
                    print("      ✓ Organic Growth Confirmed")
                else:
                    data.marketing_efficiency = "Inefficient (Bought Growth)"
                    print("      ⚠️ Growth is likely paid (S&M rising faster)")
                    
            # 补充：App Store Rank 检查 (需特定 API，此处用 Search 模拟)
            if self.search:
                query_app = f"{company_name} app store ranking top charts"
                results = self.search.search(query_app, max_results=1)
                if results:
                    content = results[0].get('content', '').lower()
                    if "top" in content or "#1" in content or "most downloaded" in content:
                        data.app_store_rank = "High Ranking Detected"
                        print("      ✓ App Store Dominance Detected")

        # ========== 4. Sandbagging Detection (管理层沙袋检测) ==========
        # 适用于所有公司
        print("    - Checking for Sandbagging (Conservative Guidance)...")
        if self.search and self.llm:
            # 搜索最近的 Earnings Guidance / Press Releases
            query_guidance = f"{company_name} {ticker} earnings guidance outlook conservative beat raise 2024 2025"
            results = self.search.search(query_guidance, max_results=3)
            
            if results:
                content = "\n".join([r.get('content', '')[:400] for r in results])
                
                # 使用 LLM 分析是否有 Sandbagging 信号
                prompt = f"""
                Analyze if {company_name} ({ticker}) management is "sandbagging" (deliberately setting low expectations):
                
                {content}
                
                Signs of sandbagging:
                - Conservative guidance despite strong underlying metrics
                - "Beat and raise" pattern in recent quarters
                - Strong RPO/backlog but cautious revenue outlook
                
                Reply with ONLY one of:
                - "SANDBAGGING_DETECTED" if there's evidence of sandbagging (bullish)
                - "NO_SANDBAGGING" if guidance seems normal
                - "INCONCLUSIVE" if unclear
                """
                
                try:
                    result = self.llm.analyze_text(prompt, system_prompt="You are a Wall Street analyst.")
                    
                    if "SANDBAGGING_DETECTED" in result.upper():
                        data.sandbagging_detected = True
                        data.sandbagging_details = "Management setting low bar (bullish signal)"
                        print("      ✓ Sandbagging Detected (Bullish - SNIPER Opportunity)")
                    else:
                        data.sandbagging_details = "No sandbagging pattern"
                        print("      No sandbagging detected")
                except Exception as e:
                    print(f"      [Warning] Sandbagging check failed: {e}")

        return data
