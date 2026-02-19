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

3. 预期差 (Variant Perception)
   - 华尔街共识 vs 另类数据/现实的偏差
"""

from tools.llm import LLMClient
from tools.search import SearchClient
from tools.search_helpers import SearchHelper
from datetime import datetime
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

    def __init__(self, llm_client=None, search_client=None, deep_client=None):
        from tools.deep_search import DeepSearchClient
        self.llm = llm_client or LLMClient()
        self.search = search_client or SearchClient()
        self.deep = deep_client or DeepSearchClient()
        self.sh = SearchHelper(self.search, self.deep)

    # ========== Main Entry ==========

    def analyze(self, ticker: str, company_name: str = None,
                references: list = None, deep_search: bool = False,
                business_model: str = None) -> CatalystData:
        """
        Analyze Phase 5: Catalysts & Waves + Variant Perception
        """
        data = CatalystData()
        if references is None:
            references = []

        # ========== 1. Primary: Thematic Waves ==========
        print(f"    - [Phase 5] Identifying Thematic Waves for {ticker}...")
        data.thematic_waves, data.wave_strength = self._identify_thematic_waves(
            ticker, company_name, references, deep_search, business_model
        )

        # ========== 2. Secondary: Hard Events ==========
        print(f"    - [Phase 5] Identifying Hard Events for {ticker}...")
        data.upcoming_events, data.catalyst_analysis = self._identify_hard_events(
            ticker, references, deep_search
        )

        # ========== 3. Variant Perception ==========
        print(f"    - [Phase 5] Analyzing Variant Perception for {ticker}...")
        data.variant_perception = self._analyze_variant_perception(
            ticker, references, deep_search
        )

        return data

    # ========== Sub-Modules ==========

    def _identify_thematic_waves(
        self, ticker: str, company_name: str = None,
        references: list = None, deep_search: bool = False,
        business_model: str = None
    ) -> tuple[str, str]:
        """
        Identify macro thematic waves that the company is riding.
        """
        search_name = company_name or ticker

        query = f"{search_name} macro tailwind industry trend demand driver recent"

        results = []
        if deep_search:
            print("    [Deep Search] Generating matrix for Thematic Waves...")
            matrix = self.deep.generate_search_matrix(ticker, company_name, 
                "捕捉宏观浪潮(AI/Cloud/EV等) + 行业技术拐点 + 政策利好")
            deep_res, _ = self.deep.execute_matrix(matrix, business_model=business_model)
            results.extend(deep_res)

        print(f"      Searching: {query}")
        reg_res = self.sh.unified_search(query, max_results=8, days=365, deep_search=deep_search)
        results.extend(reg_res)
        
        if references is not None:
            context = self.sh.collect_refs(results, references)
        else:
            context = "\n".join([r["content"] for r in results if r and "content" in r])

        if not context or len(context.strip()) < 50:
            print("      [Skip] Insufficient data for thematic wave analysis")
            return None, None

        prompt = f"""
        Current Date: {datetime.now().strftime('%Y-%m-%d')}
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
        
        Use [ID] citations in RATIONALE if applicable.

        Example:
        WAVE: Labor Shortage → AI/Automation Demand
        STRENGTH: High
        RATIONALE: Police departments face chronic staffing shortages; Axon's Draft One AI reduces report writing time by 80%, making it a mission-critical efficiency tool [1].

        CRITICAL: If the context lacks specific evidence of macro tailwinds, output:
        WAVE: None
        STRENGTH: None
        RATIONALE: N/A
        Do not speculate or fabricate connections.
        """

        response = self.llm.analyze_text(prompt).strip()
        print(f"      LLM Response: {response[:150]}...")

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
            strength_map = {"high": "High", "medium": "Medium", "low": "Low"}
            strength = strength_map.get(strength.lower(), "Medium")

        return wave, strength

    def _identify_hard_events(self, ticker: str, references: list = None,
                              deep_search: bool = False) -> tuple[list, str]:
        """
        Identify upcoming hard catalyst events (earnings, product launches, investor days).
        """
        print("      Searching for official announcements...")
        results = self.search.get_press_releases(ticker, limit=5)

        if references is not None:
            context = self.sh.collect_refs(results, references)
        else:
            context = "\n".join([r["content"] for r in results if r and "content" in r])

        if not context or len(context.strip()) < 50:
            print("      [Skip] Insufficient data for hard events analysis")
            return [], "N/A"

        prompt_events = f"""
        Current Date: {datetime.now().strftime('%Y-%m-%d')}
        Identify major catalysts for {ticker} from the provided context based on {context}, 
        categorizing them into:
        1. **Recently Triggered** (Events within the last 30 days that are still driving price action)
        2. **Upcoming** (Future events in the next 6 months)
        
        Focus on:
        - Earnings Releases (Past results explaining momentum or future dates)
        - Product Launches / Refresh Cycles
        - Investor Days / Analyst Days

        CRITICAL: The AI should judge the significance. If an event happened 2 weeks ago but was a "game changer", include it as "Recently Triggered". 
        Focus on 2026 events or high-impact late 2025 milestones that recently concluded.

        Return ONLY a simple list, one event per line.
        CRITICAL: Every event MUST include a specific date or estimated quarter (e.g., "Feb 25, 2025" or "Q3 2025").
        
        Example:
        - Earnings: Feb 25, 2025 [1]
        - Product Launch: Taser 11 expected Q2 2025 [2]
        - Investor Day: May 2025 [3]
        
        Use [ID] citations if possible.
        CRITICAL: If the context lacks specific event dates or catalysts, output ONLY "N/A". Do not speculate.
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

        prompt_analysis = f"""
        Current Date: {datetime.now().strftime('%Y-%m-%d')}
        Analyze the catalyst impact of these events for {ticker}:
        {events_text}

        Context:
        {context}

        Focus on:
        1. Which event is the most critical for stock price?
        2. What is the expected market reaction?
        3. CRITICAL: Define the specific timeline/window of impact for each major catalyst.

        Output: 1-2 paragraphs. Direct analysis only. No headers.
        Use [ID] citations where appropriate.
        CRITICAL: If the events lack sufficient detail for meaningful analysis, output ONLY "N/A". Do not speculate.
        """

        analysis = self.llm.analyze_text(prompt_analysis).strip()
        print(f"      Analysis: {analysis[:100]}...")

        return events, analysis

    def _analyze_variant_perception(self, ticker: str, references: list = None,
                                    deep_search: bool = False) -> str:
        """
        Identify gaps between Wall Street consensus and alternative data/reality.
        Migrated from Intelligence phase — this is a catalyst-class insight.
        """
        if references is None:
            references = []

        query = f"{ticker} wall street consensus vs reality KPI tracking"
        print(f"      Searching for Variant Perception: {query}")
        results = self.sh.unified_search(query, max_results=10, days=365, deep_search=deep_search)
        context = self.sh.collect_refs(results, references)

        if not context or len(context.strip()) < 50:
            print("      [Skip] Insufficient data for variant perception analysis")
            return "N/A"

        prompt = f"""
        Current Date: {datetime.now().strftime('%Y-%m-%d')}
        Identify any "Variant Perception" for {ticker}.
        Context: {context}
        
        Is there a gap between Wall Street consensus and alternative data/reality?
        
        Output Requirements:
        - Start directly with the core Variant Perception.
        - NO "Based on the text".
        - NO Markdown headers (e.g. ## Variant Perception).
        - Be provocative but grounded in data.
        - IMPORTANT: Cite sources using [ID] format.
        - CRITICAL: If the context lacks specific data to identify a variant perception, output ONLY "N/A". Do not speculate.
        """
        result = self.llm.analyze_text(prompt).strip()
        print(f"      Variant Perception: {result[:100]}...")
        return result


catalystsAnalyzer = CatalystsAnalyzer()
if __name__ == "__main__":
    from tools.llm import LLMClient
    from tools.search import SearchClient
    
    llm = LLMClient()
    search = SearchClient()
    analyzer = CatalystsAnalyzer(llm, search)
    
    ticker = "AXON"
    print(f"Testing Catalysts Analyzer for {ticker}...")
    result = analyzer.analyze(ticker, company_name="Axon Enterprise")
    
    print("\n--- Thematic Waves ---")
    print(f"Wave: {result.thematic_waves}")
    print(f"Strength: {result.wave_strength}")
    
    print("\n--- Hard Events ---")
    for event in result.upcoming_events:
        print(f" - {event}")
        
    print("\n--- Analysis ---")
    print(result.catalyst_analysis)
    
    print("\n--- Variant Perception ---")
    print(result.variant_perception)
