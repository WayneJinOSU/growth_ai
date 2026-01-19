"""
Phase 3 & 5: Entry & Valuation + Final Tribunal - V3.7 Armored Sniper
=====================================================================
利用"当前数据的难看"买入"未来的爆发"，并输出最终决策。

V3.7 估值逻辑:
1. 前瞻性定价 (Forward Spring Pricing) - Forward PE < 20x
2. PEG 安全网 - PEG < 0.6 (加分项)
3. 历史 PE Z-Score - Current PE < (5yr Avg - 1 Std Dev)
4. "厨房水槽"买点 - 财报爆雷但股价不跌

V3.7 最终评级:
- TACTICAL SNIPER: 基本面沙袋 + 估值低 + 宏观允许
- STRATEGIC COMPOUNDER: 技术独占窗口 > 3年 + 巨头客户背书
- TRAP: CFO < NI 或核心技术人员离职

数据源: yfinance (Forward Data) + FMP (Historical Ratios)
"""

from typing import List
import numpy as np
from core.data_models import (
    CompanyData, TribunalDecision, Decision, Confidence,
    ValuationData
)
from tools.llm import LLMClient
from tools.fmp import FMPClient
from tools.yfinance_client import YFinanceClient
import json


class Tribunal:
    """
    V3.7 最终审判 + 估值分析
    
    职责：
    - 执行 V3.7 估值弹簧检查 (Forward PE, PEG, Z-Score)
    - 检测 "厨房水槽" 买点
    - 综合所有 Phase 数据输出最终评级
    """
    
    # V3.7 估值阈值
    FORWARD_PE_THRESHOLD = 20.0  # Forward PE < 20x 触发买入
    PEG_THRESHOLD = 0.6          # PEG < 0.6 加分项
    PE_ZSCORE_THRESHOLD = -1.0   # Z-Score < -1 表示历史底部
    
    # 紧急弹射关键词
    EMERGENCY_EJECT_KEYWORDS = [
        "CTO resign", "CTO departure", "CTO leaving", "CTO quit",
        "CFO resign", "CFO departure", "CFO leaving",
        "CEO resign", "CEO departure", "CEO stepping down",
        "chief technology officer leaving", "chief financial officer resign",
        "key executive departure", "management exodus",
        "lost contract", "contract terminated", "major customer loss",
        "fraud", "SEC investigation", "accounting irregularities",
        "restatement", "material weakness"
    ]

    def __init__(self, llm_client: LLMClient, fmp_client: FMPClient = None, yf_client: YFinanceClient = None):
        self.llm = llm_client
        self.fmp = fmp_client
        self.yf = yf_client or YFinanceClient()

    # ========== V3.7 Valuation Analysis ==========

    def analyze_valuation(self, ticker: str) -> ValuationData:
        """
        V3.7 估值弹簧分析
        
        Args:
            ticker: 股票代码
            
        Returns:
            ValuationData: 估值数据
        """
        print(f"  [Phase 3] Valuation Analysis for {ticker}...")
        
        valuation = ValuationData()
        
        # ========== 1. Forward Spring Pricing (yfinance) ==========
        print("    - Fetching Forward PE from yfinance...")
        yf_data = self.yf.get_valuation_data(ticker)
        
        valuation.forward_pe = yf_data.get('forward_pe')
        valuation.peg_ratio = yf_data.get('peg_ratio')
        valuation.current_pe = yf_data.get('trailing_pe')
        
        if valuation.forward_pe:
            valuation.forward_pe_signal = valuation.forward_pe < self.FORWARD_PE_THRESHOLD
            print(f"      Forward PE: {valuation.forward_pe:.1f}x (Threshold: <{self.FORWARD_PE_THRESHOLD}x) -> {'BUY SIGNAL' if valuation.forward_pe_signal else 'No signal'}")
        else:
            print("      Forward PE: N/A")
        
        # ========== 2. PEG Safety Net ==========
        print("    - Checking PEG Ratio...")
        if valuation.peg_ratio:
            valuation.peg_signal = valuation.peg_ratio < self.PEG_THRESHOLD
            print(f"      PEG Ratio: {valuation.peg_ratio:.2f} (Threshold: <{self.PEG_THRESHOLD}) -> {'BONUS SIGNAL' if valuation.peg_signal else 'No bonus'}")
        else:
            print("      PEG Ratio: N/A - falling back to Historical PE Z-Score")
            
            # ========== 3. Historical PE Z-Score (备选) ==========
            if self.fmp:
                print("    - Calculating Historical PE Z-Score...")
                z_score_data = self._calculate_pe_zscore(ticker)
                valuation.pe_5y_avg = z_score_data.get('avg')
                valuation.pe_5y_std = z_score_data.get('std')
                valuation.pe_z_score = z_score_data.get('z_score')
                
                if valuation.pe_z_score is not None:
                    valuation.historical_pe_signal = valuation.pe_z_score < self.PE_ZSCORE_THRESHOLD
                    print(f"      PE Z-Score: {valuation.pe_z_score:.2f} (5Y Avg: {valuation.pe_5y_avg:.1f}, Std: {valuation.pe_5y_std:.1f})")
                    print(f"      Result: {'HISTORICAL LOW' if valuation.historical_pe_signal else 'Normal range'}")
        
        # ========== 4. Kitchen Sink Check ==========
        # 注: 完整实现需要追踪财报日期和价格变动，这里简化处理
        print("    - Kitchen Sink check (simplified)...")
        valuation.kitchen_sink_signal = False  # 需要更多数据才能判断
        print("      Kitchen Sink: Requires earnings date tracking (skipped)")
        
        # ========== 5. 综合买入信号 ==========
        valuation.buy_signal_triggered = (
            valuation.forward_pe_signal or 
            valuation.peg_signal or 
            valuation.historical_pe_signal or
            valuation.kitchen_sink_signal
        )
        
        if valuation.buy_signal_triggered:
            signals = []
            if valuation.forward_pe_signal:
                signals.append(f"Forward PE {valuation.forward_pe:.1f}x")
            if valuation.peg_signal:
                signals.append(f"PEG {valuation.peg_ratio:.2f}")
            if valuation.historical_pe_signal:
                signals.append(f"PE Z-Score {valuation.pe_z_score:.2f}")
            print(f"    - ✓ BUY SIGNAL TRIGGERED: {', '.join(signals)}")
        else:
            print("    - No buy signal triggered")
        
        return valuation

    def _calculate_pe_zscore(self, ticker: str) -> dict:
        """
        计算历史 PE Z-Score
        
        公式: Z = (Current PE - 5yr Avg PE) / 5yr Std PE
        
        Returns:
            dict: {'avg': float, 'std': float, 'z_score': float}
        """
        result = {'avg': None, 'std': None, 'z_score': None}
        
        try:
            # 获取 5 年历史比率
            ratios = self.fmp.get_ratios(ticker, period='annual', limit=5)
            
            if not ratios or len(ratios) < 3:
                return result
            
            # 提取 PE 值
            pe_values = []
            for r in ratios:
                pe = r.get('priceEarningsRatio')
                if pe and pe > 0 and pe < 500:  # 过滤异常值
                    pe_values.append(pe)
            
            if len(pe_values) < 3:
                return result
            
            # 计算统计量
            avg = np.mean(pe_values)
            std = np.std(pe_values)
            
            # 获取当前 PE
            current_pe = self.yf.get_trailing_pe(ticker)
            if not current_pe:
                ratios_ttm = self.fmp.get_ratios_ttm(ticker)
                if ratios_ttm:
                    current_pe = ratios_ttm.get('peRatioTTM')
            
            if current_pe and std > 0:
                z_score = (current_pe - avg) / std
                result = {'avg': avg, 'std': std, 'z_score': z_score}
            
        except Exception as e:
            print(f"      [Warning] PE Z-Score calculation failed: {e}")
        
        return result

    # ========== Emergency Eject ==========

    def _check_emergency_eject(self, ticker: str, news: List[dict] = None) -> tuple[bool, str]:
        """
        V3.7 紧急弹射检测
        
        检查是否存在需要立即清仓的信号
        """
        if not news:
            return False, ""
        
        for article in news:
            title = (article.get('title', '') or '').lower()
            text = (article.get('text', '') or '').lower()
            content = title + ' ' + text
            
            for keyword in self.EMERGENCY_EJECT_KEYWORDS:
                if keyword.lower() in content:
                    return True, f"Emergency Signal: '{keyword}' detected in news"
        
        return False, ""

    # ========== V3.7 Final Judgment ==========

    def judge(self, data: CompanyData, news: List[dict] = None) -> TribunalDecision:
        """
        V3.7 最终审判
        
        综合所有 Phase 数据，输出 "Armored Sniper" 评级
        
        Args:
            data: 公司完整数据
            news: 最近的新闻列表
            
        Returns:
            TribunalDecision: 最终评级
        """
        print(f"    - [V3.7] CIO Tribunal is deliberating on {data.ticker}...")
        
        # ========== 1. 紧急弹射检测 ==========
        should_eject, eject_reason = self._check_emergency_eject(data.ticker, news)
        if should_eject:
            print(f"      ⚠️ EMERGENCY EJECT: {eject_reason}")
            return TribunalDecision(
                decision=Decision.TRAP,
                confidence=Confidence.HIGH,
                rationale=f"EMERGENCY EJECT: {eject_reason}. Immediate sell recommended.",
                growth_thesis_intact=False,
                valuation_fit=False,
                is_true_discount=False
            )
        
        # ========== 2. 构建 V3.7 决策上下文 ==========
        context = self._build_decision_context(data)
        context_str = json.dumps(context, indent=2, default=str)
        
        # ========== 3. V3.7 决策 Prompt ==========
        prompt = f"""
        You are the Chief Investment Officer (CIO) executing the Mahaney Growth Protocol (MGP) V3.7 "Armored Sniper".
        
        This Strategy is for $50B+ market cap industry winners facing TEMPORARY, FIXABLE bottlenecks (e.g., capacity constraints).
        
        Review the following data for {data.ticker} and render a Final Verdict.

        Data:
        {context_str}

        ### V3.7 Decision Logic Chain:

        1. **Pedigree Gate (V3.7)**:
           - Market Cap > $50B? Industry winner?
           - Sector not blacklisted?

        2. **Financial Forensics Gate (V3.7)**:
           - Inventory turnover stable (not crashing)?
           - Capex pulse positive (investing in capacity)?
           - Gross margin stable (<3% drop)?
           - High switching cost moat?

        3. **Financial Armor Gate (V3.7)**:
           - Gross Margin drop < 300bps?
           - Net Debt/EBITDA < 3.0x (or cash runway > 24mo)?
           - SBC dilution < 3%?

        4. **Valuation Gate (V3.7)**:
           - Forward PE < 20x? (Primary signal)
           - PEG < 0.6? (Bonus)
           - PE Z-Score < -1? (Historical low)

        5. **Catalyst Gate (V3.7)**:
           - Near-term catalyst within 12 months?
           - Keywords: Approval, Launch, Production start, Facility open

        ### V3.7 Final Rating Categories:

        - **TACTICAL SNIPER** (⚔️):
            - All gates passed + Forward PE < 20x + Near-term catalyst
            - "Heavy position for repair trade, target 6-12 months"

        - **STRATEGIC COMPOUNDER** (🏰):
            - All gates passed + High moat strength + May not have catalyst yet
            - "Core position, hold through volatility"

        - **CONVICTION BUY**:
            - Most gates passed + Good valuation + Some catalyst
            - "Standard buy signal"

        - **ACCUMULATE**:
            - Gates passed but valuation not at ideal entry
            - "Build position on dips"

        - **WATCH**:
            - Some concerns but fundamentals intact
            - "Monitor for better entry"

        - **TRAP** (💣):
            - Failed Financial Forensics (inventory crash, margin collapse)
            - OR Failed Financial Armor (debt too high, excessive dilution)
            - "Do not buy - not a good bottleneck"

        - **SKIP**:
            - Failed Pedigree (market cap, sector blacklist)
            - "Does not fit V3.7 criteria"

        ### Output Requirement:
        Provide a structured JSON response with:
        - decision: One of "TACTICAL SNIPER", "STRATEGIC COMPOUNDER", "CONVICTION BUY", "ACCUMULATE", "WATCH", "TRAP", "SKIP"
        - confidence: "High", "Medium", or "Low"
        - rationale: 2-3 sentences explaining which gates passed/failed and why this rating
        - growth_thesis_intact: boolean (is the core business thesis still valid?)
        - valuation_fit: boolean (is valuation attractive for V3.7?)
        - is_true_discount: boolean (is this a temporary bottleneck, not permanent decline?)
        """

        system_prompt = "You are a hedge fund CIO executing MGP V3.7 Armored Sniper. Focus on identifying TRUE temporary bottlenecks in industry winners, not value traps."

        result = self.llm.extract_structured_data(prompt, TribunalDecision, system_prompt=system_prompt)

        if not result:
            print(f"      [Error] Tribunal failed for {data.ticker}. Falling back to WATCH.")
            return TribunalDecision(
                decision=Decision.WATCH,
                confidence=Confidence.LOW,
                rationale="AI Analysis Failed - Manual review required",
                growth_thesis_intact=False,
                valuation_fit=False,
                is_true_discount=False
            )

        print(f"      Decision: {result.decision.value} | Confidence: {result.confidence.value}")
        print(f"      Rationale: {result.rationale[:150]}...")
        return result

    def _build_decision_context(self, data: CompanyData) -> dict:
        """构建 V3.7 决策上下文"""
        context = {
            "ticker": data.ticker,
            "company_name": data.company_name,
            "market_cap_b": data.market_cap / 1e9 if data.market_cap else None,
            
            # Pedigree (V3.7)
            "pedigree": None,
            
            # Financial Forensics (V3.7)
            "forensics": None,
            
            # Financial Armor (V3.7)
            "armor": None,
            
            # Valuation (V3.7)
            "valuation": None,
            
            # Catalysts (V3.7)
            "catalysts": None,
            
            # Legacy context
            "business_model": None,
            "moat_strength": None,
        }
        
        # Pedigree
        if data.gatekeeper and data.gatekeeper.pedigree:
            p = data.gatekeeper.pedigree
            context["pedigree"] = {
                "market_cap_passed": p.market_cap_passed,
                "sector_passed": p.sector_passed,
                "sector": p.sector,
                "industry": p.industry,
                "revenue_cagr_10y": f"{p.revenue_cagr_10y:.1%}" if p.revenue_cagr_10y else None,
                "is_winner": p.is_industry_winner,
                "passed": p.passed,
            }
        
        # Forensics
        if data.identifier and data.identifier.forensics:
            f = data.identifier.forensics
            context["forensics"] = {
                "inventory_check_passed": f.inventory_check_passed,
                "capex_pulse_positive": f.capex_pulse_positive,
                "pricing_power_intact": f.pricing_power_intact,
                "moat_strength": f.moat_strength.value,
                "passed": f.passed,
            }
            context["moat_strength"] = f.moat_strength.value
        
        # Armor
        if data.iron_gate:
            a = data.iron_gate
            context["armor"] = {
                "gross_margin_safe": a.gross_margin_safe,
                "gm_change_bps": a.gross_margin_yoy_change_bps,
                "debt_safe": a.debt_safe,
                "net_debt_to_ebitda": a.net_debt_to_ebitda,
                "dilution_safe": a.dilution_safe,
                "sbc_dilution_rate": f"{a.sbc_dilution_rate:.1%}" if a.sbc_dilution_rate else None,
                "passed": a.passed,
            }
        
        # Valuation
        if data.valuation:
            v = data.valuation
            context["valuation"] = {
                "forward_pe": v.forward_pe,
                "forward_pe_signal": v.forward_pe_signal,
                "peg_ratio": v.peg_ratio,
                "peg_signal": v.peg_signal,
                "pe_z_score": v.pe_z_score,
                "historical_pe_signal": v.historical_pe_signal,
                "buy_signal_triggered": v.buy_signal_triggered,
            }
        
        # Catalysts
        if data.intelligence and data.intelligence.catalysts:
            c = data.intelligence.catalysts
            context["catalysts"] = {
                "keywords_found": c.catalyst_keywords_found,
                "within_12m": c.catalyst_within_12m,
                "upcoming_events": c.upcoming_events[:3] if c.upcoming_events else [],
            }
        
        # Constraints
        if data.intelligence and data.intelligence.constraints:
            context["constraints"] = {
                "has_near_term_catalyst": data.intelligence.constraints.has_near_term_catalyst,
                "timeline_acceptable": data.intelligence.constraints.timeline_acceptable,
            }
        
        # Business Model
        if data.identifier:
            context["business_model"] = data.identifier.business_model.value
        
        return context
