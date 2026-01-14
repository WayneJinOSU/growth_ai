from core.data_models import CompanyData, TribunalDecision, Decision, Confidence
from tools.llm import LLMClient
import json


class Tribunal:
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def judge(self, data: CompanyData) -> TribunalDecision:
        # Construct a comprehensive context for the Judge
        context = {
            "ticker": data.ticker,
            "iron_gate": data.iron_gate.model_dump() if data.iron_gate else "Skipped/Failed",
            "business_model": data.identifier.business_model if data.identifier else "Unknown",
            "kpis": data.intelligence.kpi_values if data.intelligence else {},
            "management": data.intelligence.management_integrity if data.intelligence else "Unknown",
            "moat": data.intelligence.product_moat if data.intelligence else "Unknown",
            "insider": data.intelligence.insider_activity if data.intelligence else "Unknown",
            "dislocation": data.intelligence.dislocation_context if data.intelligence else "Unknown",
            "blue_sky": data.intelligence.blue_sky.model_dump() if data.intelligence and data.intelligence.blue_sky else "Unknown",
            "catalysts": data.intelligence.catalysts.model_dump() if data.intelligence and data.intelligence.catalysts else "Unknown"
        }

        context_str = json.dumps(context, indent=2)

        prompt = f"""
        You are the Chief Investment Officer (CIO) executing the Mahaney Growth Protocol (MGP) V3.2.
        
        This Strategy V3.2 emphasizes "Asymmetric Returns":
        1. Downside protected by Valuation & Hygiene.
        2. Upside driven by "Blue Sky" (Option Value).
        3. Ignited by "Catalysts".

        Review the following data for {data.ticker} and render a Final Verdict.

        Data:
        {context_str}

        ### Decision Logic Tree (V3.2):

        1. **Hygiene Check (Iron Gate & Dilution Shield)**:
           - Is Revenue Growth intact (>20% or high)? 
           - Is Dilution/SBC under control? (SBC/Rev < 20%)
           - If Hygiene Fails -> **AVOID/SELL**.

        2. **Valuation Check**:
           - PEG < 1.0 (Cheap) or < 1.5 (Reasonable)?
           - Or if "Blue Sky" is massive, is PEG < 2.0 acceptable?

        3. **Alpha / Option Value Check**:
           - Is there a "Second Curve" (R&D Effectiveness)?
           - Is there "TAM Expansion" capability?
           
        4. **Timing / Catalyst Check**:
           - Are there upcoming events (Earnings, Investor Day) and Variant Perception?

        ### Final Rating Categories:

        - **CONVICTION BUY**:
            - Reasonable Valuation + High Option Value + Clear Catalyst.
            - "Rocket ready to launch."

        - **ACCUMULATE**:
            - Low/Reasonable Valuation + High Option Value. But NO near-term catalyst.
            - "Long-term winner, wait for wind."

        - **SPECULATIVE BUY**:
            - High Valuation (PEG > 2) but Massive Option Value + Strong Catalyst.
            - "Expensive but explosive."

        - **VALUE TRAP**:
            - Low Valuation but NO Option Value (Old tech) and NO Catalyst.
            - "Cheap for a reason."

        - **WATCH**:
            - Fundamentals okay but waiting for better price or clarity.
            
        - **SELL**:
            - Broken thesis, high dilution, or deteriorating fundamentals.

        ### Output Requirement:
        Provide a structured JSON response with:
        - decision: Enum value ("CONVICTION BUY", "ACCUMULATE", "SPECULATIVE BUY", "VALUE_TRAP", "WATCH", "SELL")
        - confidence: "High", "Medium", or "Low"
        - rationale: A concise explanation focusing on the V3.2 logic.
        - growth_thesis_intact: boolean
        - valuation_fit: boolean
        - is_true_discount: boolean
        """

        result = self.llm.extract_structured_data(prompt, TribunalDecision,
                                                  system_prompt="You are a VC-minded public market investor (MGP V3.2).")

        if not result:
            # Fallback
            return TribunalDecision(
                decision=Decision.WATCH,
                confidence=Confidence.LOW,
                rationale="AI Analysis Failed",
                growth_thesis_intact=False,
                valuation_fit=False,
                is_true_discount=False
            )

        return result

