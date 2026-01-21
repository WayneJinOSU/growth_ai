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


class GatekeeperData(BaseModel):
    sector_check_passed: bool
    macro_mode: MacroMode
    us10y_yield: Optional[float] = None
    vix_value: Optional[float] = None
    future_revenue_cagr_3y: Optional[float] = None  # V3.5 New
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


class PolygraphData(BaseModel):
    cash_flow_divergence_check: bool = True  # True means PASS (No massive divergence)
    sandbagging_detected: bool = False       # True means Sandbagging detected (Good for Sniper)
    details: Optional[str] = None


class DeepAuditData(BaseModel):
    """Formerly IronGateMetrics, expanded for V3.5"""
    revenue_cagr_ny: Optional[float] = None
    revenue_growth_current_q: Optional[float] = None
    revenue_growth_prev_y_q: Optional[float] = None
    peg_ratio: Optional[float] = None
    gross_margin_slope: Optional[float] = None  # Positive means increasing
    opex_growth: Optional[float] = None
    operating_leverage: Optional[bool] = None  # True if Rev Growth > OpEx Growth
    
    # V3.2
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

    passed: bool = False
    fail_reason: Optional[str] = None


class IdentifierData(BaseModel):
    business_model: BusinessModel
    specific_kpis: List[str] = Field(default_factory=list)
    bear_case_hook: Optional[str] = None


class BlueSkyData(BaseModel):
    rnd_effectiveness: Optional[str] = None
    tam_expansion: Optional[str] = None


class CatalystData(BaseModel):
    upcoming_events: List[str] = Field(default_factory=list)
    variant_perception: Optional[str] = None
    coattail_effect: Optional[str] = None # V3.5


class PhysicsData(BaseModel):
    """V3.5 New: Quant/VPA Data"""
    sma_20: Optional[float] = None
    current_price: Optional[float] = None
    relative_volume: Optional[float] = None # RVol
    is_accumulation: bool = False
    is_ignition: bool = False
    is_broken_trend: bool = False # Price < SMA20 for 3 days
    details: Optional[str] = None


class IntelligenceData(BaseModel):
    kpi_values: Dict[str, Any] = Field(default_factory=dict)
    management_integrity: Optional[str] = None
    product_moat: Optional[str] = None
    insider_activity: Optional[str] = None
    dislocation_context: Optional[str] = None
    
    # V3.2
    blue_sky: Optional[BlueSkyData] = None
    catalysts: Optional[CatalystData] = None


class TribunalDecision(BaseModel):
    decision: Decision
    confidence: Confidence
    rationale: str
    growth_thesis_intact: bool
    valuation_fit: bool
    is_true_discount: bool


class CompanyData(BaseModel):
    ticker: str
    company_name: Optional[str] = None
    current_price: Optional[float] = None
    market_cap: Optional[float] = None

    # Phases
    gatekeeper: Optional[GatekeeperData] = None
    deep_audit: Optional[DeepAuditData] = None # Renamed from iron_gate
    shadow_audit: Optional[ShadowAuditData] = None
    identifier: Optional[IdentifierData] = None
    polygraph: Optional[PolygraphData] = None
    intelligence: Optional[IntelligenceData] = None
    physics: Optional[PhysicsData] = None # V3.5 New
    tribunal: Optional[TribunalDecision] = None

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
