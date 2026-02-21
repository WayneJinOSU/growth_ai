"""
Phase 8: The Final Tribunal (最终审判) - V3.5 Blue Sky Edition
=========================================================
下单前的最后 60 秒核对清单。

核对项目:
[ ] 风险熔断: VIX < 30? 美债收益率稳定?
[ ] 审计通过: 核心指标健康? 没有内幕大额抛售?
[ ] 蓝天确认: 有第二增长曲线或 TAM 扩张的故事?
[ ] 战略匹配: 是 Tier 1/2 护城河? 估值有没有透支未来?
[ ] 势能共振: 是否处于全行业不可逆的爆发潮中?
[ ] 物理点火: Ignition 信号出现了吗?

结果:
- 全部 YES => FIRE (全仓开火)
- 缺物理点火 => WATCH (加入自选，设置警报)
- 审计/战略 FAIL => TRASH (永远剔除)
"""

from core.data_models import (
    CompanyData, Decision, TribunalDecision, Confidence,
    StrategicPricingData, StrategicDefinition, TierLevel, GatekeeperData
)
from tools.llm import LLMClient


class Tribunal:
    """
    最终法庭：MGP V3.5 策略的决策核心
    """

    def __init__(self, llm_client=None, deep_client=None):
        from tools.deep_search import DeepSearchClient
        self.llm = llm_client or LLMClient()
        self.deep = deep_client or DeepSearchClient()

    def judge(self, data: CompanyData) -> TribunalDecision:
        print(f"  [Phase 8] The Final Tribunal for {data.ticker} (V3.5 Blue Sky)...")
        
        strategic_pricing = data.strategic_pricing
        
        # ========== 60-Second Checklist ==========
        checklist = {}
        
        # 1. Risk Fuse (风险熔断)
        checklist['risk_fuse'] = self._check_risk_fuse(data)
        
        # 2. Audit Passed (审计通过)
        checklist['audit_passed'] = self._check_audit_passed(data)
        
        # 3. Blue Sky Confirmed (蓝天确认)
        checklist['blue_sky'] = self._check_blue_sky(data, strategic_pricing)
        
        # 4. Strategic Match (战略匹配)
        checklist['strategic_match'] = self._check_strategic_match(data, strategic_pricing)
        
        # 5. Wave Resonance (势能共振)
        checklist['wave_resonance'] = self._check_wave_resonance(data)
        
        # 6. Physical Ignition (物理点火)
        checklist['physical_ignition'] = data.physics and data.physics.is_ignition
                # ========== Decision Logic ==========
        decision = Decision.WATCH
        confidence = Confidence.MEDIUM
        
        # Count passes
        passes = sum(1 for v in checklist.values() if v)
        total = len(checklist)
        
        print(f"    Checklist: {passes}/{total} passed")
        for k, v in checklist.items():
            status = "✅" if v else "❌"
            print(f"      [{status}] {k}")
        
        # TRASH: Audit or Strategic fails hard
        if not checklist['audit_passed']:
            decision = Decision.TRAP
            confidence = Confidence.HIGH
        elif data.physics and data.physics.is_broken_trend:
            # V3.5: Fortress Accumulation Exemption with VIX Safety Catch
            is_fortress = (strategic_pricing and 
                          strategic_pricing.strategic_definition == StrategicDefinition.FORTRESS_ACCUMULATION)
            is_true_discount = self._parse_true_discount(data)
            vix_safe = data.gatekeeper and (data.gatekeeper.vix_value is None or data.gatekeeper.vix_value < 30)
            
            if is_fortress and is_true_discount and vix_safe:
                # Override TRAP -> ACCUMULATE (Left-side buying opportunity)
                decision = Decision.ACCUMULATE
                confidence = Confidence.MEDIUM
                print("      🏰 FORTRESS EXEMPTION ACTIVATED: Broken trend overridden (True Discount + VIX Safe)")
            elif is_fortress and is_true_discount and not vix_safe:
                # VIX > 30: Too dangerous, downgrade to WATCH
                decision = Decision.WATCH
                confidence = Confidence.LOW
                print("      ⚠️ FORTRESS BLOCKED: True Discount but VIX > 30 (Catching falling knives)")
            else:
                decision = Decision.TRAP
                confidence = Confidence.HIGH
        # FIRE: All checks pass
        elif all(checklist.values()):
            decision = Decision.FIRE
            confidence = Confidence.HIGH
        # Integrate with Strategic Pricing if available
        elif strategic_pricing and strategic_pricing.strategic_definition:
            sd = strategic_pricing.strategic_definition
            if sd == StrategicDefinition.DIAMOND_SETUP:
                decision = Decision.CONVICTION_BUY
                confidence = Confidence.HIGH
            elif sd == StrategicDefinition.MOMENTUM_RIDE:
                decision = Decision.SPECULATIVE_BUY
                confidence = Confidence.MEDIUM
            elif sd == StrategicDefinition.FORTRESS_ACCUMULATION:
                decision = Decision.ACCUMULATE
                confidence = Confidence.MEDIUM
            elif sd == StrategicDefinition.DEAD_MONEY:
                decision = Decision.WATCH
                confidence = Confidence.LOW
            elif sd == StrategicDefinition.CORRECTION_WATCH:
                decision = Decision.WATCH
                confidence = Confidence.MEDIUM
            elif sd == StrategicDefinition.SHORT_TARGET:
                decision = Decision.TRAP
                confidence = Confidence.HIGH
        # Legacy: accumulation without ignition
        elif checklist['audit_passed'] and data.physics and data.physics.is_accumulation:
            decision = Decision.ACCUMULATE
            confidence = Confidence.MEDIUM
        # Default
        else:
            decision = Decision.WATCH
            confidence = Confidence.LOW

        # TODO: 红蓝对抗 (Adversarial Review) — 暂未启用，待设计完善后开放
        # if deep_search and decision in [Decision.FIRE, Decision.ACCUMULATE]:
        #     print(f"    [Deep Search] Running Adversarial Review (Red Team)...")
        #     bullish_thesis = f"Decision: {decision.value}. Growth: {checklist.get('growth_thesis_intact')}. Val: {checklist.get('valuation_fit')}."
        #     adv_res = self.deep.adversarial_review(data.ticker, bullish_thesis)
        #
        #     if not adv_res['passed']:
        #         print(f"    🚩 ADVERSARIAL REVIEW FAILED! Found {len(adv_res['red_flags'])} red flags.")
        #         for flag in adv_res['red_flags']:
        #             print(f"       - {flag[:100]}...")
        #
        #         decision = Decision.WATCH
        #         confidence = Confidence.LOW
        #         checklist['adversarial_passed'] = False
        #         data.tribunal_notes = f"Adversarial Review FAILED: {'; '.join([f[:50] for f in adv_res['red_flags']])}"
        #     else:
        #         print(f"    ✅ Adversarial Review PASSED. Thesis holds.")
        #         checklist['adversarial_passed'] = True

        # ========== LLM Rationale ==========
        rationale = self._generate_rationale(data, decision, checklist, strategic_pricing)

        print(f"    Decision: {decision.value} | Confidence: {confidence.value}")
        
        return TribunalDecision(
            decision=decision,
            confidence=confidence,
            rationale=rationale,
            checklist_results=checklist,
            growth_thesis_intact=checklist['audit_passed'] and checklist['blue_sky'],
            valuation_fit=checklist['strategic_match'],
            is_true_discount=self._parse_true_discount(data)
        )

    def _check_risk_fuse(self, data: CompanyData) -> bool:
        """Check VIX < 30 and macro stability"""
        if data.gatekeeper:
            vix_ok = data.gatekeeper.vix_value is None or data.gatekeeper.vix_value < 30
            return vix_ok
        return True

    def _check_audit_passed(self, data: CompanyData) -> bool:
        """V3.5: Check Phase 1 Deep Audit using red flag system (passed if red_flags < 2)"""
        audit_ok = data.deep_audit and data.deep_audit.passed
        return audit_ok

    def _parse_true_discount(self, data: CompanyData) -> bool:
        """V3.5: Parse [DISCOUNT_TYPE: TRUE_DISCOUNT] from Phase 3 Intelligence dislocation_context"""
        if data.intelligence and data.intelligence.dislocation_context:
            return "[DISCOUNT_TYPE: TRUE_DISCOUNT]" in data.intelligence.dislocation_context
        return False

    def _check_blue_sky(self, data: CompanyData, pricing: StrategicPricingData) -> bool:
        """Check for second growth curve or TAM expansion"""
        if pricing and pricing.blue_sky_triggered:
            return True
        if data.blue_sky_phase and data.blue_sky_phase.blue_sky:
            bs = data.blue_sky_phase.blue_sky
            rnd_valid = bs.rnd_effectiveness and bs.rnd_effectiveness.strip().upper() != "N/A"
            tam_valid = bs.tam_expansion and bs.tam_expansion.strip().upper() != "N/A"
            return bool(rnd_valid or tam_valid)
        return False

    def _check_strategic_match(self, data: CompanyData, pricing: StrategicPricingData) -> bool:
        """Check Tier 1/2 moat and valuation within Business Model safety margin (Green)"""
        if pricing:
            tier_ok = pricing.tier_level in [TierLevel.TIER_1, TierLevel.TIER_2]
            val_ok = pricing.valuation_status == "Green"  # 估值在所处 Business Model 的安全边际内
            return tier_ok or val_ok
        # Fallback: shadow audit king makers
        return data.shadow_audit and data.shadow_audit.has_king_maker_clients

    def _check_wave_resonance(self, data: CompanyData) -> bool:
        """Check if riding a thematic wave"""
        if data.catalysts:
            cat = data.catalysts
            return cat.wave_strength in ["High", "Medium"]
        return False

    def _generate_rationale(self, data: CompanyData, decision: Decision, 
                            checklist: dict = None, pricing: StrategicPricingData = None) -> str:
        """
        Generate Executive Summary using LLM
        """
        # Build context
        checklist_str = ""
        if checklist:
            checklist_str = "\n".join([f"- {k}: {'PASS' if v else 'FAIL'}" for k, v in checklist.items()])
        
        strategic_str = ""
        if pricing and pricing.strategic_definition:
            strategic_str = f"Strategic Definition: {pricing.strategic_definition.value}\nAction: {pricing.action_instruction}"

        context = f"""
        Ticker: {data.ticker}
        Decision: {decision.value}
        
        V3.5 Checklist:
        {checklist_str or "N/A"}
        
        {strategic_str}
        
        Key Facts:
        - Gatekeeper: {'Passed' if data.gatekeeper and data.gatekeeper.passed else 'Failed'}
        - Deep Audit: {'Passed' if data.deep_audit and data.deep_audit.passed else 'Failed'}
        - King Makers: {'Yes' if data.shadow_audit and data.shadow_audit.has_king_maker_clients else 'No'}
        - Ignition: {'Yes' if data.physics and data.physics.is_ignition else 'No'}
        - Broken Trend: {'Yes' if data.physics and data.physics.is_broken_trend else 'No'}
        """
        
        prompt = f"""
        Write a 3-4 sentence Executive Summary explaining the investment decision for {data.ticker}.
        
        {context}
        
        Requirements:
        1. Be direct. No intro phrases. Start with the key insight.
        2. CRITICAL: Include the timing context—why is this decision being made NOW? Mention specific upcoming events or recent price action/audit findings with their timeframes.
        3. Explain the expected duration or critical window for the thesis.
        """
        
        try:
            rationale = self.llm.analyze_text(prompt, system_prompt="You are a hedge fund analyst writing a brief summary.")
            return rationale.strip()[:500]
        except:
            return f"{decision.value} decision based on MGP V3.5 Blue Sky gates analysis."

tribunal = Tribunal()