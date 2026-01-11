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
            "dislocation": data.intelligence.dislocation_context if data.intelligence else "Unknown"
        }

        context_str = json.dumps(context, indent=2)

        prompt = f"""
        You are the Chief Investment Officer (CIO) executing the Mahaney Growth Protocol (MGP) V3.0.

        Review the following data for {data.ticker} and render a Final Verdict.

        Data:
        {context_str}

        ### Decision Logic (The Tribunal):

        1. **Growth Thesis Check**:
           - Is Revenue Growth (>20%) and specific KPIs (e.g. NDR, GMV) still strong?
           - If Growth < 20% AND KPIs slowing -> SELL/AVOID.
           - If Revenue slowing but KPIs strong -> Proceed to Valuation.

        2. **Valuation Fit**:
           - PEG < 1.0 (and healthy model) -> STRONG BUY.
           - PEG 1.0 - 1.5 -> BUY.
           - PEG > 2.0 -> HOLD/WATCH (unless absolute monopoly growing >40%).

        3. **Dislocation Check**:
           - Is the price drop a "True Discount" (Macro/Sentiment) or "Fake Discount" (Broken Thesis)?
           - If "True Discount" -> Upgrade confidence.
           - If "Fake Discount" -> Downgrade to AVOID/SELL.

        ### Output Requirement:
        Provide a structured JSON response with:
        - decision: "STRONG BUY", "BUY", "HOLD", "SELL", or "WATCH"
        - confidence: "High", "Medium", or "Low"
        - rationale: A concise 2-3 sentence explanation.
        - growth_thesis_intact: boolean
        - valuation_fit: boolean
        - is_true_discount: boolean
        """

        result = self.llm.extract_structured_data(prompt, TribunalDecision,
                                                  system_prompt="You are a disciplined growth investor.")

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

