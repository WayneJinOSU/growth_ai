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
from tools.search_helpers import SearchHelper
from datetime import datetime
from core.data_models import ShadowAuditData, BusinessModel

class ShadowAudit:
    """
    影子验证器：负责非财务数据的侧面验证
    """

    def __init__(self, search_client=None, fmp_client=None, llm_client=None, deep_client=None):
        from tools.deep_search import DeepSearchClient

        self.search = search_client or SearchClient()
        self.fmp = fmp_client or FMPClient()
        self.llm = llm_client or LLMClient()
        self.deep = deep_client or DeepSearchClient()
        self.sh = SearchHelper(self.search, self.deep)

    def audit(self, ticker: str, company_name: str, business_model: BusinessModel, references: list = None, deep_search: bool = False) -> ShadowAuditData:
        print(f"  [Phase 2] Shadow Audit for {ticker} (V3.5)...")
        
        data = ShadowAuditData()
        if references is None:
            references = []

        # ========== 1. Fake Tech Detection (LinkedIn Audit) ==========
        # 适用于所有声称是 Tech 的公司
        print("    - Checking LinkedIn Hiring (Fake Tech Audit)...")
        # LLM-Enhanced: 如果是真科技公司，应该在招 AI/ML/Engineering 人才
        query_hiring = f"{company_name} {ticker} hiring careers AI engineer machine learning data scientist"
        
        hiring_results = []
        
        # [Deep Search]
        if deep_search:
            print("    [Deep Search] generating matrix for Fake Tech & Hiring...")
            matrix = self.deep.generate_search_matrix(ticker, company_name, 
                "验证假科技(招聘真实性) + 研发团队规模 + 核心技术壁垒")
            deep_res, _ = self.deep.execute_matrix(matrix)
            hiring_results.extend(deep_res)

        if self.search:
            # V3.5 Optimize: More results (8) to capture varied job postings
            reg_res = self.search.search(query_hiring, max_results=8, days=180)
            hiring_results.extend(reg_res)
            
            context = self.sh.collect_refs(hiring_results, references)
            if hiring_results:
                
                # V3.5 LLM Enhancement for Fake Tech
                prompt = f"""
                Current Date: {datetime.now().strftime('%Y-%m-%d')}
                Analyze if {company_name} ({ticker}) is a "Fake Tech" company based on hiring data:
                
                {context}
                
                Task:
                Determine if they are actively hiring for core R&D/Tech roles (AI, ML, Engineering, Data Science) vs just Sales/Marketing.
                
                Reply with ONLY one of:
                - "REAL_TECH" (Found significant engineering/AI hiring)
                - "FAKE_TECH" (Mostly sales/marketing/general hiring, little tech)
                - "INCONCLUSIVE" (Not enough info)
                
                Then add a pipe "|" and a ONE sentence evidence summary. 
                CRITICAL: Mention the timing/recency of these job postings if found (e.g., "posted 2 weeks ago").
                Example: "REAL_TECH|Hiring 3 Machine Learning Engineers and a CTO (posted Jan 2025) [3]."
                Use [ID] citations in evidence summary if possible.
                """
                
                try:
                    llm_result = self.llm.analyze_text(prompt, system_prompt="You are a tech recruiter auditor.").strip()
                    decision_part = llm_result.split('|')[0].strip()
                    evidence_part = llm_result.split('|')[1].strip() if '|' in llm_result else "LLM Analysis"
                    
                    if "REAL_TECH" in decision_part:
                        data.linkedin_hiring_audit = f"Active Tech Hiring Verified: {evidence_part}"
                        print(f"      ✓ Tech Hiring Active ({evidence_part})")
                    elif "FAKE_TECH" in decision_part:
                        data.is_fake_tech = True
                        data.linkedin_hiring_audit = f"WARNING: Potential Fake Tech. {evidence_part}"
                        print(f"      ⚠️ Potential Fake Tech: {evidence_part}")
                    else:
                        data.linkedin_hiring_audit = "Inconclusive hiring data"
                        print("      Inconclusive hiring data")
                        
                except Exception as e:
                    print(f"      [Error] LLM Hiring Audit failed: {e}")
                    # Fallback to keywords
                    tech_keywords = ["engineer", "developer", "data scientist", "machine learning", " ai ", "r&d"]
                    combined = " ".join(r.get('content', '') for r in hiring_results).lower()
                    is_hiring_tech = any(k in combined for k in tech_keywords)
                    if is_hiring_tech:
                        data.linkedin_hiring_audit = "Active Tech Hiring (Keyword Verified)"
                    else:
                        data.is_fake_tech = True
                        data.linkedin_hiring_audit = "No significant tech hiring found (Keyword Check)"
        
        # ========== 2. Path A: King Maker Validation ==========
        # 适用于 B2B, Hardware, SaaS
        if business_model in [BusinessModel.SAAS, BusinessModel.HARDWARE, BusinessModel.CONSUMPTION, BusinessModel.OTHER]:
            print("    - [Path A] Checking for King Makers...")
            query_client = f"{company_name} {ticker} major customers partners Apple Microsoft Nvidia Amazon Google government contract"
            km_results = []

            # [Deep Search]
            if deep_search:
                print("    [Deep Search] generating matrix for King Makers...")
                matrix_km = self.deep.generate_search_matrix(ticker, company_name, 
                    "验证造王者大客户(Apple/Nvidia/Microsoft/Gov) + 供应链关系")
                deep_res_km, _ = self.deep.execute_matrix(matrix_km)
                km_results.extend(deep_res_km)

            if self.search:
                # V3.5 Optimize: Longer horizon (365 days) and more results (8) for strategic partnerships
                reg_res_km = self.search.search(query_client, max_results=8, days=365)
                km_results.extend(reg_res_km)
            
            context = self.sh.collect_refs(km_results, references)
            
            if km_results:
                    # V3.5 LLM-Enhanced King Maker Validation
                    prompt = f"""
                    Current Date: {datetime.now().strftime('%Y-%m-%d')}
                    Identify 'King Maker' clients or partners for {company_name} ({ticker}) based on:
                    
                    {context}
                    
                    King Makers include: Apple, Microsoft, Nvidia, Amazon, Google, Meta, Tesla, or major Government/Defense agencies.
                    
                    Task:
               if self.search:
                # V3.5 Optimize: Longer horizon (365 days) and more results (8) for strategic partnerships
                reg_res_km = self.search.search(query_client, max_results=8, days=365)
                km_results.extend(reg_res_km)
                 - Use [ID] citations for every claim.
                    - If no significant relationships are found, reply exactly with "None".
                    """
                    
                    try:
                        llm_result = self.llm.analyze_text(
                            prompt, 
                            system_prompt="You are a strategic business analyst focusing on corporate supply chains and ecosystems.", 
                            model="google/gemini-2.5-flash"
                        ).strip()
                        
                        if llm_result.lower() != "none" and len(llm_result) > 10:
                            data.has_king_maker_clients = True
                            data.customer_quality_audit = llm_result
                            print("      ✓ King Makers: Detailed audit performed")
                        else:
                            data.customer_quality_audit = "No King Makers detected in public search"
                            print("      No King Makers detected")
                    except Exception as e:
                        print(f"      [Warning] King Maker LLM audit failed: {e}")
                        # Fallback to keyword check
                        king_makers = ["apple", "microsoft", "nvidia", "amazon", "google", "meta", "tesla", "government", "defense"]
                        found_kings = [k for k in king_makers if k in context.lower()]
                        if found_kings:
                            data.has_king_maker_clients = True
                            data.customer_quality_audit = f"King Makers found (Keyword Check): {', '.join(found_kings)}"
                        else:
                            data.customer_quality_audit = "No King Makers detected"

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
                sm_trend = f"S&M moved {sm_ratio_prev:.1%} -> {sm_ratio_curr:.1%}"
                
                if sm_ratio_curr <= (sm_ratio_prev + 0.01) and rev_curr > rev_prev:
                    data.organic_growth_confirmed = True
                    data.marketing_efficiency = f"Efficient (Organic): {sm_trend} with growing revenue"
                    print("      ✓ Organic Growth Confirmed")
                else:
                    data.marketing_efficiency = f"Inefficient (Bought Growth): {sm_trend}"
                    print("      ⚠️ Growth is likely paid (S&M rising faster)")
                    
            # 补充：App Store Rank 检查 (需特定 API，此处用 Search 模拟)
            if self.search:
                query_app = f"{company_name} app store ranking top charts"
                results = self.search.search(query_app, max_results=1)
                self.sh.collect_refs(results, references)
                if results:
                    content = results[0].get('content', '').lower()
                    if "top" in content or "#1" in content or "most downloaded" in content:
                        data.app_store_rank = "High Ranking Detected"
                        print("      ✓ App Store Dominance Detected")

        # ========== 4. Sandbagging Detection (管理层沙袋检测) ==========
        # 适用于所有公司
        print("    - Checking for Sandbagging (Conservative Guidance)...")
        if self.search and self.llm:
            # 使用 get_press_releases 锁定官方源进行沙袋检测 - 增加到 5 条以覆盖更多财报
            results = self.search.get_press_releases(ticker, company_name=company_name, limit=5)
            context = self.sh.collect_refs(results, references)
            
            if results:
                
                # 使用 LLM 分析是否有 Sandbagging 信号
                prompt = f"""
                Current Date: {datetime.now().strftime('%Y-%m-%d')}
                Analyze if {company_name} ({ticker}) management is "sandbagging" (deliberately setting low expectations):
                
                {context}
                
                Signs of sandbagging:
                - Conservative guidance despite strong underlying metrics
                - "Beat and raise" pattern in recent quarters
                - Strong RPO/backlog but cautious revenue outlook
                
                Reply with ONLY one of:
                - "SANDBAGGING_DETECTED" if there's evidence of sandbagging (bullish)
                - "NO_SANDBAGGING" if guidance seems normal
                - "INCONCLUSIVE" if unclear
                
                CRITICAL: If detected, specify the exact quarters or dates where this behavior was observed.
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

shadowAudit = ShadowAudit()