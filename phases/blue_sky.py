"""
Phase 4: Blue Sky & Valuation (蓝天展望 & 估值)
================================================
R&D 第二曲线、TAM 扩张分析，以及宏观调整估值。

核心功能:
1. Blue Sky Analysis: R&D 效能 (Offensive vs Maintenance) + TAM 扩张
2. Macro-Adjusted Valuation: 根据 MacroMode 动态调整 PE 倍数
"""

from tools.llm import LLMClient
from tools.search import SearchClient
from tools.fmp import FMPClient
from tools.search_helpers import SearchHelper
from tools.json_parser import JSONParser
from datetime import datetime
from core.data_models import BlueSkyPhaseData, BlueSkyData, GatekeeperData, MacroMode, BusinessModel, DeepAuditData


class BlueSkyAnalyzer:
    """
    Phase 4: 蓝天展望 & 估值分析器

    职责:
    - R&D 第二增长曲线评估
    - TAM (Total Addressable Market) 扩张能力
    - 基于宏观环境 (MacroMode) 的动态估值
    """

    MACRO_PE_ADJUSTMENTS = {
        MacroMode.LOOSE: {
            "bear_pe": 20,
            "target_pe": 30,
            "bull_pe": 45,
            "peg_max": 2.0,
        },
        MacroMode.NEUTRAL: {
            "bear_pe": 18,
            "target_pe": 25,
            "bull_pe": 35,
            "peg_max": 1.5,
        },
        MacroMode.TIGHT: {
            "bear_pe": 15,
            "target_pe": 20,
            "bull_pe": 25,
            "peg_max": 1.2,
        },
    }

    def __init__(self, llm_client=None, search_client=None, fmp_client=None, deep_client=None):
        from tools.deep_search import DeepSearchClient
        self.llm = llm_client or LLMClient()
        self.search = search_client or SearchClient()
        self.fmp = fmp_client or FMPClient()
        self.deep = deep_client or DeepSearchClient()
        self.sh = SearchHelper(self.search, self.deep)

    def analyze(self, data) -> BlueSkyPhaseData:
        """
        Execute Phase 4: Blue Sky & Valuation
        """
        ticker = data.ticker
        gatekeeper_data = data.gatekeeper
        references = data.references
        deep_search = data.deep_search
        business_model = data.identifier.business_model if data.identifier else None

        result = BlueSkyPhaseData()

        print(f"  [Phase 4] Analyzing Blue Sky & Valuation for {ticker}...")

        # 1. Blue Sky Analysis - R&D & TAM
        print("    - Performing Blue Sky Analysis...")
        result.blue_sky = self._analyze_blue_sky(ticker, references, deep_search)

        # 2. Macro-Adjusted Valuation
        if gatekeeper_data:
            print("    - [V3.5] Calculating Macro-Adjusted Valuation...")
            rule_of_40 = data.deep_audit.rule_of_40 if data.deep_audit else None
            result.macro_valuation_analysis = self._analyze_macro_adjusted_valuation(
                ticker, gatekeeper_data, business_model=business_model, rule_of_40=rule_of_40
            )

        return result

    def _analyze_blue_sky(self, ticker: str, references: list,
                          deep_search: bool = False) -> BlueSkyData:
        blue_sky = BlueSkyData()
        current_date = datetime.now().strftime('%Y-%m-%d')

        query = f"{ticker} R&D investment areas new product expansion TAM analysis"
        print(f"      Searching for Blue Sky potential: {query}")
        results = self.sh.unified_search(query, max_results=10, days=365, deep_search=deep_search)
        context = self.sh.collect_refs(results, references)

        if not context or len(context.strip()) < 50:
            print("      [Skip] Insufficient data for Blue Sky analysis")
            blue_sky.rnd_effectiveness = "N/A"
            blue_sky.tam_expansion = "N/A"
            return blue_sky

        prompt_rnd = f"""
        Current Date: {current_date}
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
        - CRITICAL: If the context lacks specific R&D or product information, output ONLY "N/A". Do not speculate.
        """
        blue_sky.rnd_effectiveness = self.llm.analyze_text(prompt_rnd).strip()
        print(f"      R&D Effectiveness: {blue_sky.rnd_effectiveness[:100]}...")

        prompt_tam = f"""
        Current Date: {current_date}
        Based on the Context and the company's R&D strategy, analyze the TAM expansion.
        
        Context: {context}
        R&D Strategy: {blue_sky.rnd_effectiveness}
        
        Task 1 (Deep Analysis):
        Analyze the TAM (Total Addressable Market) expansion capability of {ticker} based on the Context.
        Does the management have a history of successfully crossing into new industries (TAM Expansion)?
        Is the TAM static or dynamic?
        Provide evidence of TAM expansion (e.g., new geographies, customer segments).
        
        Task 2 (Conclusion):
        Based on BOTH the R&D Strategy and your TAM expansion analysis, does this company possess a "Strong Second Curve"?
        A strong second curve is defined as explosive growth indicators (e.g., >50% growth, doubling, breakthrough technology, massive new TAM expansion, clear second curve).
        
        Output MUST be valid JSON format exactly like this:
        {{
            "tam_expansion": "Your detailed, multi-paragraph deep dive analysis goes here (string). Cite sources using [ID] format. If the context lacks specific TAM data, output ONLY 'N/A'.",
            "is_strong_second_curve": true or false
        }}
        """
        tam_result = self.llm.analyze_text(prompt_tam).strip()
        tam_data = JSONParser.parse_llm_json(tam_result, default={})
        blue_sky.tam_expansion = tam_data.get("tam_expansion", "N/A")
        blue_sky.is_strong_second_curve = tam_data.get("is_strong_second_curve", False)
        print(f"      TAM Expansion: {blue_sky.tam_expansion[:100]}...")
        print(f"      Strong Second Curve Detected: {blue_sky.is_strong_second_curve}")


        return blue_sky

    def _analyze_macro_adjusted_valuation(self, ticker: str, gatekeeper_data: GatekeeperData, 
                                          business_model: BusinessModel = None, rule_of_40: float = None) -> str:
        """
        根据当前宏观环境 (MacroMode) 调整估值倍数，计算 Bear/Target/Bull Case。
        """
        macro_mode = gatekeeper_data.macro_mode
        us10y = gatekeeper_data.us10y_yield
        vix = gatekeeper_data.vix_value

        valuation_params = self.MACRO_PE_ADJUSTMENTS.get(macro_mode, self.MACRO_PE_ADJUSTMENTS[MacroMode.NEUTRAL])

        print(f"      Macro Mode: {macro_mode.value}")
        print(f"      Adjusted PE Parameters: Bear={valuation_params['bear_pe']}x, Target={valuation_params['target_pe']}x, Bull={valuation_params['bull_pe']}x")
        print(f"      Max Allowed PEG: {valuation_params['peg_max']}")

        current_pe = None
        current_price = None
        if self.fmp:
            quote = self.fmp.get_quote(ticker)
            ratios = self.fmp.get_ratios_ttm(ticker)
            if quote:
                current_price = quote.get('price')
            if ratios:
                current_pe = ratios.get('peRatioTTM')

        analysis_parts = []
        analysis_parts.append(f"Macro Environment: {macro_mode.value} (US10Y: {us10y:.2f}%)" if us10y else f"Macro Environment: {macro_mode.value}")
        if vix:
            vix_status = "⚠️ PANIC" if vix > 30 else "Normal"
            analysis_parts.append(f"VIX: {vix:.1f} ({vix_status})")

        # --- V3.5 SaaS Specific P/S Track ---
        if business_model in [BusinessModel.SAAS, BusinessModel.CONSUMPTION]:
            eff_rule_of_40 = rule_of_40 or 0
            # Target P/S Formula: 5.0 + max(0, (rule_of_40 - 0.30) * 100 * 0.4)
            target_ps = 5.0 + max(0, (eff_rule_of_40 - 0.30) * 100 * 0.4)
            bear_ps = target_ps * 0.7 if macro_mode == MacroMode.TIGHT else target_ps * 0.8
            bull_ps = target_ps * 1.05 if macro_mode == MacroMode.TIGHT else target_ps * 1.2
            
            analysis_parts.append("\nValuation Parameters (SaaS P/S Model):")
            analysis_parts.append(f"  - Business Model: {business_model.value}")
            analysis_parts.append(f"  - Rule of 40: {eff_rule_of_40:.1%}")
            analysis_parts.append(f"  - Bear Case (Forward P/S): {bear_ps:.1f}x")
            analysis_parts.append(f"  - Target Case (Forward P/S): {target_ps:.1f}x")
            analysis_parts.append(f"  - Bull Case (Forward P/S): {bull_ps:.1f}x")
            
            # Note: Need FMP integration to retrieve current P/S or Sales/Share 
            # for full dynamic output. We output the multiplier targets clearly.
            analysis_parts.append("\n[Action]: P/S Anchors calculated. Use these multiples to gauge current Market Cap against Forward Sales.")
            
        else:
            # --- Traditional PE Track ---
            analysis_parts.append("\nValuation Parameters (Macro-Adjusted PE):")
            analysis_parts.append(f"  - Bear Case PE: {valuation_params['bear_pe']}x")
            analysis_parts.append(f"  - Target PE: {valuation_params['target_pe']}x")
            analysis_parts.append(f"  - Bull Case PE: {valuation_params['bull_pe']}x")
            analysis_parts.append(f"  - Max Acceptable PEG: {valuation_params['peg_max']}")

            if current_pe and current_price:
                analysis_parts.append("\nCurrent Valuation (PE):")
                analysis_parts.append(f"  - Price: ${current_price:.2f}")
                analysis_parts.append(f"  - PE (TTM): {current_pe:.1f}x")

                if current_pe > 0:
                    eps = current_price / current_pe
                    bear_price = eps * valuation_params['bear_pe']
                    target_price = eps * valuation_params['target_pe']
                    bull_price = eps * valuation_params['bull_pe']

                    analysis_parts.append(f"\nImplied Price Targets (Based on EPS ${eps:.2f}):")
                    analysis_parts.append(f"  - Bear Case: ${bear_price:.2f} ({((bear_price/current_price)-1)*100:+.1f}%)")
                    analysis_parts.append(f"  - Target: ${target_price:.2f} ({((target_price/current_price)-1)*100:+.1f}%)")
                    analysis_parts.append(f"  - Bull Case: ${bull_price:.2f} ({((bull_price/current_price)-1)*100:+.1f}%)")

                    if current_price < bear_price:
                        analysis_parts.append("\n✅ STRONG BUY ZONE: Current price below Bear Case")
                    elif current_price < target_price:
                        analysis_parts.append("\n✓ BUY ZONE: Current price between Bear and Target")
                    elif current_price < bull_price:
                        analysis_parts.append("\n⚠️ HOLD ZONE: Current price between Target and Bull")
                    else:
                        analysis_parts.append("\n❌ SELL ZONE: Current price above Bull Case")

        return "\n".join(analysis_parts)
