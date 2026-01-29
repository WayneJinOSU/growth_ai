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
        
        # Define helper locally to capture references
        def _collect_refs(results):
            new_refs = []
            for r in results:
                if r.get('url'):
                    if not any(ref.url == r['url'] for ref in references):
                        new_id = len(references) + 1
                        ref = SearchReference(id=new_id, title=r.get('title',''), url=r['url'])
                        references.append(ref)
                        new_refs.append(ref)
                    else:
                        existing = next(ref for ref in references if ref.url == r['url'])
                        new_refs.append(existing)
            
            parts = []
            for r, ref in zip(results, new_refs):
                parts.append(f"[{ref.id}] {ref.title}: {r.get('content','')}")
            return "\n\n".join(parts)

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
        
        # Helper for this scope if we can't access outer one.
        # Ideally we'd pass the helper function or move to class method but 
        # duplicating valid logic is safer for 1-shot tool calls.
        def _collect_refs(results):
            if references is None: return ""
            new_refs = []
            for r in results:
                if r.get('url'):
                    if not any(ref.url == r['url'] for ref in references):
                        new_id = len(references) + 1
                        ref = SearchReference(id=new_id, title=r.get('title',''), url=r['url'])
                        references.append(ref)
                        new_refs.append(ref)
                    else:
                        existing = next(ref for ref in references if ref.url == r['url'])
                        new_refs.append(existing)
            parts = []
            for r, ref in zip(results, new_refs):
                parts.append(f"[{ref.id}] {ref.title}: {r.get('content','')}")
            return "\n\n".join(parts)

        # Search for macro tailwinds - removed hardcoded years and duplicates
        query = f"{search_name} macro tailwind industry trend demand driver recent"
        print(f"      Searching: {query}")
        # V3.5 Optimize: 8 results/365 days for industry-wide macro trends
        results = self.search.search(query, max_results=8, days=365)
        
        if references is not None:
             context = _collect_refs(results)
        else:
             context = "\n".join([r["content"] for r in results if r and "content" in r])

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
        # Identify upcoming hard events - Use get_press_releases for official announcements
        print(f"      Searching for official announcements...")
        # V3.5 Optimize: 5 results for more comprehensive event coverage
        results = self.search.get_press_releases(ticker, limit=5)
        if references is not None:
             def _collect_refs_inner(results):
                # Re-use logic or just inline simple version since we are inside a method
                # Better to use the main _collect_refs via a helper or duplicated for now
                # Given scope, simpler to just inline the ID logic here again or move to class method
                # Let's assume we copy the logic from analyze() or make analyze() pass a helper
                # For expedience in this tool call, I will duplicate the ID logic briefly 
                # actually I can't access analyze scope. 
                # Let's adhere to the pattern:
                new_refs = []
                for r in results:
                    if r.get('url'):
                        if not any(ref.url == r['url'] for ref in references):
                            new_id = len(references) + 1
                            ref = SearchReference(id=new_id, title=r.get('title',''), url=r['url'])
                            references.append(ref)
                            new_refs.append(ref)
                        else:
                            existing = next(ref for ref in references if ref.url == r['url'])
                            new_refs.append(existing)
                
                parts = []
                for r, ref in zip(results, new_refs):
                    parts.append(f"[{ref.id}] {ref.title}: {r.get('content','')}")
                return "\n\n".join(parts)
             
             context = _collect_refs_inner(results)
        else:
             context = "\n".join([r["content"] for r in results if r and "content" in r])

        # Extract events
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
        """

        analysis = self.llm.analyze_text(prompt_analysis).strip()
        print(f"      Analysis: {analysis[:100]}...")

        return events, analysis

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
