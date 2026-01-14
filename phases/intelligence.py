from tools.llm import LLMClient
from tools.search import SearchClient
from core.data_models import IntelligenceData, IdentifierData, BlueSkyData, CatalystData
from typing import Dict, Any, List


class Intelligence:
    def __init__(self, llm_client: LLMClient, search_client: SearchClient):
        self.llm = llm_client
        self.search = search_client

    def gather(self, ticker: str, identifier_data: IdentifierData) -> IntelligenceData:
        data = IntelligenceData()

        # 1. Verify Specific KPIs
        kpi_values = {}
        for kpi in identifier_data.specific_kpis:
            query = f"{ticker} {kpi} latest quarter 2024 2025 financial results"
            search_results = self.search.search(query, max_results=3)
            context = "\n".join([r['content'] for r in search_results if r and 'content' in r])

            prompt = f"""
            Based on the search results below, extract the latest value for the KPI: {kpi} for {ticker}.
            If found, provide the value and a brief context (e.g., "120% (Q3 2024)").
            If not found, return "Not Found".

            Search Results:
            {context}
            """
            val = self.llm.analyze_text(prompt, system_prompt="Extract financial data precisely.")
            kpi_values[kpi] = val.strip()

        data.kpi_values = kpi_values

        # 2. Soft Factors - Management Integrity
        query_mgmt = f"{ticker} management guidance track record beat miss history"
        res_mgmt = self.search.search(query_mgmt, max_results=3)
        context_mgmt = "\n".join([r['content'] for r in res_mgmt])

        prompt_mgmt = f"""
        Analyze the management integrity of {ticker} based on:
        {context_mgmt}

        Do they have a history of over-promising and under-delivering? Or are they conservative ("sandbaggers")?
        Summarize in 2-3 sentences.
        """
        data.management_integrity = self.llm.analyze_text(prompt_mgmt).strip()

        # 3. Soft Factors - Moat/Competition
        query_moat = f"{ticker} competitive advantage moat analysis new products"
        res_moat = self.search.search(query_moat, max_results=3)
        context_moat = "\n".join([r['content'] for r in res_moat])

        prompt_moat = f"""
        Analyze the competitive moat of {ticker} based on:
        {context_moat}

        Is their moat widening or narrowing? Any new products driving growth?
        Summarize in 2-3 sentences.
        """
        data.product_moat = self.llm.analyze_text(prompt_moat).strip()

        # 4. Insider Activity
        query_insider = f"{ticker} insider trading recent selling buying"
        res_insider = self.search.search(query_insider, max_results=3)
        context_insider = "\n".join([r['content'] for r in res_insider])

        prompt_insider = f"""
        Analyze insider activity for {ticker} based on:
        {context_insider}

        Are insiders buying or selling significantly? Is it routine selling or alarming?
        Summarize in 2-3 sentences.
        """
        data.insider_activity = self.llm.analyze_text(prompt_insider).strip()

        # 5. Dislocation / Price Action Context
        query_drop = f"{ticker} stock price drop reason recent news"
        res_drop = self.search.search(query_drop, max_results=3)
        context_drop = "\n".join([r['content'] for r in res_drop])

        prompt_drop = f"""
        Analyze the recent price action of {ticker} based on:
        {context_drop}

        If the stock is down, is it due to macro factors/sector rotation (True Discount) or broken fundamentals/competitor threat (Fake Discount)?
        """
        data.dislocation_context = self.llm.analyze_text(prompt_drop).strip()

        # 6. Blue Sky Analysis (V3.2) - R&D & TAM
        data.blue_sky = self._analyze_blue_sky(ticker)

        # 7. Catalyst Analysis (V3.2) - Events & Variant Perception
        data.catalysts = self._analyze_catalysts(ticker)

        return data

    def _analyze_blue_sky(self, ticker: str) -> BlueSkyData:
        blue_sky = BlueSkyData()
        
        # Search for R&D and TAM info
        query = f"{ticker} R&D investment areas new product expansion TAM analysis"
        results = self.search.search(query, max_results=3)
        context = "\n".join([r['content'] for r in results])
        
        # Analyze R&D Effectiveness (Second Curve)
        prompt_rnd = f"""
        Analyze the R&D strategy of {ticker} based on:
        {context}
        
        Are they investing in "Offensive R&D" (new markets/products like AWS for Amazon) or just maintenance?
        Do they have a clear "Second Growth Curve"?
        """
        blue_sky.rnd_effectiveness = self.llm.analyze_text(prompt_rnd).strip()
        
        # Analyze TAM Expansion
        prompt_tam = f"""
        Analyze the TAM (Total Addressable Market) expansion capability of {ticker} based on:
        {context}
        
        Does the management have a history of successfully crossing into new industries (TAM Expansion)?
        Is the TAM static or dynamic?
        """
        blue_sky.tam_expansion = self.llm.analyze_text(prompt_tam).strip()
        
        return blue_sky

    def _analyze_catalysts(self, ticker: str) -> CatalystData:
        catalyst = CatalystData()
        
        # Search for upcoming events
        query_events = f"{ticker} upcoming earnings date investor day product launch 2025"
        results = self.search.search(query_events, max_results=3)
        context = "\n".join([r['content'] for r in results])
        
        prompt_events = f"""
        List upcoming major events for {ticker} in the next 3-9 months based on:
        {context}
        
        Focus on: Earnings, Investor Days, Product Launches.
        Return a list of strings, e.g. ["Earnings: Aug 25", "Investor Day: Oct 10"].
        """
        events_text = self.llm.analyze_text(prompt_events, system_prompt="List specific events.")
        # Simple split by newline for list, cleaning up
        catalyst.upcoming_events = [line.strip('- *') for line in events_text.split('\n') if line.strip()]
        
        # Analyze Variant Perception
        query_var = f"{ticker} wall street consensus vs reality KPI tracking"
        results_var = self.search.search(query_var, max_results=3)
        context_var = "\n".join([r['content'] for r in results_var])
        
        prompt_var = f"""
        Identify any "Variant Perception" for {ticker}.
        Context: {context_var}
        
        Is there a gap between Wall Street consensus and alternative data/reality?
        """
        catalyst.variant_perception = self.llm.analyze_text(prompt_var).strip()
        
        return catalyst
