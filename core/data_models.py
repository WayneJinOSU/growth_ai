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
    STRONG_BUY = "STRONG BUY"
    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"
    WATCH = "WATCH"


class Confidence(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class IronGateMetrics(BaseModel):
    revenue_cagr_5y: Optional[float] = None
    revenue_growth_current_q: Optional[float] = None
    revenue_growth_prev_y_q: Optional[float] = None
    peg_ratio: Optional[float] = None
    gross_margin_slope: Optional[float] = None  # Positive means increasing
    opex_growth: Optional[float] = None
    operating_leverage: Optional[bool] = None  # True if Rev Growth > OpEx Growth
    passed: bool = False
    fail_reason: Optional[str] = None


class IdentifierData(BaseModel):
    business_model: BusinessModel
    specific_kpis: List[str] = Field(default_factory=list)
    bear_case_hook: Optional[str] = None


class IntelligenceData(BaseModel):
    kpi_values: Dict[str, Any] = Field(default_factory=dict)
    management_integrity: Optional[str] = None
    product_moat: Optional[str] = None
    insider_activity: Optional[str] = None
    dislocation_context: Optional[str] = None


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
    iron_gate: Optional[IronGateMetrics] = None
    identifier: Optional[IdentifierData] = None
    intelligence: Optional[IntelligenceData] = None
    tribunal: Optional[TribunalDecision] = None

    error: Optional[str] = None


class AnalysisReport(BaseModel):
    ticker: str
    timestamp: str
    final_decision: Decision
    summary: str
    details: CompanyData

