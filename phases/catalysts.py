"""
Phase 5: Catalysts & Waves (势能与催化)
=======================================
V3.5 Blue Sky Edition

核心修正：宏观需求 (Macro Need) > 微观事件 (Micro Events)

1. 一级催化：全行业势能 (Thematic Waves)
   - 不需要看财报就能感知的"不可逆刚需"
   - 例: 劳动力短缺 -> AI 刚需; 地缘政治 -> 预算溢出

2. 二级催化：硬事件 (Hard Events)
   - 财报日、产品换代等具体验证节点
"""

from tools.llm import LLMClient
from tools.search import SearchClient
from core.data_models import CatalystData, SearchReference


class CatalystsAnalyzer:
    """
    Phase 5: Catalysts & Waves Analyzer
    """

    # Known Thematic Waves (can be expanded)
    KNOWN_THEMATIC_WAVES = {
        "labor_shortage_ai": {
            "trigger": ["labor shortage", "workforce shortage", "hiring crisis"],
            "beneficiaries": ["AI automation", "robotics", "software efficiency"],
            "description": "Labor Shortage → AI/Automation Demand",
        },
        "geopolitical_defense": {
            "trigger": ["defense budget", "military spending", "geopolitical tension"],
            "beneficiaries": ["defense", "cybersecurity", "intelligence software"],
            "description": "Geopolitical Tension → Defense Budget Overflow",
        },
        "cloud_migration": {
            "trigger": ["cloud adoption", "digital transformation", "legacy migration"],
            "beneficiaries": ["cloud infrastructure", "SaaS", "cybersecurity"],
            "description": "Cloud Migration → Infrastructure Demand",
        },
        "ai_infrastructure": {
            "trigger": ["AI infrastructure", "GPU demand", "AI compute"],
            "beneficiaries": ["semiconductors", "data centers", "AI chips"],
            "description": "AI Boom → Infrastructure Bottleneck",
        },
        "regulatory_compliance": {
            "trigger": ["regulatory compliance", "data privacy", "audit requirements"],
            "beneficiaries": ["GRC software", "identity management", "legal tech"],
            "description": "Regulation Wave → Compliance Spending",
        },
    }

    def __init__(self, llm_client: LLMClient, search_client: SearchClient):
        self.llm = llm_client
        self.search = search_client

    def analyze(self, ticker: str, company_name: str = None, references: list = None) -> CatalystData:
        """
        Analyze Phase 5: Catalysts & Waves
        """
        data = CatalystData()
        if references is None:
            references = []

        # ========== Primary: Thematic Waves ==========
        print(f"    - [Phase 5] Identifying Thematic Waves for {ticker}...")
        data.thematic_waves, data.wave_strength = self._identify_thematic_waves(
            ticker, company_name, references
        )

        # ========== Secondary: Hard Events ==========
        print(f"    - [Phase 5] Identifying Hard Events for {ticker}...")
        data.upcoming_events, data.catalyst_analysis = self._identify_hard_events(
            ticker, references
        )

        return data

    def _identify_thematic_waves(
        self, ticker: str, company_name: str = None, references: list = None
    ) -> tuple[str, str]:
        """
        Identify macro thematic waves that the company is riding.
        """
        search_name = company_name or ticker

        # Search for macro tailwinds
        query = f"{search_name} macro tailwind industry trend demand driver 2024 2025"
        print(f"      Searching: {query}")
        # Search for macro tailwinds
        query = f"{search_name} macro tailwind industry trend demand driver 2024 2025"
        print(f"      Searching: {query}")
        results = self.search.search(query, max_results=4)
        
        if references is not None:
             for r in results:
                if r.get('url') and not any(ref.url == r['url'] for ref in references):
                    references.append(SearchReference(title=r.get('title',''), url=r['url']))
                    
        context = "\n".join([r["content"] for r in results if r and "content" in r])

        prompt = f"""
        Analyze the macro tailwinds for {ticker} ({company_name or ''}) based on:
        {context}

        Identify if the company is riding any of these THEMATIC WAVES:
        1. Labor Shortage → AI/Automation Demand (e.g., police AI, warehouse robotics)
        2. Geopolitical Tension → Defense Budget Overflow (e.g., defense software, surveillance)
        3. Cloud Migration → Infrastructure Demand (e.g., cloud security, SaaS)
        4. AI Infrastructure Boom → Compute Demand (e.g., GPUs, data centers)
        5. Regulatory Compliance → GRC/Identity Spending

        Output Format (STRICTLY follow):
        WAVE: [The primary thematic wave, or "None" if not applicable]
        STRENGTH: [High/Medium/Low/None]
        RATIONALE: [1-2 sentences explaining why this wave applies]

        Example:
        WAVE: Labor Shortage → AI/Automation Demand
        STRENGTH: High
        RATIONALE: Police departments face chronic staffing shortages; Axon's Draft One AI reduces report writing time by 80%, making it a mission-critical efficiency tool.

        Direct output only. No headers or extra text.
        """

        response = self.llm.analyze_text(prompt).strip()
        print(f"      LLM Response: {response[:150]}...")

        # Parse response
        wave = "None"
        strength = "None"
        for line in response.split("\n"):
            if line.strip().upper().startswith("WAVE:"):
                wave = line.split(":", 1)[1].strip()
            elif line.strip().upper().startswith("STRENGTH:"):
                strength = line.split(":", 1)[1].strip()

        if wave.lower() == "none" or not wave:
            wave = None
            strength = None
        else:
            # Normalize strength
            strength_map = {"high": "High", "medium": "Medium", "low": "Low"}
            strength = strength_map.get(strength.lower(), "Medium")

        return wave, strength

    def _identify_hard_events(self, ticker: str, references: list = None) -> tuple[list, str]:
        """
        Identify hard catalytic events (earnings, product launches, etc.)
        """
        query = f"{ticker} upcoming earnings date investor day product launch 2025 2026"
        print(f"      Searching: {query}")
        query = f"{ticker} upcoming earnings date investor day product launch 2025 2026"
        print(f"      Searching: {query}")
        results = self.search.search(query, max_results=3)
        if references is not None:
             for r in results:
                if r.get('url') and not any(ref.url == r['url'] for ref in references):
                    references.append(SearchReference(title=r.get('title',''), url=r['url']))
        context = "\n".join([r["content"] for r in results if r and "content" in r])

        # Extract events
        prompt_events = f"""
        List upcoming major events for {ticker} in the next 6 months based on:
        {context}

        Focus on:
        - Earnings Dates
        - Product Launches / Refresh Cycles
        - Investor Days / Analyst Days

        Return ONLY a simple list, one event per line.
        Example:
        - Earnings: Feb 25, 2025
        - Product Launch: Taser 11 expected Q2 2025
        - Investor Day: May 2025

        If no events found, return "None scheduled".
        """

        events_text = self.llm.analyze_text(
            prompt_events, system_prompt="List specific events only. Be concise."
        ).strip()
        events = [
            line.strip("- *")
            for line in events_text.split("\n")
            if line.strip() and line.strip().lower() != "none scheduled"
        ]
        print(f"      Events: {events}")

        # Analyze impact
        prompt_analysis = f"""
        Analyze the catalyst impact of these events for {ticker}:
        {events_text}

        Context:
        {context}

        Focus on:
        1. Which event is the most critical for stock price?
        2. What is the expected market reaction?

        Output: 1-2 paragraphs. Direct analysis only. No headers.
        """

        analysis = self.llm.analyze_text(prompt_analysis).strip()
        print(f"      Analysis: {analysis[:100]}...")

        return events, analysis
