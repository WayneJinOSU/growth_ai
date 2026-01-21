"""
Phase 6: The Final Tribunal (最终审判) - V3.5 Singularity
=========================================================
下单前的最后 60 秒核对清单。

设计原则:
- 决策逻辑: 纯 Python 规则 (基于前面阶段的 Gates 状态)
- LLM 职责: 只生成 rationale (Executive Summary)
"""

from core.data_models import CompanyData, Decision, TribunalDecision, Confidence
from tools.llm import LLMClient


class Tribunal:
    """
    最终法庭：MGP V3.5 策略的决策核心
    """

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def judge(self, data: CompanyData) -> TribunalDecision:
        print(f"  [Phase 6] The Final Tribunal for {data.ticker} (V3.5)...")
        
        # ========== 1. 提取 Gates 状态 (已在前面阶段计算完成) ==========
        gate_gatekeeper = data.gatekeeper and data.gatekeeper.passed
        gate_audit = data.deep_audit and data.deep_audit.passed
        gate_shadow = not (data.shadow_audit and data.shadow_audit.is_fake_tech)
        
        has_king_maker = data.shadow_audit and data.shadow_audit.has_king_maker_clients
        organic_growth = data.shadow_audit and data.shadow_audit.organic_growth_confirmed
        is_sandbagging = data.shadow_audit and data.shadow_audit.sandbagging_detected
        
        is_ignition = data.physics and data.physics.is_ignition
        is_accumulation = data.physics and data.physics.is_accumulation
        is_broken_trend = data.physics and data.physics.is_broken_trend
        
        has_catalyst = (data.intelligence and data.intelligence.catalysts and 
                        len(data.intelligence.catalysts.upcoming_events) > 0)

        # ========== 2. 规则化决策 (Decision Matrix) ==========
        decision = Decision.WATCH
        confidence = Confidence.MEDIUM
        
        # TRAP: 硬性否决条件
        if not gate_shadow:  # Fake Tech
            decision = Decision.TRAP
            confidence = Confidence.HIGH
        elif is_broken_trend:  # Physics 破位
            decision = Decision.TRAP
            confidence = Confidence.HIGH
        elif data.deep_audit and "CFO Divergence" in (data.deep_audit.fail_reason or ""):
            decision = Decision.TRAP
            confidence = Confidence.HIGH
            
        # FIRE: 全部通过 + Ignition + 催化剂
        elif gate_gatekeeper and gate_audit and gate_shadow and is_ignition and has_catalyst:
            decision = Decision.FIRE
            confidence = Confidence.HIGH
            
        # STRATEGIC COMPOUNDER: 基本面强 + King Maker + 长期持有
        elif gate_gatekeeper and gate_audit and has_king_maker and not is_broken_trend:
            decision = Decision.STRATEGIC_COMPOUNDER
            confidence = Confidence.MEDIUM
            
        # TACTICAL SNIPER: 审计通过 + (Sandbagging OR Organic Growth)
        elif gate_audit and (is_sandbagging or organic_growth):
            decision = Decision.TACTICAL_SNIPER
            confidence = Confidence.HIGH if is_sandbagging else Confidence.MEDIUM
            
        # ACCUMULATE: 基本面好 + Accumulation (吸筹) 但无 Ignition
        elif gate_gatekeeper and gate_audit and is_accumulation and not is_ignition:
            decision = Decision.ACCUMULATE
            confidence = Confidence.MEDIUM
            
        # WATCH: 其他情况
        else:
            decision = Decision.WATCH
            confidence = Confidence.LOW

        # ========== 3. LLM 生成 Rationale (轻量) ==========
        rationale = self._generate_rationale(data, decision)

        print(f"    Decision: {decision.value} | Confidence: {confidence.value}")
        
        return TribunalDecision(
            decision=decision,
            confidence=confidence,
            rationale=rationale,
            growth_thesis_intact=gate_gatekeeper and gate_audit,
            valuation_fit=gate_audit,
            is_true_discount=not is_broken_trend
        )

    def _generate_rationale(self, data: CompanyData, decision: Decision) -> str:
        """
        用 LLM 生成简洁的 Executive Summary (只生成文字，不做决策)
        """
        # 构建精简的上下文
        context = f"""
        Ticker: {data.ticker}
        Decision: {decision.value}
        
        Key Facts:
        - Gatekeeper: {'Passed' if data.gatekeeper and data.gatekeeper.passed else 'Failed'}
        - Deep Audit: {'Passed' if data.deep_audit and data.deep_audit.passed else 'Failed'}
        - King Makers: {'Yes' if data.shadow_audit and data.shadow_audit.has_king_maker_clients else 'No'}
        - Organic Growth: {'Confirmed' if data.shadow_audit and data.shadow_audit.organic_growth_confirmed else 'No'}
        - Sandbagging: {'Detected (Bullish)' if data.shadow_audit and data.shadow_audit.sandbagging_detected else 'No'}
        - Ignition: {'Yes' if data.physics and data.physics.is_ignition else 'No'}
        - Broken Trend: {'Yes' if data.physics and data.physics.is_broken_trend else 'No'}
        """
        
        prompt = f"""
        Write a 2-3 sentence Executive Summary explaining the investment decision for {data.ticker}.
        
        {context}
        
        Be direct. No intro phrases. Start with the key insight.
        """
        
        try:
            rationale = self.llm.analyze_text(prompt, system_prompt="You are a hedge fund analyst writing a brief summary.")
            return rationale.strip()[:500]
        except:
            return f"{decision.value} decision based on MGP V3.5 gates analysis."
