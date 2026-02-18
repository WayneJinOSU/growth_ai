"""
Phase 0: The Gatekeeper (前置过滤器) - V3.5 Singularity
================================================
在进入财报分析前，先排除"不该玩的赛道"和"不该玩的时间"。

核心检查项:
1. 宏观压力阀 (Macro Valve) - 根据 10Y 美债收益率确定估值容忍度
2. VIX 熔断机制 (VIX Breaker) - 市场恐慌时禁止左侧买入
3. 行业黑名单 (Absolute Blacklist) - 剔除护城河不可验证的行业
4. 20% 铁律 (Future 20% Iron Rule) - 3年预期营收 CAGR 必须 > 20%
"""

from typing import Optional, Dict
from tools.fmp import FMPClient
from tools.search import SearchClient
from tools.yahoo import YahooClient
from core.data_models import GatekeeperData, MacroMode
import config


class Gatekeeper:
    """
    前置过滤器：MGP V3.5 策略的第零道关卡
    """
    
    # 宏观阈值
    MACRO_LOOSE_THRESHOLD = 3.0    # < 3.0% = 宽松
    MACRO_TIGHT_THRESHOLD = 4.5    # > 4.5% = 紧缩
    VIX_PANIC_THRESHOLD = 30       # > 30 = 市场恐慌

    def __init__(self, fmp_client: FMPClient = None, search_client: SearchClient = None, yahoo_client: YahooClient = None):
        self.fmp = fmp_client or FMPClient()
        self.search = search_client or SearchClient()
        self.yahoo = yahoo_client or YahooClient()

    def _determine_macro_mode(self, us10y: Optional[float]) -> MacroMode:
        """
        根据 10 年期美债收益率确定宏观模式
        """
        if us10y is None:
            print("      [Warning] Unable to fetch US10Y yield. Assuming Neutral mode.")
            return MacroMode.NEUTRAL
        
        if us10y < self.MACRO_LOOSE_THRESHOLD:
            return MacroMode.LOOSE
        elif us10y > self.MACRO_TIGHT_THRESHOLD:
            return MacroMode.TIGHT
        else:
            return MacroMode.NEUTRAL

    def _check_sector(self, profile: Optional[Dict]) -> tuple[bool, str]:
        """
        检查公司行业是否在黑名单内 (V3.5 Absolute Blacklist)
        """
        if not profile:
            return True, "Profile unavailable, assuming pass"
        
        sector = profile.get('sector', '')
        industry = profile.get('industry', '')
        
        # 检查黑名单 (from config)
        for blacklisted in config.BLACKLIST_SECTORS:
            if blacklisted.lower() in sector.lower() or blacklisted.lower() in industry.lower():
                return False, f"Blacklisted sector/industry: {sector} / {industry} (Matches '{blacklisted}')"
        
        return True, f"Sector: {sector}, Industry: {industry}"

    def analyze(self, ticker: str) -> GatekeeperData:
        """
        执行 V3.5 前置过滤分析
        """
        print(f"  [Phase 0] Gatekeeper Analysis for {ticker} (V3.5)...")
        
        # ========== 1. 获取宏观数据 ==========
        print("    - Fetching macro data...")
        us10y = self.search.get_treasury_yield()
        print(f"      US 10Y Treasury Yield: {us10y:.2f}%" if us10y else "      US 10Y Treasury Yield: N/A")
        
        vix = self.fmp.get_vix()
        print(f"      VIX: {vix:.2f}" if vix else "      VIX: N/A")
        
        # ========== 2. 判断宏观模式 ==========
        macro_mode = self._determine_macro_mode(us10y)
        print(f"      Macro Mode: {macro_mode.value}")
        
        # ========== 3. VIX 熔断检查 ==========
        vix_panic = vix is not None and vix > self.VIX_PANIC_THRESHOLD
        if vix_panic:
            print(f"      ⚠️ VIX PANIC MODE: VIX {vix:.2f} > {self.VIX_PANIC_THRESHOLD}")
        
        # ========== 4. 行业过滤 ==========
        print("    - Checking sector blacklist...")
        profile = self.fmp.get_profile(ticker)
        sector_passed, sector_reason = self._check_sector(profile)
        print(f"      {sector_reason}")
        
        # ========== 5. 20% 铁律 (Future CAGR) ==========
        print("    - Checking Future 20% Iron Rule...")
        future_cagr = self.yahoo.get_future_growth_estimates(ticker)
        
        cagr_passed = True
        cagr_reason = "Passed"
        
        if future_cagr is not None:
            # Convert decimal to percent for check
            # Yahoo often returns e.g. 0.25 for 25%
            # If > 1.0, might be percentage already? Usually it's decimal.
            # Assuming decimal.
            print(f"      Future Growth Est: {future_cagr:.1%}")
            
            if future_cagr < config.FUTURE_CAGR_THRESHOLD:
                cagr_passed = False
                cagr_reason = f"Future Growth {future_cagr:.1%} < {config.FUTURE_CAGR_THRESHOLD:.0%} Threshold"
        else:
            print("      [Warning] Future growth estimates unavailable. Skipping Iron Rule check.")
            
        
        # ========== 6. 综合判断 ==========
        passed = sector_passed and cagr_passed
        fail_reason = None
        
        if not sector_passed:
            fail_reason = sector_reason
        elif not cagr_passed:
            fail_reason = cagr_reason
            
        if not passed:
            print(f"    - Gatekeeper FAILED: {fail_reason}")
        elif vix_panic:
            print("    - Gatekeeper PASSED (with VIX Warning)")
        else:
            print(f"    - Gatekeeper PASSED for {ticker}")
        
        return GatekeeperData(
            sector_check_passed=sector_passed,
            macro_mode=macro_mode,
            us10y_yield=us10y,
            vix_value=vix,
            future_revenue_cagr_3y=future_cagr,
            passed=passed,
            fail_reason=fail_reason
        )

gatekeeper = Gatekeeper()