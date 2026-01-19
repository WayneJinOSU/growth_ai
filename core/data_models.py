from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class BusinessModel(str, Enum):
    SAAS = "SaaS"
    CONSUMPTION = "Consumption"
    MARKETPLACE = "Marketplace"
    ADVERTISING = "Advertising"
    HARDWARE = "Hardware"
    PHARMA = "Pharma"  # V3.7: 医药行业
    SEMICONDUCTOR = "Semiconductor"  # V3.7: 半导体
    OTHER = "Other"


class MoatStrength(str, Enum):
    """V3.7: 护城河强度 - 用于 Moat Lock-in 判断"""
    HIGH = "High"      # SaaS, Pharma - 客户跑不掉
    MEDIUM = "Medium"  # Semiconductor, Enterprise Software
    LOW = "Low"        # Consumer, Hardware - 客户容易跑


class Decision(str, Enum):
    # V3.7 Core Decisions (Armored Sniper)
    TACTICAL_SNIPER = "TACTICAL SNIPER"      # 基本面沙袋 + 估值低 + 宏观允许
    STRATEGIC_COMPOUNDER = "STRATEGIC COMPOUNDER"  # 技术独占窗口 > 3年
    TRAP = "TRAP"                            # CFO < NI 或核心技术人员离职
    
    # Standard Decisions
    CONVICTION_BUY = "CONVICTION BUY"
    ACCUMULATE = "ACCUMULATE"
    SPECULATIVE_BUY = "SPECULATIVE BUY"
    VALUE_TRAP = "VALUE TRAP"
    WATCH = "WATCH"
    SKIP = "SKIP"  # For failed gates


class MacroMode(str, Enum):
    LOOSE = "Loose"      # < 3.0%
    NEUTRAL = "Neutral"  # 3.0% - 4.5%
    TIGHT = "Tight"      # > 4.5%


class Confidence(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


# ========== V3.7 Phase 0: Pedigree Check ==========
class PedigreeData(BaseModel):
    """V3.7 血统验证数据"""
    market_cap: Optional[float] = None
    market_cap_passed: bool = False  # > $50B
    sector: Optional[str] = None
    industry: Optional[str] = None
    sector_passed: bool = False  # 白名单通过
    revenue_cagr_10y: Optional[float] = None  # 10年营收CAGR
    is_industry_winner: bool = False  # 是否为行业赢家
    passed: bool = False
    fail_reason: Optional[str] = None


class GatekeeperData(BaseModel):
    """V3.7 Gatekeeper 数据 (包含 Pedigree + Macro)"""
    # Pedigree Check (V3.7 New)
    pedigree: Optional[PedigreeData] = None
    
    # Macro Check (Legacy)
    sector_check_passed: bool = True
    macro_mode: MacroMode = MacroMode.NEUTRAL
    us10y_yield: Optional[float] = None
    vix_value: Optional[float] = None
    passed: bool = False
    fail_reason: Optional[str] = None


# ========== V3.7 Phase 1: Financial Forensics ==========
class ForensicsData(BaseModel):
    """V3.7 财务侦探数据 - 判断"是造不出来，还是卖不出去" """
    
    # 指标 A: 库存周转测试 (Inventory Check)
    inventory_turnover_current: Optional[float] = None
    inventory_turnover_3y_avg: Optional[float] = None
    inventory_check_passed: bool = True  # 允许 -10% 波动
    
    # 指标 B: 资本开支脉冲 (Capex Pulse)
    capex_revenue_current: Optional[float] = None
    capex_revenue_3y_avg: Optional[float] = None
    capex_pulse_positive: bool = False  # Capex/Rev > 3Y Avg = 正信号
    
    # 指标 C: 定价权测试 (Pricing Power)
    gross_margin_current: Optional[float] = None
    gross_margin_prev_year: Optional[float] = None
    gross_margin_change: Optional[float] = None  # 变化百分点
    pricing_power_intact: bool = True  # 跌幅 < 3%
    
    # 护城河锁定 (Moat Lock-in)
    moat_strength: MoatStrength = MoatStrength.MEDIUM
    moat_assessment: Optional[str] = None
    
    passed: bool = False
    fail_reason: Optional[str] = None


class ShadowAuditData(BaseModel):
    linkedin_hiring_audit: Optional[str] = None
    customer_quality_audit: Optional[str] = None
    is_fake_tech: bool = False
    has_king_maker_clients: bool = False


class PolygraphData(BaseModel):
    cash_flow_divergence_check: bool = True  # True means PASS (No massive divergence)
    sandbagging_detected: bool = False       # True means Sandbagging detected (Good for Sniper)
    details: Optional[str] = None


# ========== V3.7 Phase 2: Financial Armor ==========
class IronGateMetrics(BaseModel):
    """V3.7 财务装甲数据"""
    
    # === 毛利率熔断 (Gross Margin Fuse) ===
    gross_margin_current: Optional[float] = None
    gross_margin_prev_year: Optional[float] = None
    gross_margin_yoy_change_bps: Optional[float] = None  # 基点变化
    gross_margin_safe: bool = True  # 下降 < 300bps
    
    # === 债务窒息线 (Debt Suffocation Line) ===
    net_debt: Optional[float] = None
    ebitda: Optional[float] = None
    net_debt_to_ebitda: Optional[float] = None
    cash_runway_months: Optional[float] = None  # 备选: 现金跑道
    debt_safe: bool = True  # Net Debt/EBITDA < 3.0x 或 现金跑道 > 24个月
    
    # === 稀释墙 (Dilution Wall) ===
    sbc_annual: Optional[float] = None
    market_cap: Optional[float] = None
    sbc_dilution_rate: Optional[float] = None  # SBC / Market Cap
    dilution_safe: bool = True  # < 3%
    
    # === Legacy Metrics (保留兼容性) ===
    revenue_cagr_ny: Optional[float] = None
    revenue_growth_current_q: Optional[float] = None
    revenue_growth_prev_y_q: Optional[float] = None
    peg_ratio: Optional[float] = None
    gross_margin_slope: Optional[float] = None
    opex_growth: Optional[float] = None
    operating_leverage: Optional[bool] = None
    sbc_revenue_ratio: Optional[float] = None
    share_count_growth: Optional[float] = None
    dilution_shield_passed: Optional[bool] = None

    passed: bool = False
    fail_reason: Optional[str] = None


# ========== V3.7 Phase 3: Entry & Valuation ==========
class ValuationData(BaseModel):
    """V3.7 估值弹簧数据"""
    
    # Forward Spring Pricing (前瞻性定价)
    forward_pe: Optional[float] = None
    forward_pe_signal: bool = False  # < 20x
    
    # PEG Safety Net
    peg_ratio: Optional[float] = None
    peg_signal: bool = False  # < 0.6
    
    # Historical PE Z-Score (备选)
    current_pe: Optional[float] = None
    pe_5y_avg: Optional[float] = None
    pe_5y_std: Optional[float] = None
    pe_z_score: Optional[float] = None
    historical_pe_signal: bool = False  # Current < (Avg - 1 Std)
    
    # Kitchen Sink (厨房水槽买点)
    last_earnings_date: Optional[str] = None
    price_reaction_positive: bool = False  # 坏消息但股价不跌
    kitchen_sink_signal: bool = False
    
    # 综合买入信号
    buy_signal_triggered: bool = False


class IdentifierData(BaseModel):
    """V3.7 商业模式识别 + Financial Forensics"""
    business_model: BusinessModel
    specific_kpis: List[str] = Field(default_factory=list)
    bear_case_hook: Optional[str] = None
    
    # V3.7: Financial Forensics
    forensics: Optional[ForensicsData] = None


class BlueSkyData(BaseModel):
    rnd_effectiveness: Optional[str] = None
    tam_expansion: Optional[str] = None


# ========== V3.7 Phase 4: Constraints & Catalysts ==========
class CatalystData(BaseModel):
    """V3.7 催化剂数据"""
    upcoming_events: List[str] = Field(default_factory=list)
    variant_perception: Optional[str] = None
    
    # V3.7: 催化剂侦测
    catalyst_keywords_found: List[str] = Field(default_factory=list)  # "Approval", "Launch", etc.
    catalyst_within_12m: bool = False  # 催化剂是否在 12 个月内
    catalyst_details: Optional[str] = None


class ConstraintsData(BaseModel):
    """V3.7 时空约束数据"""
    # 时间视界 (Timeline)
    bottleneck_resolution_months: Optional[int] = None  # 瓶颈解决预计时间
    timeline_acceptable: bool = False  # <= 12 个月
    
    # 催化剂
    catalyst: Optional[CatalystData] = None
    has_near_term_catalyst: bool = False
    
    # 强制退出规则
    holding_period_months: int = 0
    should_time_stop: bool = False  # 持有 6 个月后无进展


class IntelligenceData(BaseModel):
    kpi_values: Dict[str, Any] = Field(default_factory=dict)
    management_integrity: Optional[str] = None
    product_moat: Optional[str] = None
    insider_activity: Optional[str] = None
    dislocation_context: Optional[str] = None
    
    # V3.2
    blue_sky: Optional[BlueSkyData] = None
    catalysts: Optional[CatalystData] = None
    
    # V3.7: Constraints
    constraints: Optional[ConstraintsData] = None


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

    # V3.7 Phases
    gatekeeper: Optional[GatekeeperData] = None      # Phase 0: Pedigree + Macro
    identifier: Optional[IdentifierData] = None      # Phase 1: Forensics + Business Model
    iron_gate: Optional[IronGateMetrics] = None      # Phase 2: Financial Armor
    valuation: Optional[ValuationData] = None        # Phase 3: Entry & Valuation (V3.7 New)
    intelligence: Optional[IntelligenceData] = None  # Phase 4: Catalysts & Constraints
    tribunal: Optional[TribunalDecision] = None      # Phase 5: Final Decision
    
    # Legacy (保留兼容性)
    shadow_audit: Optional[ShadowAuditData] = None
    polygraph: Optional[PolygraphData] = None

    error: Optional[str] = None


class AnalysisReport(BaseModel):
    ticker: str
    timestamp: str
    final_decision: Decision
    summary: str
    details: CompanyData

