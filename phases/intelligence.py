"""
Phase 3: Intelligence (情报收集) + Phase 4: Blue Sky & Valuation (蓝天展望 & 估值)
==================================================================================
收集软实力指标、蓝天分析，并进行宏观调整估值。
催化剂分析已移至 phases/catalysts.py (Phase 5)。

核心功能:
1. Phase 3: Intelligence (KPI 验证, 管理层诚信, 护城河, 内部人交易, 错杀分析)
2. Phase 4: Blue Sky & Valuation (R&D/TAM 蓝天分析, 宏观调整估值)
"""


from tools.llm import LLMClient
from tools.search import SearchClient
from tools.fmp import FMPClient
from tools.search_helpers import SearchHelper
from datetime import datetime
from core.data_models import IntelligenceData, IdentifierData, BlueSkyData, GatekeeperData, MacroMode, SearchReference


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

    def __init__(self, llm_client=None, search_client=None, fmp_client=None, deep_client=None):
        from tools.deep_search import DeepSearchClient
        self.llm = llm_client or LLMClient()
        self.search = search_client or SearchClient()
        self.fmp = fmp_client or FMPClient()
        self.deep = deep_client or DeepSearchClient()
        self.sh = SearchHelper(self.search, self.deep)

    # ========== Main Entry ==========

    def gather(self, ticker: str, identifier_data: IdentifierData, 
               gatekeeper_data: GatekeeperData = None, references: list = None,
               deep_search: bool = False) -> IntelligenceData:
        """
        收集 Phase 3 & 4 数据
        """
        data = IntelligenceData()
        if references is None:
            references = []
        
        # Deep Search Pre-Enrichment (matrix + echo loop for broad financial context)
        deep_context = ""
        if deep_search:
            print("  [Deep Search] Generating Financial Matrix & Echo Loop...")
            matrix = self.deep.generate_search_matrix(ticker, "", 
                "查找关键财务指标: Revenue Growth, Net Dollar Retention, CAC, Churn, FCF Margin, 管理层变动")
            deep_res, deep_ctx = self.deep.execute_matrix(matrix)
            extracted_gaps, deep_ctx_enriched = self.deep.run_echo_loop(ticker, deep_res)
            
            deep_context = deep_ctx_enriched
            print(f"  [Deep Search] Enriched Financial Context: {len(deep_context)} chars")
            
            for r in deep_res:
                if not any(ref.url == r.get('url') for ref in references):
                    references.append(SearchReference(
                        id=len(references)+1,
                        title=r.get('title',''),
                        url=r.get('url',''),
                        snippet=f"[Deep Search] {r.get('content','')[:100]}..."
                    ))

        # ========== Phase 3: Intelligence (Soft Skills) ==========
        print(f"  [Phase 3] Gathering Intelligence for {ticker}...")

        # 1. Verify Specific KPIs
        kpi_values = {}
        print(f"    - Verifying {len(identifier_data.specific_kpis)} KPIs...")
        for kpi in identifier_data.specific_kpis:
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

            prompt = f"""
            Current Date: {datetime.now().strftime('%Y-%m-%d')}
            Based on the search results below, extract the latest value for the KPI: {kpi} for {ticker}.
            If found, provide ONLY the value and a very brief context. It is CRITICAL to include the exact period/timestamp (e.g., "120% (Q3 2024)" or "Value: 10M as of Dec 2024").
            Do NOT include any introductory text or explanations.
            Use [ID] citations if applicable.
            If not found, return "Not Found".

            Search Results:
            {full_context}
            """
            val = self.llm.analyze_text(prompt, system_prompt="Extract financial data precisely. Direct output only.")
            kpi_values[kpi] = val.strip()
            print(f"      Result for {kpi}: {kpi_values[kpi]}")

        data.kpi_values = kpi_values

        # 2. Soft Factors - Management Integrity
        print("    - Analyzing Management Integrity...")
        res_mgmt = self.search.get_press_releases(ticker, limit=5)
        context_mgmt = self.sh.collect_refs(res_mgmt, references)

        prompt_mgmt = f"""
        Current Date: {datetime.now().strftime('%Y-%m-%d')}
        Analyze the management integrity of {ticker} based on:
        {context_mgmt}

        Do they have a history of over-promising and under-delivering? Or are they conservative ("sandbaggers")?
        
        Output Requirements:
        - Provide a detailed assessment citing specific guidance vs. actual performance examples.
        - IMPORTANT: Include specific dates or quarters for every example mentioned (e.g., "In Q2 2024, they promised... but by Nov 2024...").
        - Direct answer only. No "Based on..." or "The search results indicate...".
        - Do not limit length; be thorough.
        - Cite sources using [ID] format (e.g. "CEO stated growth is slowing [1]").
        """
        data.management_integrity = self.llm.analyze_text(prompt_mgmt).strip()
        print(f"      Result: {data.management_integrity[:100]}...")

        # 3. Soft Factors - Moat/Competition
        print("    - Analyzing Competitive Moat...")
        query_moat = f"{ticker} competitive advantage moat analysis new products"
        res_moat = self.sh.unified_search(query_moat, max_results=10, days=365, deep_search=deep_search)
        context_moat = self.sh.collect_refs(res_moat, references)

        prompt_moat = f"""
        Current Date: {datetime.now().strftime('%Y-%m-%d')}
        Analyze the competitive moat of {ticker} based on:
        {context_moat}

        Is their moat widening or narrowing? Any new products driving growth?
        
        Output Requirements:
        - Detail specific competitive advantages, new product traction, and competitive threats.
        - Use data where possible.
        - Direct answer only. No "Based on..." or intro text.
        - IMPORTANT: Cite sources using [ID] format at the end of claims.
        """
        data.product_moat = self.llm.analyze_text(prompt_moat).strip()
        print(f"      Result: {data.product_moat[:100]}...")

        # 4. Insider Activity
        print("    - Analyzing Insider Activity...")
        query_insider = f"{ticker} insider trading recent selling buying"
        res_insider = self.sh.unified_search(query_insider, max_results=5, days=90, deep_search=deep_search)
        context_insider = self.sh.collect_refs(res_insider, references)

        prompt_insider = f"""
        Current Date: {datetime.now().strftime('%Y-%m-%d')}
        Analyze insider activity for {ticker} based on:
        {context_insider}

        Are insiders buying or selling significantly? Is it routine selling or alarming?
        
        Output Requirements:
        - Distinguish between routine options exercise and opportunistic selling/buying.
        - IMPORTANT: Specify the exact dates or months of the recent transactions.
        - Provide context on volume if available.
        - Direct answer only. No "Based on..." or intro text.
        - Cite sources using [ID] format.
        """
        data.insider_activity = self.llm.analyze_text(prompt_insider).strip()
        print(f"      Result: {data.insider_activity[:100]}...")

        # 5. Dislocation / Price Action Context
        print("    - Analyzing Price Action Context...")
        query_drop = f"{ticker} stock price drop reason recent news"
        res_drop = self.sh.unified_search(query_drop, max_results=5, days=30, deep_search=deep_search)
        context_drop = self.sh.collect_refs(res_drop, references)

        prompt_drop = f"""
        Current Date: {datetime.now().strftime('%Y-%m-%d')}
        Analyze the recent price action of {ticker} based on:
        {context_drop}

        If the stock is down, is it due to macro factors/sector rotation (True Discount) or broken fundamentals/competitor threat (Fake Discount)?
        
        Output Requirements:
        - Analyze the drivers of price action.
        - IMPORTANT: Provide a timeline of the price action and key events (e.g., "Dropped 15% on Jan 12th following...").
        - Distinguish macro vs. company-specific issues.
        - Direct answer only. No "Based on..." or intro text.
        - Cite sources using [ID] format.
        """
        data.dislocation_context = self.llm.analyze_text(prompt_drop).strip()
        print(f"      Result: {data.dislocation_context[:100]}...")

        # ========== Phase 4: Blue Sky & Valuation ==========
        print(f"  [Phase 4] Analyzing Blue Sky & Valuation for {ticker}...")

        # 6. Blue Sky Analysis (V3.5) - R&D & TAM
        print("    - Performing Blue Sky Analysis...")
        data.blue_sky = self._analyze_blue_sky(ticker, references, deep_search=deep_search)

        # 7. [V3.5] Macro-Adjusted Valuation Analysis
        if gatekeeper_data:
            print("    - [V3.5] Calculating Macro-Adjusted Valuation...")
            valuation_analysis = self._analyze_macro_adjusted_valuation(ticker, gatekeeper_data)
            data.kpi_values["macro_valuation_analysis"] = valuation_analysis

        return data

    # ========== Phase 4 Sub-Modules ==========

    def _analyze_blue_sky(self, ticker: str, references: list,
                          deep_search: bool = False) -> BlueSkyData:
        blue_sky = BlueSkyData()

        query = f"{ticker} R&D investment areas new product expansion TAM analysis"
        print(f"      Searching for Blue Sky potential: {query}")
        results = self.sh.unified_search(query, max_results=10, days=365, deep_search=deep_search)
        context = self.sh.collect_refs(results, references)
        
        # Analyze R&D Effectiveness (Second Curve)
        prompt_rnd = f"""
        Current Date: {datetime.now().strftime('%Y-%m-%d')}
        Analyze the R&D strategy of {ticker} based on:
        {context}
        
        Are they investing in "Offensive R&D" (new markets/products like AWS for Amazon) or just maintenance?
        Do they have a clear "Second Growth Curve"?
        
        Output Requirements:
        - Include specific projects, investment amounts, and CRITICAL: Include specific target dates or expected launch timelines.
        - Direct analysis only.
        - NO introductory phrases like "Based on the provided text".
        - NO Markdown headers (e.g. ## R&D).
        - Allow multi-paragraph deep dive; do not be overly concise.
        - Cite specific sources using [ID] format (e.g. "R&D budget increased 15% [2]").
        """
        blue_sky.rnd_effectiveness = self.llm.analyze_text(prompt_rnd).strip()
        print(f"      R&D Effectiveness: {blue_sky.rnd_effectiveness[:100]}...")
        
        # Analyze TAM Expansion
        prompt_tam = f"""
        Current Date: {datetime.now().strftime('%Y-%m-%d')}
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
        - IMPORTANT: Cite sources using [ID] format.
        """
        blue_sky.tam_expansion = self.llm.analyze_text(prompt_tam).strip()
        print(f"      TAM Expansion: {blue_sky.tam_expansion[:100]}...")
        
        return blue_sky

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

intelligence = Intelligence()
