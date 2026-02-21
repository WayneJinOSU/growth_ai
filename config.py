import os
from dotenv import load_dotenv

load_dotenv()

# ========== API Keys ==========
FMP_API_KEY = os.getenv("FMP_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

if not FMP_API_KEY:
    print("Warning: FMP_API_KEY not found in environment variables.")
if not OPENAI_API_KEY:
    print("Warning: OPENAI_API_KEY not found in environment variables.")
if not TAVILY_API_KEY:
    print("Warning: TAVILY_API_KEY not found in environment variables.")

# ========== Report Language ==========
# "en" = English output (LLM + Report Structure)
# "zh" = Chinese output (中文输出)
REPORT_LANGUAGE = os.getenv("REPORT_LANGUAGE", "en")

# ========== MGP Strategy Parameters V3.5 ==========

# --- Phase 0: Gatekeeper ---
# V3.5 Absolute Blacklist
BLACKLIST_SECTORS = [
    "Fashion", "Apparel", "Footwear",  # Pure Consumer Fashion
    "Banks - Regional", "Regional Banks", # Black Box Balance Sheets
    "Oil & Gas", "Energy", "Metals & Mining", "Gold", "Silver", # Commodities
    "Auto Manufacturers", "Airlines", "Airports" # Heavy Asset / Unions
]

# V3.5 Future Growth Threshold (The 20% Iron Rule)
FUTURE_CAGR_THRESHOLD = 0.20

# --- Phase 1: Deep Audit (formerly Iron Gate) ---
# CAGR Calculation Years
CAGR_YEARS = 3

# Quarterly Data Config
QUARTERS_FOR_YOY = 5
QUARTERS_FOR_DECEL_CHECK = 9
QUARTERS_FOR_MARGIN_SLOPE = 6
QUARTERS_FOR_NI_SUM = 4

# Thresholds
GROWTH_THRESHOLD_CAGR = 0.15
GROWTH_THRESHOLD_QUARTER = 0.20
DECEL_PREV_GROWTH_THRESHOLD = 0.40
DECEL_DROP_RATIO = 0.7

# V3.5 Segment Specific Thresholds
NDR_THRESHOLD = 1.10  # 110% Net Dollar Retention
RULE_OF_40_THRESHOLD = 0.40 # Rev Growth + FCF Margin
SBC_THRESHOLD_STRICT = 0.20 # 20% max
SBC_THRESHOLD_KILL = 0.25   # 25% automatic kill

# V3.5 Insider Selling (Institutional-Grade)
INSIDER_SELL_COUNT_THRESHOLD = 3  # API 初筛：> N 次 C-Level sale 触发 Agent
INSIDER_INTENSITY_PASS = 0.05     # < 5%: 资产配置，PASS
INSIDER_INTENSITY_WARNING = 0.20  # > 20%: 重大减持，WARNING
INSIDER_INTENSITY_RED_FLAG = 0.50 # > 50%: 清仓式出逃，RED FLAG
INSIDER_PRICE_DROP_DANGER = -0.20 # 股价跌 > 20% 期间卖出 = 跳船信号

# Profitability
MIN_NET_MARGIN_FOR_PEG = 0.03
PEG_THRESHOLD_STRONG_BUY = 1.0
PEG_THRESHOLD_BUY = 1.5
PEG_THRESHOLD_BUBBLE = 2.0
PEG_THRESHOLD_SELL = 2.5
PEG_DREAM_PREMIUM = 2.0 # Allowed if R&D > 20% & New Growth > 50%

GROSS_MARGIN_SLOPE_TOLERANCE = -0.005

# --- Phase 4: Physics (VPA) ---
RVOL_ACCUMULATION = 1.5
RVOL_IGNITION = 2.0
SMA_PERIOD = 20
ACCUMULATION_RANGE_PCT = 0.02 # 2% price range

# --- Phase 7: Tribunal ---
HIGH_GROWTH_EXEMPTION = 0.40
