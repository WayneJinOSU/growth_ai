"""
Phase 4: The Tribunal (最终审判) - V3.4 Upgrade
================================================
综合所有检查点，输出最终评级和战术指令。

V3.4 决策逻辑链:
1. 宏观关 - 10Y 美债是否炸裂？VIX > 30？
2. 行业关 - 是否在"白名单"内？
3. 卫生关 - 增长 >20%？无 SBC 陷阱？
4. 测谎关 - 现金流是否匹配利润？是否有核心技术人员离职？
5. 估值关 - 现价是否在宏观折价后的 Bear Case 区间？

V3.4 评级体系:
- TACTICAL_SNIPER: 基本面真沙袋 + 估值低 + 宏观环境允许
- STRATEGIC_COMPOUNDER: 技术独占窗口 > 3年 + 巨头客户背书 + 现金流健康
- TRAP: 看似高增长，但 CFO < NI，或核心技术大牛离职
"""

from typing import List, Optional
from core.data_models import (
    CompanyData, TribunalDecision, Decision, Confidence,
    GatekeeperData, ShadowAuditData, PolygraphData, MacroMode
)
from tools.llm import LLMClient
from tools.fmp import FMPClient
import json


class Tribunal:
    """
    最终审判：MGP V3.4 策略的终极决策引擎
    
    职责：
    - 综合 Gatekeeper、IronGate、ShadowAudit、Polygraph、Intelligence 数据
    - 执行紧急弹射检测
    - 输出 V3.4 标准的最终评级
    """
    
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

    def __init__(self, llm_client: LLMClient, fmp_client: FMPClient = None):
        self.llm = llm_client
        self.fmp = fmp_client

    def _check_emergency_eject(self, ticker: str, news: List[dict] = None) -> tuple[bool, str]:
        """
        V3.4 紧急弹射检测
        
        检查是否存在需要立即清仓的信号：
        - 核心高管（CTO/CFO/CEO）离职
        - 重大客户流失
        - 财务造假/SEC 调查
        
        Returns:
            (should_eject, reason): 是否应紧急弹射及原因
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

    def judge(self, data: CompanyData, news: List[dict] = None) -> TribunalDecision:
        """
        V3.4 最终审判
        
        Args:
            data: 公司完整数据 (含 Gatekeeper, IronGate, ShadowAudit, Polygraph, Intelligence)
            news: 最近的新闻列表 (用于紧急弹射检测)
            
        Returns:
            TribunalDecision: 最终评级和理由
        """
        print(f"    - [V3.4] CIO Tribunal is deliberating on {data.ticker}...")
        
        # ========== 1. 紧急弹射检测 ==========
        should_eject, eject_reason = self._check_emergency_eject(data.ticker, news)
        if should_eject:
            print(f"      ⚠️ EMERGENCY EJECT: {eject_reason}")
            return TribunalDecision(
                decision=Decision.TRAP,
                confidence=Confidence.HIGH,
                rationale=f"EMERGENCY EJECT: {eject_reason}. Immediate sell recommended regardless of valuation.",
                growth_thesis_intact=False,
                valuation_fit=False,
                is_true_discount=False
            )
        
        # ========== 2. 构建 V3.4 决策上下文 ==========
        context = {
            "ticker": data.ticker,
            "market_cap": data.market_cap,
            
            # Gatekeeper Data (V3.4)
            "gatekeeper": {
                "macro_mode": data.gatekeeper.macro_mode.value if data.gatekeeper else "Unknown",
                "us10y_yield": data.gatekeeper.us10y_yield if data.gatekeeper else None,
                "vix": data.gatekeeper.vix_value if data.gatekeeper else None,
                "sector_passed": data.gatekeeper.sector_check_passed if data.gatekeeper else True,
                "vix_panic": (data.gatekeeper.vix_value or 0) > 30 if data.gatekeeper else False,
            },
            
            # Iron Gate Data
            "iron_gate": data.iron_gate.model_dump() if data.iron_gate else "Skipped/Failed",
            
            # Shadow Audit Data (V3.4)
            "shadow_audit": {
                "is_fake_tech": data.shadow_audit.is_fake_tech if data.shadow_audit else False,
                "has_king_maker_clients": data.shadow_audit.has_king_maker_clients if data.shadow_audit else False,
                "linkedin_audit": data.shadow_audit.linkedin_hiring_audit[:200] if data.shadow_audit and data.shadow_audit.linkedin_hiring_audit else None,
                "customer_audit": data.shadow_audit.customer_quality_audit[:200] if data.shadow_audit and data.shadow_audit.customer_quality_audit else None,
            } if data.shadow_audit else "Not Available",
            
            # Polygraph Data (V3.4)
            "polygraph": {
                "cash_flow_check_passed": data.polygraph.cash_flow_divergence_check if data.polygraph else True,
                "sandbagging_detected": data.polygraph.sandbagging_detected if data.polygraph else False,
                "details": data.polygraph.details if data.polygraph else None,
            } if data.polygraph else "Not Available",
            
            # Business Model & KPIs
            "business_model": data.identifier.business_model.value if data.identifier else "Unknown",
            "kpis": data.intelligence.kpi_values if data.intelligence else {},
            
            # Soft Factors
            "management": data.intelligence.management_integrity[:300] if data.intelligence and data.intelligence.management_integrity else "Unknown",
            "moat": data.intelligence.product_moat[:300] if data.intelligence and data.intelligence.product_moat else "Unknown",
            "insider": data.intelligence.insider_activity[:200] if data.intelligence and data.intelligence.insider_activity else "Unknown",
            "dislocation": data.intelligence.dislocation_context[:200] if data.intelligence and data.intelligence.dislocation_context else "Unknown",
            
            # Blue Sky & Catalysts
            "blue_sky": data.intelligence.blue_sky.model_dump() if data.intelligence and data.intelligence.blue_sky else "Unknown",
            "catalysts": data.intelligence.catalysts.model_dump() if data.intelligence and data.intelligence.catalysts else "Unknown"
        }

        context_str = json.dumps(context, indent=2, default=str)

        # ========== 3. V3.4 决策 Prompt ==========
        prompt = f"""
        You are the Chief Investment Officer (CIO) executing the Mahaney Growth Protocol (MGP) V3.4.
        
        This Strategy V3.4 is the "Anti-Fragile Patch" for $10B-$50B mid-cap growth stocks:
        - Uses "Shadow Data" (LinkedIn hiring, customer quality) to verify hidden moats
        - Uses "Macro Valve" (US10Y yield) to protect against valuation kills
        - Implements "Polygraph" (CFO divergence, sandbagging) to detect fraud/opportunity

        Review the following data for {data.ticker} and render a Final Verdict.

        Data:
        {context_str}

        ### V3.4 Decision Logic Chain:

        1. **Macro Gate (V3.4)**:
           - If US10Y > 4.5% (Tight), ONLY accept PEG < 1.2
           - If VIX > 30, flag as "Panic Mode" - only right-side trades allowed

        2. **Sector Gate (V3.4)**:
           - Reject if sector_passed is False (Blacklisted industry)

        3. **Hygiene Gate (V3.3)**:
           - Revenue Growth > 20%? SBC/Rev < 20%? Dilution under control?

        4. **Polygraph Gate (V3.4)**:
           - If cash_flow_check_passed is False -> TRAP (CFO divergence = fraud risk)
           - If sandbagging_detected is True -> Bullish signal (management setting low bar)

        5. **Shadow Audit Gate (V3.4)**:
           - If is_fake_tech is True -> Major red flag (claims tech but no hiring)
           - If has_king_maker_clients is True -> Strong positive (validated by giants)

        6. **Valuation Gate (V3.3)**:
           - Is current price in macro-adjusted Bear Case zone?

        ### V3.4 Final Rating Categories:

        - **TACTICAL SNIPER** (⚔️):
            - Sandbagging detected (RPO strong + guidance weak) + Low valuation + Macro allows
            - "Heavy position for repair trade"

        - **STRATEGIC COMPOUNDER** (🏰):
            - Tech moat window > 3 years + King Maker client validation + Healthy cash flow
            - "Lock position, ignore quarterly noise"

        - **TRAP** (💣):
            - High growth but CFO < NI (cash flow divergence)
            - OR is_fake_tech detected (no real R&D hiring)
            - OR key executive departure
            - "Do not buy regardless of how cheap - potential fraud/failure"

        - **CONVICTION BUY**:
            - Reasonable Valuation + High Option Value + Clear Catalyst + Passes all V3.4 gates
            - "Rocket ready to launch"

        - **ACCUMULATE**:
            - Low Valuation + High Option Value but NO near-term catalyst
            - "Long-term winner, wait for wind"

        - **SPECULATIVE BUY**:
            - High Valuation (PEG > 2) but Massive Option Value + Strong Catalyst
            - "Expensive but explosive"

        - **VALUE TRAP**:
            - Low Valuation but NO Option Value (Old tech) and NO Catalyst
            - "Cheap for a reason"

        - **WATCH**:
            - Fundamentals okay but waiting for better price or clarity
            - OR VIX > 30 panic mode - wait for 20MA reclaim

        - **SKIP**:
            - Failed critical V3.4 gates (sector blacklist, CFO divergence)

        ### Output Requirement:
        Provide a structured JSON response with:
        - decision: Enum value (use EXACTLY one of: "TACTICAL SNIPER", "STRATEGIC COMPOUNDER", "TRAP", "CONVICTION BUY", "ACCUMULATE", "SPECULATIVE BUY", "VALUE TRAP", "WATCH", "SKIP")
        - confidence: "High", "Medium", or "Low"
        - rationale: A concise explanation focusing on the V3.4 logic (which gates passed/failed)
        - growth_thesis_intact: boolean
        - valuation_fit: boolean
        - is_true_discount: boolean
        """

        system_prompt = "You are a hedge fund CIO executing MGP V3.4 - the Anti-Fragile Growth Protocol. Be rigorous about the V3.4 gates."

        result = self.llm.extract_structured_data(prompt, TribunalDecision,
                                                  system_prompt=system_prompt)

        if not result:
            # Fallback
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
