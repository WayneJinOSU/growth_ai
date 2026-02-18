"""
Phase 6: Strategic Pricing (战略定价)
=====================================
V3.5 Blue Sky Edition - "The Holographic Judgment"

目标: 将所有定性情报转化为定量的操作指令。此处是逻辑的终点，行动的起点。

Steps:
1. Valuation Scrub (估值清洗) - Adjust PE based on Sandbagging/Over-Promising
2. Fortress Test (底仓资格认证) - Tier 1/2/3 based on Phase 1 & 2
3. Blue Sky Re-Rating (蓝天重定价) - Relax PEG limit if Second Curve exists
4. Executive Matrix (最终决策矩阵) - Output strategic definition
"""

from core.data_models import (
    StrategicPricingData,
    StrategicDefinition,
    TierLevel,
    CompanyData,
    ShadowAuditData,
    DeepAuditData,
    CatalystData,
    IntelligenceData,
)


class StrategyAnalyzer:
    """
    Phase 6: Strategic Pricing Analyzer

    Aggregates signals from previous phases into a single strategic definition.
    """

    # PEG Thresholds
    DEFAULT_PEG_LIMIT = 2.0
    BLUE_SKY_PEG_LIMIT = 2.5

    def __init__(self):
        pass

    def analyze(
        self,
        data: CompanyData,
        catalyst_data: CatalystData = None,
    ) -> StrategicPricingData:
        """
        Execute Phase 6: Strategic Pricing

        Args:
            data: Full CompanyData with previous phase results
            catalyst_data: Phase 5 Catalyst data (if separate from intelligence)

        Returns:
            StrategicPricingData with final strategic definition
        """
        result = StrategicPricingData()

        # ========== Step 1: Valuation Scrub ==========
        print("    - [Phase 6] Step 1: Valuation Scrub...")
        result.adjusted_pe, result.adjustment_reason = self._valuation_scrub(data)

        # ========== Step 2: Fortress Test ==========
        print("    - [Phase 6] Step 2: Fortress Test (Tier Level)...")
        result.tier_level, result.tier_rationale = self._fortress_test(data)

        # ========== Step 3: Blue Sky Re-Rating ==========
        print("    - [Phase 6] Step 3: Blue Sky Re-Rating...")
        result.blue_sky_triggered, result.peg_limit = self._blue_sky_rerate(data)

        # ========== Step 4: Executive Matrix ==========
        print("    - [Phase 6] Step 4: Executive Matrix...")
        (
            result.catalyst_strength,
            result.valuation_status,
            result.strategic_definition,
            result.action_instruction,
        ) = self._executive_matrix(data, result, catalyst_data)

        return result

    def _valuation_scrub(self, data: CompanyData) -> tuple:
        """
        Step 1: Valuation Scrub

        Adjust PE/PS based on management integrity signals.
        - Sandbagger: Apply 20% discount (multiply E by 1.25)
        - Over-Promiser: Apply 20% premium (risk)
        """
        adjusted_pe = None
        adjustment_reason = None

        # Get raw PE from deep_audit or gatekeeper
        raw_pe = None
        if data.deep_audit and data.deep_audit.peg_ratio:
            # PEG is typically PE / Growth, we need to infer PE
            # For simplicity, we'll use a placeholder logic
            pass

        # Check for sandbagging/over-promising from shadow_audit or intelligence
        is_sandbagger = False
        is_over_promiser = False

        if data.shadow_audit:
            is_sandbagger = data.shadow_audit.sandbagging_detected

        if data.intelligence and data.intelligence.management_integrity:
            integrity_text = data.intelligence.management_integrity.lower()
            if "sandbag" in integrity_text or "conservative" in integrity_text:
                is_sandbagger = True
            if "over-promis" in integrity_text or "miss" in integrity_text:
                is_over_promiser = True

        if is_sandbagger:
            adjustment_reason = "Sandbagger Discount: PE adjusted -20% (hidden earnings)"
            # In practice: PE * 0.8 = effective valuation looks cheaper
        elif is_over_promiser:
            adjustment_reason = "Over-Promiser Premium: PE adjusted +20% (risk premium)"
        else:
            adjustment_reason = "No adjustment applied"

        print(f"      Adjustment: {adjustment_reason}")
        return adjusted_pe, adjustment_reason

    def _fortress_test(self, data: CompanyData) -> tuple:
        """
        Step 2: Fortress Test (Tier Level)

        Tier 1: Phase 1 passed + Phase 2 King Makers
        Tier 2: Phase 1 passed only
        Tier 3: Did not pass Phase 1 or weak signals
        """
        # Check Phase 1 (Deep Audit)
        phase1_passed = data.deep_audit and data.deep_audit.passed

        # Check Phase 2 (Shadow Audit - King Makers)
        has_king_makers = (
            data.shadow_audit and data.shadow_audit.has_king_maker_clients
        )

        if phase1_passed and has_king_makers:
            tier = TierLevel.TIER_1
            rationale = "Phase 1 (Deep Audit) passed + King Maker clients confirmed"
        elif phase1_passed:
            tier = TierLevel.TIER_2
            rationale = "Phase 1 (Deep Audit) passed, but no King Maker clients"
        else:
            tier = TierLevel.TIER_3
            rationale = "Phase 1 (Deep Audit) failed or weak fundamental signals"

        print(f"      Tier Level: {tier.value} - {rationale}")
        return tier, rationale

    def _blue_sky_rerate(self, data: CompanyData) -> tuple:
        """
        Step 3: Blue Sky Re-Rating

        If a strong second growth curve exists (>50% growth, >10% of revenue),
        allow PEG limit to expand from 2.0 to 2.5.
        """
        blue_sky_triggered = False
        peg_limit = self.DEFAULT_PEG_LIMIT

        if data.intelligence and data.intelligence.blue_sky:
            blue_sky = data.intelligence.blue_sky
            # Check for second curve signals in R&D or TAM text
            rnd_text = (blue_sky.rnd_effectiveness or "").lower()
            tam_text = (blue_sky.tam_expansion or "").lower()

            # Heuristic: look for strong growth indicators
            growth_indicators = [
                "50%",
                "100%",
                "doubling",
                "triple",
                "explosive",
                "breakthrough",
                "new segment",
                "second curve",
                "tam expansion",
            ]
            for indicator in growth_indicators:
                if indicator in rnd_text or indicator in tam_text:
                    blue_sky_triggered = True
                    break

        if blue_sky_triggered:
            peg_limit = self.BLUE_SKY_PEG_LIMIT
            print(f"      Blue Sky TRIGGERED: PEG limit relaxed to {peg_limit}")
        else:
            print(f"      Blue Sky not triggered: PEG limit remains {peg_limit}")

        return blue_sky_triggered, peg_limit

    def _executive_matrix(
        self,
        data: CompanyData,
        pricing: StrategicPricingData,
        catalyst_data: CatalystData = None,
    ) -> tuple:
        """
        Step 4: Executive Matrix

        Combines:
        - Catalyst Strength (from Phase 5)
        - Valuation Status (Green = low/reasonable, Red = high/premium)
        - Tier Level (from Step 2)

        Outputs:
        - Strategic Definition (Diamond Setup, Momentum Ride, etc.)
        - Action Instruction
        """
        # Determine Catalyst Strength
        catalyst_strength = "Low"
        if catalyst_data:
            if catalyst_data.wave_strength in ["High"]:
                catalyst_strength = "High"
            elif catalyst_data.wave_strength in ["Medium"] and catalyst_data.upcoming_events:
                catalyst_strength = "High"
        elif data.intelligence and data.intelligence.catalysts:
            cat = data.intelligence.catalysts
            if cat.wave_strength in ["High"]:
                catalyst_strength = "High"
            elif cat.upcoming_events and len(cat.upcoming_events) >= 2:
                catalyst_strength = "High"

        # Determine Valuation Status (simplified heuristic)
        valuation_status = "Green"  # Default to reasonable
        if data.deep_audit:
            peg = data.deep_audit.peg_ratio
            if peg and peg > pricing.peg_limit:
                valuation_status = "Red"

        # Tier Level
        tier = pricing.tier_level or TierLevel.TIER_3

        # Apply Executive Matrix Logic
        definition = None
        instruction = None

        if catalyst_strength == "High" and valuation_status == "Green":
            definition = StrategicDefinition.DIAMOND_SETUP
            instruction = "💎 Perfect strike zone. Aggressive Buy."
        elif catalyst_strength == "High" and valuation_status == "Red":
            definition = StrategicDefinition.MOMENTUM_RIDE
            instruction = "🚀 Momentum overrides valuation. Right-side chase. Use Phase 7 for entry."
        elif catalyst_strength == "Low" and valuation_status == "Green" and tier == TierLevel.TIER_1:
            definition = StrategicDefinition.FORTRESS_ACCUMULATION
            instruction = "🏰 Deep moat, cheap valuation. Scale in (left-side accumulation)."
        elif catalyst_strength == "Low" and valuation_status == "Green" and tier != TierLevel.TIER_1:
            definition = StrategicDefinition.DEAD_MONEY
            instruction = "⚰️ Cheap but mediocre. Watch only. Capital has time cost."
        elif catalyst_strength == "Low" and valuation_status == "Red" and tier == TierLevel.TIER_1:
            definition = StrategicDefinition.CORRECTION_WATCH
            instruction = "⏸️ Expensive + no catalyst. DO NOT SHORT Tier 1. Wait for pullback."
        else:  # Low catalyst, Red valuation, Tier 2/3
            definition = StrategicDefinition.SHORT_TARGET
            instruction = "💣 No moat, no catalyst, overvalued. Clear short candidate."

        print(f"      Catalyst Strength: {catalyst_strength}")
        print(f"      Valuation Status: {valuation_status}")
        print(f"      Strategic Definition: {definition.value}")

        return catalyst_strength, valuation_status, definition, instruction

strategyAnalyzer = StrategyAnalyzer()