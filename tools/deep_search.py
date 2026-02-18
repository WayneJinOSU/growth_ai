"""
Deep Search Client (深度搜索指挥官) - Search 2.0
=================================================
独立于 SearchClient 的 4 模块智能情报系统。
Phase 专项化版本：由各 Phase 按需调用，提供定制化搜索矩阵。

核心模块:
1. Matrix Generator: Gemini → 针对 Phase 目标生成搜索指令矩阵
2. Execution Module: Tavily → 定点爆破 (Domain-Locked)
3. Echo Loop: Gemini → 差距分析 & 回音循环 (Phase 3 专用)
4. Adversarial Module: Gemini → 自我攻击验证 (Phase 8 专用)

使用方式:
    deep = DeepSearchClient()
    # 1. 生成矩阵
    matrix = deep.generate_search_matrix("INTC", "Intel", "验证假科技和造王者客户")
    # 2. 执行搜索
    results, context = deep.execute_matrix(matrix)
"""

import json
from typing import List, Dict, Optional, Tuple
from datetime import datetime


# ===================== Constants =====================

DOMAIN_GROUPS = {
    "HARD_INTEL": ["sec.gov", "annualreports.com", "investor.*"],
    "SOFT_INTEL": ["reddit.com", "teamblind.com", "glassdoor.com", "trustradius.com"],
    "EXPERT_INTEL": ["stackoverflow.com", "github.com", "ycombinator.com"],
    "SHORT_SELLER": ["muddywatersresearch.com", "citronresearch.com", "seekingalpha.com"],
    "LEGAL": ["sec.gov", "law360.com", "reuters.com", "justice.gov"],
}

# Davis Protocol 必填字段 Checklist (Phase 3 专用)
REQUIRED_CHECKLIST = [
    "Revenue Growth",
    "Net Dollar Retention (NDR)",
    "Customer Acquisition Cost (CAC)",
    "Churn Rate",
    "FCF Margin",
    "Management Changes",
    "Insider Activity",
    "Competitive Position",
]

# Echo Loop 最大循环次数
MAX_ECHO_LOOPS = 3


class DeepSearchClient:
    """
    深度搜索指挥官：4 模块智能情报系统
    """

    def __init__(self, search_client=None, llm_client=None):
        from tools.search import SearchClient
        from tools.llm import LLMClient

        self.search = search_client or SearchClient()
        self.llm = llm_client or LLMClient()

    # =====================================================================
    # Module 1: Matrix Generator (定制化搜索矩阵)
    # =====================================================================

    def generate_search_matrix(self, ticker: str, company_name: str, phase_objective: str) -> List[Dict]:
        """
        根据 Phase 的具体目标，生成 5-8 条针对性搜索指令。
        """
        print(f"\n  🎯 [Deep Search] Matrix Generator: {phase_objective}...")

        search_name = company_name or ticker
        current_date = datetime.now().strftime('%Y-%m-%d')

        prompt = f"""你是一个金融情报指挥官。
当前任务目标: *"{phase_objective}"*
目标公司: {ticker} ({search_name})
当前日期: {current_date}

请生成一个包含 5-8 条 Tavily 搜索指令的矩阵，专门用于完成上述目标。
你需要决定每条指令应该去哪个情报源 (Domain Group) 搜索。

Domain Groups:
- HARD_INTEL: 官方 SEC 文件、年报、投资者关系 (适合查财务、大客户、官方声明)
- SOFT_INTEL: 员工论坛、Glassdoor、Reddit (适合查假科技、裁员、内部吐槽)
- EXPERT_INTEL: 技术论坛、GitHub (适合查技术实力、行业趋势)
- SHORT_SELLER: 做空报告、寻求Alpha (适合查负面、欺诈指控)

**关键规则**：
1. 不要搜索通用信息，只搜能直接验证目标的证据。
2. 尽量使用"假设已发生"的搜索词 (例如查假科技，搜 "fake tech accusation" 而不是 "is it real tech")。
3. 请严格按以下 JSON 格式返回:

[
  {{"query": "搜索关键词 (英文)", "domain_group": "HARD_INTEL"}},
  {{"query": "搜索关键词 (英文)", "domain_group": "SOFT_INTEL"}}
]"""

        try:
            response = self.llm.analyze_text(prompt, system_prompt="只返回 JSON 数组，不要 markdown。")
            json_str = self._clean_json(response)
            matrix = json.loads(json_str)
            print(f"    ✅ Generated {len(matrix)} directives")
            return matrix
        except Exception as e:
            print(f"    ❌ Matrix generation error: {e}")
            return self._fallback_matrix(ticker, search_name, phase_objective)

    def _fallback_matrix(self, ticker: str, company_name: str, objective: str) -> List[Dict]:
        """简单的后备矩阵"""
        print("    ⚠️ Using fallback matrix")
        base = []
        if "财务" in objective or "Financial" in objective:
            base.append({"query": f"{ticker} revenue growth ndr retention", "domain_group": "HARD_INTEL"})
            base.append({"query": f"{ticker} 10-k risk factors", "domain_group": "HARD_INTEL"})
        elif "假科技" in objective or "Fake" in objective:
            base.append({"query": f"{company_name} fake tech fraud", "domain_group": "SOFT_INTEL"})
            base.append({"query": f"{company_name} hiring engineering team", "domain_group": "SOFT_INTEL"})
        elif "行业" in objective or "Wave" in objective:
            base.append({"query": f"{ticker} industry trends market share", "domain_group": "EXPERT_INTEL"})
        else:
            base.append({"query": f"{ticker} analysis report", "domain_group": "HARD_INTEL"})
        return base

    # =====================================================================
    # Module 2: Execution (执行 & 格式化)
    # =====================================================================

    def execute_matrix(self, matrix: List[Dict]) -> Tuple[List[Dict], str]:
        """
        执行搜索矩阵，并返回结果列表和格式化后的上下文。
        
        Returns:
            results: List[Dict] (包含 url, title, content)
            context: str (带 [ID] 的文本，用于 LLM)
        """
        print(f"  💥 [Deep Search] Executing {len(matrix)} queries...")
        all_results = []
        
        for directive in matrix:
            query = directive.get("query")
            group = directive.get("domain_group", "HARD_INTEL")
            
            print(f"    🔍 {group}: {query[:50]}...")
            
            # 使用 Tavily 锁定域名
            domains = DOMAIN_GROUPS.get(group)
            try:
                raw_res = self.search.client.search(
                    query, 
                    search_depth="advanced", 
                    include_domains=domains,
                    max_results=4
                ).get('results', [])
            except:
                # Fallback to general search
                raw_res = self.search.search(query, max_results=4)
                
            for r in raw_res:
                r['source_group'] = group
                r['query'] = query
                # Deduplicate
                if not any(x['url'] == r['url'] for x in all_results):
                    all_results.append(r)

        # Generate Context string with IDs
        context_parts = []
        for idx, r in enumerate(all_results, 1):
            context_parts.append(f"[{idx}] {r.get('title','')} ({r.get('source_group')})\nURL: {r.get('url','')}\n{r.get('content','')[:500]}...")
        
        context = "\n\n".join(context_parts)
        print(f"    📊 Retrieved {len(all_results)} unique results")
        
        return all_results, context

    # =====================================================================
    # Module 3: Echo Loop (Phase 3 专用 - 补漏)
    # =====================================================================

    def run_echo_loop(self, ticker: str, initial_results: List[Dict]) -> Dict:
        """
        针对 Phase 3 的回音循环：检查财务数据缺口并补搜。
        """
        print(f"\n  🔄 [Deep Search] Echo Loop (Financial Gaps)...")
        
        # Initial Context
        context_parts = [f"[{i+1}] {r.get('content','')}" for i, r in enumerate(initial_results)]
        full_context = "\n".join(context_parts)
        
        extracted_data = {}
        
        # 只做 1-2 轮循环即可，避免过慢
        for loop in range(2):
            # 1. Check gaps
            gaps = self._identify_gaps(ticker, extracted_data, full_context)
            if not gaps:
                break
                
            print(f"    ⚠️ Loop {loop+1}: Found {len(gaps)} gaps: {[g['field'] for g in gaps]}")
            
            # 2. Search for gaps
            new_results = []
            for gap in gaps:
                q = gap['query']
                print(f"      🔍 Retry: {q[:40]}...")
                res = self.search.search(q, max_results=2)
                new_results.extend(res)
            
            if not new_results:
                break
                
            # 3. Update context
            for r in new_results:
                full_context += f"\n[RETRY] {r.get('content','')}"
                
            # 4. Extract again (simplified for now, real extraction happens in Phase 3 logic)
            # Here we just want to fill the context for Phase 3 to use.
            # But to make the loop work, we need to know if we found it.
            # For simplicity, we assume if we searched, we 'tried'.
            for gap in gaps:
                extracted_data[gap['field']] = "Searched" 

        return extracted_data, full_context

    def _identify_gaps(self, ticker: str, current_data: Dict, context: str) -> List[Dict]:
        """简单判断哪些字段没在 context 里出现"""
        # 使用 LLM 判断 context 是否包含 REQUIRED_CHECKLIST 的内容
        # 这里为了省 token，用简单关键词匹配主要财务指标
        # 实际生产建议用 LLM，这里演示用 LLM
        prompt = f"""
        Context: {context[:5000]}
        
        Checklist: {json.dumps(REQUIRED_CHECKLIST)}
        
        Which items from Checklist are MISSING in Context?
        Return JSON list of objects: {{"field": "...", "query": "search query..."}}
        """
        try:
            res = self.llm.analyze_text(prompt, system_prompt="JSON list only.")
            return json.loads(self._clean_json(res))
        except:
            return []

    # =====================================================================
    # Module 4: Adversarial (Phase 8 专用 - 红蓝对抗)
    # =====================================================================

    def adversarial_review(self, ticker: str, bullish_thesis: str) -> Dict:
        """
        针对看多逻辑进行红蓝对抗。
        """
        print(f"\n  🛡️ [Deep Search] Adversarial Review...")
        
        # 1. Generate Attack Queries
        prompt = f"""Target: {ticker}. Bullish Thesis: {bullish_thesis[:500]}.
        Generate 3 search queries to find FRAUD, ACCOUNTING IRREGULARITIES, or LEGAL TROUBLE.
        JSON list of strings."""
        
        try:
            queries = json.loads(self._clean_json(self.llm.analyze_text(prompt)))
        except:
            queries = [f"{ticker} fraud investigation", f"{ticker} accounting scandal", f"{ticker} short seller report"]
            
        # 2. Execute
        red_flags = []
        for q in queries:
            print(f"    🔴 Attack: {q}")
            res = self.search.client.search(q, include_domains=DOMAIN_GROUPS["LEGAL"], max_results=3).get('results', [])
            for r in res:
                if any(x in r.get('content','').lower() for x in ['fraud', 'investigation', 'lawsuit']):
                    red_flags.append(f"[{r.get('title')}] {r.get('content')[:100]}")
                    
        return {"passed": len(red_flags) == 0, "red_flags": red_flags}

    def _clean_json(self, text: str) -> str:
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"): text = text[4:]
        return text.strip()

# Singleton
deepSearchClient = DeepSearchClient()
