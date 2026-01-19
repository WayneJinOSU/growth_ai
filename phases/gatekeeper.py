"""
Phase 0: The Gatekeeper (前置过滤器) - V3.4 New
================================================
在进入财报分析前，先排除"不该玩的赛道"和"不该玩的时间"。

核心检查项:
1. 宏观压力阀 (Macro Valve) - 根据 10Y 美债收益率确定估值容忍度
2. VIX 熔断机制 (VIX Breaker) - 市场恐慌时禁止左侧买入
3. 行业黑白名单 (Sector Filter) - 剔除护城河不可验证的行业
"""

from typing import Optional, Dict
from tools.fmp import FMPClient
from tools.search import SearchClient
from core.data_models import GatekeeperData, MacroMode


class Gatekeeper:
    """
    前置过滤器：MGP V3.4 策略的第零道关卡
    
    职责：
    - 获取宏观数据 (美债收益率、VIX)
    - 判断当前宏观环境 (Loose/Neutral/Tight)
    - 检查公司行业是否在白名单内
    """
    
    # 行业白名单 - 护城河"物理可验证"
    SECTOR_WHITELIST = [
        # 硬科技/高端制造
        "Technology", "Semiconductors", "Software", "Hardware",
        "Communication Services",
        # 企业级软件 B2B SaaS
        "Information Technology", "IT Services",
        # 生物医药
        "Healthcare", "Biotechnology", "Pharmaceuticals",
        # 工业科技
        "Industrials", "Aerospace & Defense",
    ]
    
    # 行业黑名单 - 护城河不可验证或周期性强
    SECTOR_BLACKLIST = [
        # 纯消费品牌 (时尚度变化快)
        "Consumer Cyclical", "Apparel", "Footwear", "Luxury Goods",
        "Restaurants", "Leisure",
        # 纯金融/银行 (资产负债表黑箱)
        "Financial Services", "Banks", "Regional Banks", "Insurance",
        # 资源周期股 (定价权在期货市场)
        "Basic Materials", "Energy", "Oil & Gas", "Mining",
        # 房地产 (利率敏感)
        "Real Estate", "REITs",
    ]
    
    # 宏观阈值
    MACRO_LOOSE_THRESHOLD = 3.0    # < 3.0% = 宽松
    MACRO_TIGHT_THRESHOLD = 4.5    # > 4.5% = 紧缩
    VIX_PANIC_THRESHOLD = 30       # > 30 = 市场恐慌

    def __init__(self, fmp_client: FMPClient, search_client: SearchClient):
        self.fmp = fmp_client
        self.search = search_client

    def _determine_macro_mode(self, us10y: Optional[float]) -> MacroMode:
        """
        根据 10 年期美债收益率确定宏观模式
        
        < 3.0%  -> Loose (宽松): 允许 PEG 1.5~2.0
        3.0-4.5% -> Neutral (中性): 严格 PEG < 1.5
        > 4.5%  -> Tight (紧缩): 强制 PEG < 1.0~1.2
        """
        if us10y is None:
            # 无法获取数据时，采用中性假设
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
        检查公司行业是否在白名单内
        
        Returns:
            (passed, reason): 是否通过检查，及原因
        """
        if not profile:
            return True, "Profile unavailable, assuming pass"
        
        sector = profile.get('sector', '')
        industry = profile.get('industry', '')
        
        # 检查黑名单
        for blacklisted in self.SECTOR_BLACKLIST:
            if blacklisted.lower() in sector.lower() or blacklisted.lower() in industry.lower():
                return False, f"Blacklisted sector/industry: {sector} / {industry}"
        
        # 检查是否在白名单 (宽松检查 - 只要不在黑名单即可)
        # 注: 严格模式可改为必须在白名单内
        return True, f"Sector: {sector}, Industry: {industry}"

    def analyze(self, ticker: str) -> GatekeeperData:
        """
        执行 V3.4 前置过滤分析
        
        Args:
            ticker: 股票代码
            
        Returns:
            GatekeeperData: 包含宏观状态、VIX、行业检查结果
        """
        print(f"  [Phase 0] Gatekeeper Analysis for {ticker}...")
        
        # ========== 1. 获取宏观数据 ==========
        print("    - Fetching macro data...")
        
        # 10Y 美债收益率 (通过 Tavily 搜索)
        us10y = self.search.get_treasury_yield()
        print(f"      US 10Y Treasury Yield: {us10y:.2f}%" if us10y else "      US 10Y Treasury Yield: N/A")
        
        # VIX 恐慌指数 (通过 FMP)
        vix = self.fmp.get_vix()
        print(f"      VIX: {vix:.2f}" if vix else "      VIX: N/A")
        
        # ========== 2. 判断宏观模式 ==========
        macro_mode = self._determine_macro_mode(us10y)
        print(f"      Macro Mode: {macro_mode.value}")
        
        # ========== 3. VIX 熔断检查 ==========
        vix_panic = vix is not None and vix > self.VIX_PANIC_THRESHOLD
        if vix_panic:
            print(f"      ⚠️ VIX PANIC MODE: VIX {vix:.2f} > {self.VIX_PANIC_THRESHOLD}")
            print("      禁止左侧买入，需等待股价站上 20 日均线")
        
        # ========== 4. 行业过滤 ==========
        print("    - Checking sector whitelist/blacklist...")
        profile = self.fmp.get_profile(ticker)
        sector_passed, sector_reason = self._check_sector(profile)
        print(f"      {sector_reason}")
        
        # ========== 5. 综合判断 ==========
        # 通过条件: 行业不在黑名单 (VIX 恐慌只是警告，不直接拒绝)
        passed = sector_passed
        fail_reason = None
        
        if not sector_passed:
            fail_reason = sector_reason
            print(f"    - Gatekeeper FAILED: {fail_reason}")
        elif vix_panic:
            # VIX 恐慌不直接拒绝，但会在后续 Tribunal 阶段影响评级
            print("    - Gatekeeper PASSED (with VIX Warning)")
        else:
            print(f"    - Gatekeeper PASSED for {ticker}")
        
        return GatekeeperData(
            sector_check_passed=sector_passed,
            macro_mode=macro_mode,
            us10y_yield=us10y,
            vix_value=vix,
            passed=passed,
            fail_reason=fail_reason
        )
