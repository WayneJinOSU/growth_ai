from tools.llm import LLMClient
from core.data_models import IdentifierData, BusinessModel
from typing import List


class Identifier:
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def identify(self, ticker: str, company_description: str) -> IdentifierData:
        prompt = f"""
        Analyze the company {ticker} based on this description: {company_description}

        Classify it into one of these business models:
        - SaaS (Subscription, Cloud Software)
        - Consumption (Usage-based, Cloud Infrastructure)
        - Marketplace (Two-sided platform, Gig Economy)
        - Advertising (Ad-driven, Social Media)
        - Hardware (Physical devices)
        - Other

        Then, list 3 specific idiosyncratic KPIs (Key Performance Indicators) that are critical for this specific business model.
        Examples:
        - SaaS: NDR (Net Dollar Retention), RPO (Remaining Performance Obligations), ARR
        - Consumption: Net Revenue Retention, Usage Growth
        - Marketplace: GMV, Take Rate
        - Advertising: DAU/MAU, ARPPU, CPM/CPC

        Also identify the "Bear Case Hook" - the most likely reason this company would fail or is failing.
        """

        system_prompt = "You are a senior equity research analyst specializing in growth stocks."

        result = self.llm.extract_structured_data(prompt, IdentifierData, system_prompt)

        if not result:
            # Fallback
            return IdentifierData(business_model=BusinessModel.OTHER, specific_kpis=["Revenue Growth"],
                                  bear_case_hook="Unknown")

        return result

