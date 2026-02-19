"""
Phase 3: Intelligence (情报收集)
================================
收集软实力指标：KPI 验证、管理层诚信、护城河、内部人交易、错杀分析。
蓝天展望 & 估值已移至 phases/blue_sky.py (Phase 4)。
催化剂分析已移至 phases/catalysts.py (Phase 5)。
"""

from tools.llm import LLMClient
from tools.search import SearchClient
from tools.search_helpers import SearchHelper
from datetime import datetime
from core.data_models import IntelligenceData, IdentifierData, SearchReference


class Intelligence:
    """
    Phase 3 情报收集器：软实力分析

    职责:
    - 特异性 KPI 验证
    - 管理层诚信评估
    - 护城河动态分析
    - 内部人交易信号
    - 价格错杀判别
    """

    def __init__(self, llm_client=None, search_client=None, deep_client=None):
        from tools.deep_search import DeepSearchClient
        self.llm = llm_client or LLMClient()
        self.search = search_client or SearchClient()
        self.deep = deep_client or DeepSearchClient()
        self.sh = SearchHelper(self.search, self.deep)

    def gather(self, ticker: str, identifier_data: IdentifierData,
               references: list = None, deep_search: bool = False,
               business_model: str = None) -> IntelligenceData:
        """收集 Phase 3 数据"""
        data = IntelligenceData()
        if references is None:
            references = []

        deep_context = self._deep_enrich(ticker, references, business_model=business_model) if deep_search else ""

        print(f"  [Phase 3] Gathering Intelligence for {ticker}...")
        data.kpi_values = self._verify_kpis(ticker, identifier_data.specific_kpis,
                                             references, deep_context, deep_search)
        data.management_integrity = self._analyze_management(ticker, references)
        data.product_moat = self._analyze_moat(ticker, references, deep_search)
        data.insider_activity = self._analyze_insider(ticker, references, deep_search)
        data.dislocation_context = self._analyze_dislocation(ticker, references, deep_search)
        return data

    # ------------------------------------------------------------------
    # Sub-analyses
    # ------------------------------------------------------------------

    def _deep_enrich(self, ticker: str, references: list, business_model: str = None) -> str:
        """Deep Search pre-enrichment: matrix + echo loop."""
        print("  [Deep Search] Generating Financial Matrix & Echo Loop...")
        matrix = self.deep.generate_search_matrix(ticker, "",
            "查找关键财务指标: Revenue Growth, Net Dollar Retention, CAC, Churn, FCF Margin, 管理层变动")
        deep_res, deep_ctx = self.deep.execute_matrix(matrix, business_model=business_model)
        _, deep_ctx_enriched = self.deep.run_echo_loop(ticker, deep_res)

        print(f"  [Deep Search] Enriched Financial Context: {len(deep_ctx_enriched)} chars")

        for r in deep_res:
            if not any(ref.url == r.get('url') for ref in references):
                references.append(SearchReference(
                    id=len(references) + 1,
                    title=r.get('title', ''),
                    url=r.get('url', ''),
                    snippet=f"[Deep Search] {r.get('content', '')[:100]}..."
                ))
        return deep_ctx_enriched

    def _verify_kpis(self, ticker: str, kpis: list, references: list,
                     deep_context: str, deep_search: bool) -> dict:
        """1. Verify Specific KPIs"""
        kpi_values = {}
        print(f"    - Verifying {len(kpis)} KPIs...")

        for kpi in kpis:
            query = f"{ticker} {kpi} latest quarter financial results"
            print(f"      Searching for {kpi}: {query}")
            search_results = self.sh.unified_search(query, max_results=3, days=180, deep_search=deep_search)
            context = self.sh.collect_refs(search_results, references)

            if search_results:
                print(f"      [Search] Found {len(search_results)} results. Snippet: {search_results[0]['content'][:100]}...")
            else:
                print(f"      [Search] No results found for {kpi}")

            if deep_context:
                full_context = f"--- DEEP SEARCH CONTEXT ---\n{deep_context}\n\n--- STANDARD SEARCH RESULTS ---\n{context}"
            else:
                full_context = context

            if len(full_context.strip()) < 50:
                print(f"      [Skip] Insufficient data for {kpi}")
                kpi_values[kpi] = "Not Found"
                continue

            prompt = f"""
            Current Date: {datetime.now().strftime('%Y-%m-%d')}
            Based on the search results below, extract the latest value for the KPI: {kpi} for {ticker}.
            If found, provide ONLY the value and a very brief context. It is CRITICAL to include the exact period/timestamp (e.g., "120% (Q3 2024)" or "Value: 10M as of Dec 2024").
            Do NOT include any introductory text or explanations.
            Use [ID] citations if applicable.
            If the context lacks specific data for this KPI, return ONLY "Not Found". Do not explain why.

            Search Results:
            {full_context}
            """
            val = self.llm.analyze_text(prompt, system_prompt="Extract financial data precisely. Direct output only.")
            kpi_values[kpi] = val.strip()
            print(f"      Result for {kpi}: {kpi_values[kpi]}")

        return kpi_values

    def _analyze_management(self, ticker: str, references: list) -> str:
        """2. Management Integrity"""
        print("    - Analyzing Management Integrity...")
        res = self.search.get_press_releases(ticker, limit=5)
        context = self.sh.collect_refs(res, references)

        if not context or len(context.strip()) < 50:
            print("      [Skip] Insufficient data for management analysis")
            return "N/A"

        prompt = f"""
        Current Date: {datetime.now().strftime('%Y-%m-%d')}
        Analyze the management integrity of {ticker} based on:
        {context}

        Do they have a history of over-promising and under-delivering? Or are they conservative ("sandbaggers")?
        
        Output Requirements:
        - Provide a detailed assessment citing specific guidance vs. actual performance examples.
        - IMPORTANT: Include specific dates or quarters for every example mentioned (e.g., "In Q2 2024, they promised... but by Nov 2024...").
        - Direct answer only. No "Based on..." or "The search results indicate...".
        - Do not limit length; be thorough.
        - Cite sources using [ID] format (e.g. "CEO stated growth is slowing [1]").
        - CRITICAL: If the context lacks specific guidance or earnings data, output ONLY "N/A". Do not speculate.
        """
        result = self.llm.analyze_text(prompt).strip()
        print(f"      Result: {result[:100]}...")
        return result

    def _analyze_moat(self, ticker: str, references: list, deep_search: bool) -> str:
        """3. Competitive Moat"""
        print("    - Analyzing Competitive Moat...")
        query = f"{ticker} competitive advantage moat analysis new products"
        res = self.sh.unified_search(query, max_results=10, days=365, deep_search=deep_search)
        context = self.sh.collect_refs(res, references)

        if not context or len(context.strip()) < 50:
            print("      [Skip] Insufficient data for moat analysis")
            return "N/A"

        prompt = f"""
        Current Date: {datetime.now().strftime('%Y-%m-%d')}
        Analyze the competitive moat of {ticker} based on:
        {context}

        Is their moat widening or narrowing? Any new products driving growth?
        
        Output Requirements:
        - Detail specific competitive advantages, new product traction, and competitive threats.
        - Use data where possible.
        - Direct answer only. No "Based on..." or intro text.
        - IMPORTANT: Cite sources using [ID] format at the end of claims.
        - CRITICAL: If the context lacks specific relevant information, output ONLY "N/A". Do not speculate.
        """
        result = self.llm.analyze_text(prompt).strip()
        print(f"      Result: {result[:100]}...")
        return result

    def _analyze_insider(self, ticker: str, references: list, deep_search: bool) -> str:
        """4. Insider Activity"""
        print("    - Analyzing Insider Activity...")
        query = f"{ticker} insider trading recent selling buying"
        res = self.sh.unified_search(query, max_results=5, days=90, deep_search=deep_search)
        context = self.sh.collect_refs(res, references)

        if not context or len(context.strip()) < 50:
            print("      [Skip] Insufficient data for insider analysis")
            return "N/A"

        prompt = f"""
        Current Date: {datetime.now().strftime('%Y-%m-%d')}
        Analyze insider activity for {ticker} based on:
        {context}

        Are insiders buying or selling significantly? Is it routine selling or alarming?
        
        Output Requirements:
        - Distinguish between routine options exercise and opportunistic selling/buying.
        - IMPORTANT: Specify the exact dates or months of the recent transactions.
        - Provide context on volume if available.
        - Direct answer only. No "Based on..." or intro text.
        - Cite sources using [ID] format.
        - CRITICAL: If the context lacks specific insider transaction data, output ONLY "N/A". Do not speculate.
        """
        result = self.llm.analyze_text(prompt).strip()
        print(f"      Result: {result[:100]}...")
        return result

    def _analyze_dislocation(self, ticker: str, references: list, deep_search: bool) -> str:
        """5. Dislocation / Price Action Context"""
        print("    - Analyzing Price Action Context...")
        query = f"{ticker} stock price drop reason recent news"
        res = self.sh.unified_search(query, max_results=5, days=30, deep_search=deep_search)
        context = self.sh.collect_refs(res, references)

        if not context or len(context.strip()) < 50:
            print("      [Skip] Insufficient data for dislocation analysis")
            return "N/A"

        prompt = f"""
        Current Date: {datetime.now().strftime('%Y-%m-%d')}
        Analyze the recent price action of {ticker} based on:
        {context}

        If the stock is down, is it due to macro factors/sector rotation (True Discount) or broken fundamentals/competitor threat (Fake Discount)?
        
        Output Requirements:
        - Analyze the drivers of price action.
        - IMPORTANT: Provide a timeline of the price action and key events (e.g., "Dropped 15% on Jan 12th following...").
        - Distinguish macro vs. company-specific issues.
        - Direct answer only. No "Based on..." or intro text.
        - Cite sources using [ID] format.
        - CRITICAL: If the context lacks specific price action data, output ONLY "N/A". Do not speculate.
        """
        result = self.llm.analyze_text(prompt).strip()
        print(f"      Result: {result[:100]}...")
        return result
