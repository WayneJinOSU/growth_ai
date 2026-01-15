from tools.llm import LLMClient
from tools.search import SearchClient
from core.data_models import IntelligenceData, IdentifierData, BlueSkyData, CatalystData


class Intelligence:
    def __init__(self, llm_client: LLMClient, search_client: SearchClient):
        self.llm = llm_client
        self.search = search_client

    def gather(self, ticker: str, identifier_data: IdentifierData) -> IntelligenceData:
        data = IntelligenceData()

        # 1. Verify Specific KPIs
        kpi_values = {}
        print(f"    - Verifying {len(identifier_data.specific_kpis)} KPIs...")
        for kpi in identifier_data.specific_kpis:
            query = f"{ticker} {kpi} latest quarter 2024 2025 financial results"
            print(f"      Searching for {kpi}: {query}")
            search_results = self.search.search(query, max_results=3)
            context = "\n".join([r['content'] for r in search_results if r and 'content' in r])
            
            if search_results:
                print(f"      [Search] Found {len(search_results)} results. Snippet: {search_results[0]['content'][:100]}...")
            else:
                print(f"      [Search] No results found for {kpi}")

            prompt = f"""
            Based on the search results below, extract the latest value for the KPI: {kpi} for {ticker}.
            If found, provide ONLY the value and a very brief context (e.g., "120% (Q3 2024)").
            Do NOT include any introductory text or explanations.
            If not found, return "Not Found".

            Search Results:
            {context}
            """
            val = self.llm.analyze_text(prompt, system_prompt="Extract financial data precisely. Direct output only.")
            kpi_values[kpi] = val.strip()
            print(f"      Result for {kpi}: {kpi_values[kpi]}")

        data.kpi_values = kpi_values

        # 2. Soft Factors - Management Integrity
        print("    - Analyzing Management Integrity...")
        query_mgmt = f"{ticker} management guidance track record beat miss history"
        res_mgmt = self.search.search(query_mgmt, max_results=3)
        context_mgmt = "\n".join([r['content'] for r in res_mgmt])

        prompt_mgmt = f"""
        Analyze the management integrity of {ticker} based on:
        {context_mgmt}

        Do they have a history of over-promising and under-delivering? Or are they conservative ("sandbaggers")?
        
        Output Requirements:
        - Provide a detailed assessment citing specific guidance vs. actual performance examples.
        - Direct answer only. No "Based on..." or "The search results indicate...".
        - Do not limit length; be thorough.
        """
        data.management_integrity = self.llm.analyze_text(prompt_mgmt).strip()
        print(f"      Result: {data.management_integrity[:100]}...")

        # 3. Soft Factors - Moat/Competition
        print("    - Analyzing Competitive Moat...")
        query_moat = f"{ticker} competitive advantage moat analysis new products"
        res_moat = self.search.search(query_moat, max_results=3)
        context_moat = "\n".join([r['content'] for r in res_moat])

        prompt_moat = f"""
        Analyze the competitive moat of {ticker} based on:
        {context_moat}

        Is their moat widening or narrowing? Any new products driving growth?
        
        Output Requirements:
        - Detail specific competitive advantages, new product traction, and competitive threats.
        - Use data where possible.
        - Direct answer only. No "Based on..." or intro text.
        """
        data.product_moat = self.llm.analyze_text(prompt_moat).strip()
        print(f"      Result: {data.product_moat[:100]}...")

        # 4. Insider Activity
        print("    - Analyzing Insider Activity...")
        query_insider = f"{ticker} insider trading recent selling buying"
        res_insider = self.search.search(query_insider, max_results=3)
        context_insider = "\n".join([r['content'] for r in res_insider])

        prompt_insider = f"""
        Analyze insider activity for {ticker} based on:
        {context_insider}

        Are insiders buying or selling significantly? Is it routine selling or alarming?
        
        Output Requirements:
        - Distinguish between routine options exercise and opportunistic selling/buying.
        - Provide context on volume if available.
        - Direct answer only. No "Based on..." or intro text.
        """
        data.insider_activity = self.llm.analyze_text(prompt_insider).strip()
        print(f"      Result: {data.insider_activity[:100]}...")

        # 5. Dislocation / Price Action Context
        print("    - Analyzing Price Action Context...")
        query_drop = f"{ticker} stock price drop reason recent news"
        res_drop = self.search.search(query_drop, max_results=3)
        context_drop = "\n".join([r['content'] for r in res_drop])

        prompt_drop = f"""
        Analyze the recent price action of {ticker} based on:
        {context_drop}

        If the stock is down, is it due to macro factors/sector rotation (True Discount) or broken fundamentals/competitor threat (Fake Discount)?
        
        Output Requirements:
        - Analyze the drivers of price action.
        - Distinguish macro vs. company-specific issues.
        - Direct answer only. No "Based on..." or intro text.
        """
        data.dislocation_context = self.llm.analyze_text(prompt_drop).strip()
        print(f"      Result: {data.dislocation_context[:100]}...")

        # 6. Blue Sky Analysis (V3.2) - R&D & TAM
        print("    - Performing Blue Sky Analysis...")
        data.blue_sky = self._analyze_blue_sky(ticker)

        # 7. Catalyst Analysis (V3.2) - Events & Variant Perception
        print("    - Performing Catalyst Analysis...")
        data.catalysts = self._analyze_catalysts(ticker)

        return data

    def _analyze_blue_sky(self, ticker: str) -> BlueSkyData:
        blue_sky = BlueSkyData()
        
        # Search for R&D and TAM info
        query = f"{ticker} R&D investment areas new product expansion TAM analysis"
        print(f"      Searching for Blue Sky potential: {query}")
        results = self.search.search(query, max_results=3)
        context = "\n".join([r['content'] for r in results])
        
        # Analyze R&D Effectiveness (Second Curve)
        prompt_rnd = f"""
        Analyze the R&D strategy of {ticker} based on:
        {context}
        
        Are they investing in "Offensive R&D" (new markets/products like AWS for Amazon) or just maintenance?
        Do they have a clear "Second Growth Curve"?
        
        Output Requirements:
        - Include specific projects, investment amounts, and expected ROI/timelines if available.
        - Direct analysis only.
        - NO introductory phrases like "Based on the provided text".
        - NO Markdown headers (e.g. ## R&D).
        - Allow multi-paragraph deep dive; do not be overly concise.
        """
        blue_sky.rnd_effectiveness = self.llm.analyze_text(prompt_rnd).strip()
        print(f"      R&D Effectiveness: {blue_sky.rnd_effectiveness[:100]}...")
        
        # Analyze TAM Expansion
        prompt_tam = f"""
        Analyze the TAM (Total Addressable Market) expansion capability of {ticker} based on:
        {context}
        
        Does the management have a history of successfully crossing into new industries (TAM Expansion)?
        Is the TAM static or dynamic?
        
        Output Requirements:
        - Provide evidence of TAM expansion (e.g., new geographies, customer segments).
        - Direct analysis only.
        - NO introductory phrases.
        - NO Markdown headers.
        - Allow multi-paragraph deep dive.
        """
        blue_sky.tam_expansion = self.llm.analyze_text(prompt_tam).strip()
        print(f"      TAM Expansion: {blue_sky.tam_expansion[:100]}...")
        
        return blue_sky

    def _analyze_catalysts(self, ticker: str) -> CatalystData:
        catalyst = CatalystData()
        
        # Search for upcoming events
        query_events = f"{ticker} upcoming earnings date investor day product launch 2025"
        print(f"      Searching for Catalysts: {query_events}")
        results = self.search.search(query_events, max_results=3)
        context = "\n".join([r['content'] for r in results])
        
        prompt_events = f"""
        List upcoming major events for {ticker} in the next 3-9 months based on:
        {context}
        
        Focus on: Earnings, Investor Days, Product Launches.
        Return a list of strings, e.g. ["Earnings: Aug 25", "Investor Day: Oct 10"].
        Do NOT include "None" or empty items if possible.
        """
        events_text = self.llm.analyze_text(prompt_events, system_prompt="List specific events. Direct output only.")
        # Simple split by newline for list, cleaning up
        catalyst.upcoming_events = [line.strip('- *') for line in events_text.split('\n') if line.strip()]
        print(f"      Upcoming Events: {catalyst.upcoming_events}")
        
        # Analyze Variant Perception
        query_var = f"{ticker} wall street consensus vs reality KPI tracking"
        print(f"      Searching for Variant Perception: {query_var}")
        results_var = self.search.search(query_var, max_results=3)
        context_var = "\n".join([r['content'] for r in results_var])
        
        prompt_var = f"""
        Identify any "Variant Perception" for {ticker}.
        Context: {context_var}
        
        Is there a gap between Wall Street consensus and alternative data/reality?
        
        Output Requirements:
        - Start directly with the core Variant Perception.
        - NO "Based on the text".
        - NO Markdown headers (e.g. ## Variant Perception).
        - Be provocative but grounded in data.
        """
        catalyst.variant_perception = self.llm.analyze_text(prompt_var).strip()
        print(f"      Variant Perception: {catalyst.variant_perception[:100]}...")
        
        return catalyst
