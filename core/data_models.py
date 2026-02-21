from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class BusinessModel(str, Enum):
    SAAS = "SaaS"
    CONSUMPTION = "Consumption"
    MARKETPLACE = "Marketplace"
    ADVERTISING = "Advertising"
    HARDWARE = "Hardware"
    OTHER = "Other"


class SearchReference(BaseModel):
    id: int  # Citation ID (e.g. 1 for [1])
    title: str
    url: str
    snippet: Optional[str] = None


class Decision(str, Enum):
    # V3.5 New Decisions
    FIRE = "FIRE"  # All gates passed (Ignition)
    
    # V3.4 Legacy Decisions
    TACTICAL_SNIPER = "TACTICAL SNIPER"
    STRATEGIC_COMPOUNDER = "STRATEGIC COMPOUNDER"
    TRAP = "TRAP"
    
    # Legacy / Compatible Decisions
    CONVICTION_BUY = "CONVICTION BUY"
    ACCUMULATE = "ACCUMULATE"
    SPECULATIVE_BUY = "SPECULATIVE BUY"
    VALUE_TRAP = "VALUE TRAP"
    WATCH = "WATCH"
    SKIP = "SKIP"  # For failed Gates


class MacroMode(str, Enum):
    LOOSE = "Loose"      # < 3.0%
    NEUTRAL = "Neutral"  # 3.0% - 4.5%
    TIGHT = "Tight"      # > 4.5%


class Confidence(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class TierLevel(str, Enum):
    """V3.5: Moat tier for Fortress Test"""
    TIER_1 = "Tier 1"  # King Maker + Core Metrics Pass
    TIER_2 = "Tier 2"  # Only Core Metrics Pass
    TIER_3 = "Tier 3"  # Weak / No clear moat


class StrategicDefinition(str, Enum):
    """V3.5 Phase 6: Executive Matrix Output"""
    DIAMOND_SETUP = "💎 Diamond Setup"  # Strong Catalyst + Low Valuation
    MOMENTUM_RIDE = "🚀 Momentum Ride"  # Strong Catalyst + High Valuation
    FORTRESS_ACCUMULATION = "🏰 Fortress Accumulation"  # No Catalyst + Low Val + Tier 1
    DEAD_MONEY = "⚰️ Dead Money"  # No Catalyst + Low Val + Tier 2/3
    CORRECTION_WATCH = "⏸️ Correction Watch"  # No Catalyst + High Val + Tier 1
    SHORT_TARGET = "💣 Short Target"  # No Catalyst + High Val + Tier 2/3


class GatekeeperData(BaseModel):
    sector_check_passed: bool
    macro_mode: MacroMode
    us10y_yield: Optional[float] = None
    vix_value: Optional[float] = None
    future_revenue_cagr_3y: Optional[float] = None  # V3.5 New
    cagr_passed: bool = True # Track raw check before deeper evaluation
    passed: bool
    fail_reason: Optional[str] = None


class ShadowAuditData(BaseModel):
    linkedin_hiring_audit: Optional[str] = None
    customer_quality_audit: Optional[str] = None
    is_fake_tech: bool = False
    has_king_maker_clients: bool = False
    
    # V3.5 New
    app_store_rank: Optional[str] = None
    marketing_efficiency: Optional[str] = None  # Organic Growth signal
    organic_growth_confirmed: bool = False
    
    # Sandbagging (moved from Polygraph)
    sandbagging_detected: bool = False
    sandbagging_details: Optional[str] = None


class DeepAuditData(BaseModel):
    """Formerly IronGateMetrics, expanded for V3.5"""
    revenue_cagr_ny: Optional[float] = None
    revenue_growth_current_q: Optional[float] = None
    revenue_growth_prev_y_q: Optional[float] = None
    peg_ratio: Optional[float] = None
    gross_margin_slope: Optional[float] = None  # Positive means increasing
    opex_growth: Optional[float] = None
    operating_leverage: Optional[bool] = None  # True if Rev Growth > OpEx Growth
    
    sbc_revenue_ratio: Optional[float] = None
    share_count_growth: Optional[float] = None
    dilution_shield_passed: Optional[bool] = None
    
    # V3.5 New Segment Specifics
    ndr: Optional[float] = None  # SaaS
    rpo_growth: Optional[float] = None # SaaS
    rule_of_40: Optional[float] = None # Consumption
    book_to_bill: Optional[float] = None # Hard Tech
    inventory_health: Optional[str] = None # Hard Tech
    take_rate_trend: Optional[str] = None # Marketplace
    insider_selling_risk: bool = False # Universal Lie Detector
    insider_selling_message: Optional[str] = None # Detail note from Agent
    insider_score: int = 0  # 0=clean, 1=routine, 2=warning, 3=red_flag
    insider_details: Optional[Dict[str, Any]] = None  # Full breakdown for report

    eps_cagr_ny: Optional[float] = None # V3.5
    red_flags: int = 0 # V3.5 New: Fail only on multiple flags

    passed: bool = False
    fail_reason: Optional[str] = None


class IdentifierData(BaseModel):
    business_model: BusinessModel
    specific_kpis: List[str] = Field(default_factory=list)
    bear_case_hook: Optional[str] = None


class BlueSkyData(BaseModel):
    rnd_effectiveness: Optional[str] = None
    tam_expansion: Optional[str] = None
    is_strong_second_curve: bool = False


class CatalystData(BaseModel):
    """V3.5 Phase 5: Catalysts & Waves"""
    # Primary: Thematic Waves (Macro Need)
    thematic_waves: Optional[str] = None  # e.g., "Labor Shortage -> AI Demand"
    wave_strength: Optional[str] = None  # "High", "Medium", "Low"
    
    # Secondary: Hard Events
    upcoming_events: List[str] = Field(default_factory=list)
    catalyst_analysis: Optional[str] = None
    
    # Legacy
    variant_perception: Optional[str] = None
    coattail_effect: Optional[str] = None


class PhysicsData(BaseModel):
    """V3.5 Phase 7: Physics of VPA"""
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None  # V3.5 New
    sma_200: Optional[float] = None # V3.5 New
    current_price: Optional[float] = None
    relative_volume: Optional[float] = None  # RVol = Vol / Avg_Vol_20
    daily_range: Optional[float] = None  # (High - Low) / Close
    close_strength: Optional[float] = None  # (Close - Low) / (High - Low)
    days_below_sma20: int = 0
    days_below_sma50: int = 0  # V3.5 New
    
    is_accumulation: bool = False  # Range < 2% + RVol > 1.5
    is_ignition: bool = False  # Price > SMA20 + RVol > 2.0 + Strong Close
    is_high_risk: bool = False  # High Rvol in down days or breakdown
    is_broken_trend: bool = False  # Close < SMA50 for 3+ days (Modified for Mid-Large Cap)
    
    details: Optional[str] = None
    
    # AI Analysis (V3.5 Blue Sky Extension)
    ai_analysis: Optional[str] = None # Detailed Physical Dynamics Analysis
    ai_conclusion: Optional[str] = None # Ignition, Broken Trend, Accumulation, etc.
    ai_recommendation: Optional[str] = None # Strong Buy, Buy, Wait, Observe, etc.


class StrategicPricingData(BaseModel):
    """V3.5 Phase 6: Strategic Pricing Output"""
    # Step 1: Valuation Scrub
    adjusted_pe: Optional[float] = None
    adjustment_reason: Optional[str] = None  # "Sandbagger Discount" or "Over-Promiser Premium"
    
    # Step 2: Fortress Test
    tier_level: Optional[TierLevel] = None
    tier_rationale: Optional[str] = None
    
    # Step 3: Blue Sky Re-Rating
    peg_limit: float = 2.0  # Default, can be raised to 2.5 if Blue Sky triggers
    blue_sky_triggered: bool = False
    
    # Step 4: Executive Matrix
    catalyst_strength: Optional[str] = None  # "High" or "Low/None"
    valuation_status: Optional[str] = None  # "Green" or "Red"
    strategic_definition: Optional[StrategicDefinition] = None
    action_instruction: Optional[str] = None


class BlueSkyPhaseData(BaseModel):
    """Phase 4: Blue Sky & Valuation"""
    blue_sky: Optional[BlueSkyData] = None
    macro_valuation_analysis: Optional[str] = None


class IntelligenceData(BaseModel):
    """Phase 3: Intelligence (软性情报)"""
    kpi_values: Dict[str, Any] = Field(default_factory=dict)
    management_integrity: Optional[str] = None
    product_moat: Optional[str] = None
    insider_activity: Optional[str] = None
    dislocation_context: Optional[str] = None


class TribunalDecision(BaseModel):
    decision: Decision
    confidence: Confidence
    rationale: str
    checklist_results: Dict[str, bool] = Field(default_factory=dict)  # V3.5 New
    growth_thesis_intact: bool
    valuation_fit: bool
    is_true_discount: bool


class CompanyData(BaseModel):
    ticker: str
    company_name: Optional[str] = None
    current_price: Optional[float] = None
    market_cap: Optional[float] = None

    # Runtime config (set by main.py)
    deep_search: bool = False
    force_deep_dive: bool = False
    report_language: str = "en"  # "en" or "zh"

    # Cached shared data (set once by main.py, read by all Phases)
    company_profile: Optional[Dict[str, Any]] = None
    press_releases: List[Dict[str, Any]] = Field(default_factory=list)

    # Phases
    gatekeeper: Optional[GatekeeperData] = None
    deep_audit: Optional[DeepAuditData] = None  # Renamed from iron_gate
    shadow_audit: Optional[ShadowAuditData] = None
    identifier: Optional[IdentifierData] = None
    intelligence: Optional[IntelligenceData] = None
    blue_sky_phase: Optional[BlueSkyPhaseData] = None  # V3.5 Phase 4
    catalysts: Optional[CatalystData] = None  # V3.5 Phase 5
    strategic_pricing: Optional[StrategicPricingData] = None  # V3.5 Phase 6
    physics: Optional[PhysicsData] = None  # V3.5 Phase 7
    tribunal: Optional[TribunalDecision] = None
    
    references: List[SearchReference] = Field(default_factory=list)  # V3.5 New


    error: Optional[str] = None
    
    # Compatibility property for legacy code if needed (optional)
    @property
    def iron_gate(self) -> Optional[DeepAuditData]:
        return self.deep_audit

    @iron_gate.setter
    def iron_gate(self, value: Optional[DeepAuditData]):
        self.deep_audit = value


class AnalysisReport(BaseModel):
    ticker: str
    timestamp: str
    final_decision: Decision
    summary: str
    details: CompanyData
