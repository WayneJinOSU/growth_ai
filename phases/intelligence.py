"""
Phase 3: Intelligence (情报收集) + Phase 4: Valuation (估值)
============================================================
收集软实力指标、蓝天分析、催化剂事件，并进行宏观调整估值。

核心功能:
1. Phase 3: Intelligence (KPI 验证, 管理层诚信, 护城河)
2. Phase 4: Valuation & Catalysts (蓝天分析, 催化剂, 宏观调整估值)
"""


from tools.llm import LLMClient
from tools.search import SearchClient
from tools.fmp import FMPClient
from core.data_models import IntelligenceData, IdentifierData, BlueSkyData, CatalystData, GatekeeperData, MacroMode


class Intelligence:
    """
    情报收集器：MGP 策略的第三道关卡
    
    V3.5 扩展职责：
    - 收集软实力指标和特异性 KPI
    - 宏观调整估值：根据 MacroMode 调整估值倍数
    """
    
    # V3.5 宏观调整估值参数
    MACRO_PE_ADJUSTMENTS = {
        MacroMode.LOOSE: {
            "bear_pe": 20,      # 宽松环境下，Bear Case PE 可放宽至 20x
            "target_pe": 30,    # 目标 PE
            "bull_pe": 45,      # 牛市 PE
            "peg_max": 2.0,     # 允许 PEG 最高 2.0
        },
        MacroMode.NEUTRAL: {
            "bear_pe": 18,      # 中性环境
            "target_pe": 25,
            "bull_pe": 35,
            "peg_max": 1.5,     # PEG 严格 < 1.5
        },
        MacroMode.TIGHT: {
            "bear_pe": 15,      # 紧缩环境，强制 Bear Case PE = 15x
            "target_pe": 20,
            "bull_pe": 25,
            "peg_max": 1.2,     # PEG 必须 < 1.0~1.2
        },
    }

    def __init__(self, llm_client: LLMClient, search_client: SearchClient, fmp_client: FMPClient = None):
        self.llm = llm_client
        self.search = search_client
        self.fmp = fmp_client

    def gather(self, ticker: str, identifier_data: IdentifierData, 
               gatekeeper_data: GatekeeperData = None) -> IntelligenceData:
        """
        收集 Phase 3 & 4 数据
        """
        data = IntelligenceData()

        # ========== Phase 3: Intelligence (Soft Skills) ==========
        print(f"  [Phase 3] Gathering Intelligence for {ticker}...")

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

        # ========== Phase 4: Valuation & Catalysts ==========
        print(f"  [Phase 4] Analyzing Valuation & Catalysts for {ticker}...")

        # 6. Blue Sky Analysis (V3.5) - R&D & TAM
        print("    - Performing Blue Sky Analysis...")
        data.blue_sky = self._analyze_blue_sky(ticker)

        # 7. Catalyst Analysis (V3.5) - Events & Variant Perception
        print("    - Performing Catalyst Analysis...")
        data.catalysts = self._analyze_catalysts(ticker)

        # 8. [V3.5] Macro-Adjusted Valuation Analysis
        if gatekeeper_data:
            print("    - [V3.5] Calculating Macro-Adjusted Valuation...")
            valuation_analysis = self._analyze_macro_adjusted_valuation(ticker, gatekeeper_data)
            data.kpi_values["macro_valuation_analysis"] = valuation_analysis

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
        
        # Analyze Catalyst Impact (Narrative)
        prompt_analysis = f"""
        Analyze the strategic impact of these upcoming events for {ticker}:
        {events_text}
        
        Context:
        {context}
        
        Which event is the most critical? What is the expected market reaction?
        
        Output Requirements:
        - Provide a detailed 1-2 paragraph analysis.
        - Focus on the "So What?" (Implications).
        - Do NOT just list the dates again; explain their significance.
        - Direct output only.
        """
        catalyst.catalyst_analysis = self.llm.analyze_text(prompt_analysis).strip()
        print(f"      Catalyst Analysis: {catalyst.catalyst_analysis[:100]}...")

        
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

    # ========== V3.5 Macro-Adjusted Valuation ==========

    def _analyze_macro_adjusted_valuation(self, ticker: str, gatekeeper_data: GatekeeperData) -> str:
        """
        V3.5 宏观调整估值分析
        
        根据当前宏观环境 (MacroMode) 调整估值倍数，计算 Bear/Target/Bull Case
        
        Args:
            ticker: 股票代码
            gatekeeper_data: Gatekeeper 数据 (包含 MacroMode)
            
        Returns:
            str: 估值分析结果
        """
        macro_mode = gatekeeper_data.macro_mode
        us10y = gatekeeper_data.us10y_yield
        vix = gatekeeper_data.vix_value
        
        # 获取宏观调整后的估值参数
        valuation_params = self.MACRO_PE_ADJUSTMENTS.get(macro_mode, self.MACRO_PE_ADJUSTMENTS[MacroMode.NEUTRAL])
        
        print(f"      Macro Mode: {macro_mode.value}")
        print(f"      Adjusted PE Parameters: Bear={valuation_params['bear_pe']}x, Target={valuation_params['target_pe']}x, Bull={valuation_params['bull_pe']}x")
        print(f"      Max Allowed PEG: {valuation_params['peg_max']}")
        
        # 获取当前估值数据 (如果 FMP 可用)
        current_pe = None
        current_price = None
        if self.fmp:
            quote = self.fmp.get_quote(ticker)
            ratios = self.fmp.get_ratios_ttm(ticker)
            if quote:
                current_price = quote.get('price')
            if ratios:
                current_pe = ratios.get('peRatioTTM')
        
        # 构建估值分析
        analysis_parts = []
        analysis_parts.append("=== V3.5 Macro-Adjusted Valuation ===")
        analysis_parts.append(f"Macro Environment: {macro_mode.value} (US10Y: {us10y:.2f}%)" if us10y else f"Macro Environment: {macro_mode.value}")
        if vix:
            vix_status = "⚠️ PANIC" if vix > 30 else "Normal"
            analysis_parts.append(f"VIX: {vix:.1f} ({vix_status})")
        
        analysis_parts.append("\nValuation Parameters (Macro-Adjusted):")
        analysis_parts.append(f"  - Bear Case PE: {valuation_params['bear_pe']}x")
        analysis_parts.append(f"  - Target PE: {valuation_params['target_pe']}x")
        analysis_parts.append(f"  - Bull Case PE: {valuation_params['bull_pe']}x")
        analysis_parts.append(f"  - Max Acceptable PEG: {valuation_params['peg_max']}")
        
        if current_pe and current_price:
            analysis_parts.append("\nCurrent Valuation:")
            analysis_parts.append(f"  - Price: ${current_price:.2f}")
            analysis_parts.append(f"  - PE (TTM): {current_pe:.1f}x")
            
            # 计算隐含的 Bear/Target/Bull 价格
            if current_pe > 0:
                eps = current_price / current_pe
                bear_price = eps * valuation_params['bear_pe']
                target_price = eps * valuation_params['target_pe']
                bull_price = eps * valuation_params['bull_pe']
                
                analysis_parts.append(f"\nImplied Price Targets (Based on EPS ${eps:.2f}):")
                analysis_parts.append(f"  - Bear Case: ${bear_price:.2f} ({((bear_price/current_price)-1)*100:+.1f}%)")
                analysis_parts.append(f"  - Target: ${target_price:.2f} ({((target_price/current_price)-1)*100:+.1f}%)")
                analysis_parts.append(f"  - Bull Case: ${bull_price:.2f} ({((bull_price/current_price)-1)*100:+.1f}%)")
                
                # 投资建议
                if current_price < bear_price:
                    analysis_parts.append("\n✅ STRONG BUY ZONE: Current price below Bear Case")
                elif current_price < target_price:
                    analysis_parts.append("\n✓ BUY ZONE: Current price between Bear and Target")
                elif current_price < bull_price:
                    analysis_parts.append("\n⚠️ HOLD ZONE: Current price between Target and Bull")
                else:
                    analysis_parts.append("\n❌ SELL ZONE: Current price above Bull Case")
        
        return "\n".join(analysis_parts)
