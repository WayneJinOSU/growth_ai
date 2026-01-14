import os
from dotenv import load_dotenv

load_dotenv()

# ========== API Keys ==========
FMP_API_KEY = os.getenv("FMP_API_KEY", "yiQrRNxbbe4TofnvMPGPz62QSTuT6Pbe")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "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")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "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")

if not FMP_API_KEY:
    print("Warning: FMP_API_KEY not found in environment variables.")
if not OPENAI_API_KEY:
    print("Warning: OPENAI_API_KEY not found in environment variables.")
if not TAVILY_API_KEY:
    print("Warning: TAVILY_API_KEY not found in environment variables.")

# ========== MGP Strategy Parameters ==========
# 可动态调整的策略阈值

# --- Phase 1: Iron Gate ---
# CAGR 计算年限 (原为5年，改为3年)
CAGR_YEARS = 3

# 季度数据配置
QUARTERS_FOR_YOY = 5               # 同比增速需要的季度数 (Q0 vs Q-4)
QUARTERS_FOR_DECEL_CHECK = 9       # 减速预警需要的季度数 (支持 Q-8 计算)
QUARTERS_FOR_MARGIN_SLOPE = 6      # 毛利斜率计算的季度数
QUARTERS_FOR_NI_SUM = 4            # 净利润求和的季度数 (TTM)

# 增长率阈值
GROWTH_THRESHOLD_CAGR = 0.15       # CAGR 最低要求 (15%)
GROWTH_THRESHOLD_QUARTER = 0.20    # 季度同比增速最低要求 (20%)

# 减速预警：前期增速阈值 & 容许下降比例
DECEL_PREV_GROWTH_THRESHOLD = 0.40  # 只有当前期增速 > 40% 时才检测减速
DECEL_DROP_RATIO = 0.7              # 增速下降超过 50% 触发警报

# PEG 阈值
MIN_NET_MARGIN_FOR_PEG = 0.03  # 净利率 > 3% 才被视为实质盈利 (否则走未盈利逻辑)
PEG_THRESHOLD_STRONG_BUY = 1.0     # PEG < 1.0 -> 极度低估
PEG_THRESHOLD_BUY = 1.5            # PEG 1.0 - 1.5 -> 合理买入
PEG_THRESHOLD_BUBBLE = 2.0         # PEG > 2.0 -> 泡沫风险 (Iron Gate 淘汰线)
PEG_THRESHOLD_SELL = 2.5           # PEG > 2.5 -> 卖出信号 (Watchtower)

# 毛利斜率噪音容忍度
GROSS_MARGIN_SLOPE_TOLERANCE = -0.005  # 允许轻微下降

# --- Phase 4: Tribunal ---
# 高速增长豁免线 (PEG > 2.0 但增速超过此值可豁免)
HIGH_GROWTH_EXEMPTION = 0.40  # 40%
