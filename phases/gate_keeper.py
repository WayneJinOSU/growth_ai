"""
Phase 0: The Pedigree Check (血统验证) - V3.7 Armored Sniper
============================================================
在深入分析前，先确认标的"配不配"使用本系统。

V3.7 核心检查项:
1. 规模门槛 - 市值 > $50B (确保流动性与抗风险能力)
2. 赢家历史 - 过去 5-10 年的行业老大或双寡头
3. 行业白/黑名单 - 通过 FMP sector 字段进行硬过滤
4. 困境性质 - 必须是内生且可控的 (非地缘政治/商业模式被取缔)
"""

from typing import Optional, Dict, List
from tools.fmp import FMPClient
from tools.search import SearchClient
from tools.yfinance_client import YFinanceClient
from core.data_models import GatekeeperData, PedigreeData, MacroMode


class Gatekeeper:
    """
    V3.7 血统验证器：MGP 策略的第零道关卡 (Pedigree Check)

    职责：
    - 验证市值门槛 (> $50B)
    - 验证行业白/黑名单
    - 验证赢家历史 (10yr Revenue CAGR)
    - 获取宏观数据 (美债收益率、VIX)
    """

    # V3.7 行业白名单 - 技术壁垒高，需求刚性，转换成本高
    SECTOR_WHITELIST = [
        # 医药 (NVO)
        "Healthcare", "Biotechnology", "Pharmaceuticals",
        # 半导体 (NVDA)
        "Semiconductors", "Semiconductor Equipment",
        # 软件 (MSFT)
        "Technology", "Software", "Software—Infrastructure", "Software—Application",
        "Information Technology", "IT Services",
        # 通信服务
        "Communication Services",
        # 工业科技
        "Industrials", "Aerospace & Defense",
        # 顶级消费 (Hermes 级别)
        "Consumer Defensive",
    ]

    # V3.7 行业黑名单 - 资产负债表不透明，或受制于宏观/政策
    SECTOR_BLACKLIST = [
        # 银行 - 资产负债表黑箱
        "Financial Services", "Banks", "Regional Banks", "Insurance",
        # 能源 - 受制于宏观
        "Energy", "Oil & Gas", "Oil & Gas E&P", "Oil & Gas Integrated",
        # 公用事业 - 受制于政策
        "Utilities",
        # 低毛利制造
        "Basic Materials", "Mining", "Steel",
        # 房地产 - 利率敏感
        "Real Estate", "REITs",
        # 纯周期消费
        "Consumer Cyclical", "Apparel", "Footwear", "Restaurants", "Leisure",
    ]

    # 市值门槛 (V3.7)
    MARKET_CAP_THRESHOLD = 50_000_000_000  # $50B

    # 宏观阈值
    MACRO_LOOSE_THRESHOLD = 3.0  # < 3.0% = 宽松
    MACRO_TIGHT_THRESHOLD = 4.5  # > 4.5% = 紧缩
    VIX_PANIC_THRESHOLD = 30  # > 30 = 市场恐慌

    def __init__(self, fmp_client: FMPClient, search_client: SearchClient = None, yf_client: YFinanceClient = None):
        self.fmp = fmp_client
        self.search = search_client
        self.yf = yf_client or YFinanceClient()

    def _calculate_cagr(self, start_value: float, end_value: float, years: int) -> float:
        """计算复合年均增长率 (CAGR)"""
        if start_value <= 0 or years <= 0:
            return 0.0
        return (end_value / start_value) ** (1 / years) - 1

    def _check_market_cap(self, ticker: str, profile: Optional[Dict]) -> tuple[bool, float]:
        """
        检查市值门槛

        V3.7 规则: 市值 > $50B

        Returns:
            (passed, market_cap)
        """
        market_cap = None

        # 优先使用 FMP Profile
        if profile:
            market_cap = profile.get('mktCap')

        # 备选: 使用 yfinance
        if not market_cap:
            market_cap = self.yf.get_market_cap(ticker)

        if not market_cap:
            return False, 0

        passed = market_cap >= self.MARKET_CAP_THRESHOLD
        return passed, market_cap

    def _check_sector(self, profile: Optional[Dict]) -> tuple[bool, str, str]:
        """
        检查行业白/黑名单

        V3.7 规则: 必须不在黑名单，优先白名单

        Returns:
            (passed, sector, industry)
        """
        if not profile:
            return True, "Unknown", "Unknown"

        sector = profile.get('sector', '')
        industry = profile.get('industry', '')

        # 检查黑名单 (硬拒绝)
        for blacklisted in self.SECTOR_BLACKLIST:
            if blacklisted.lower() in sector.lower() or blacklisted.lower() in industry.lower():
                return False, sector, industry

        # 检查白名单 (V3.7: 不在黑名单即可通过，白名单为加分项)
        return True, sector, industry

    def _check_winner_history(self, ticker: str, years: int = 10) -> tuple[bool, Optional[float]]:
        """
        检查赢家历史

        V3.7 规则: 过去 5-10 年的行业老大或双寡头
        通过 10yr Revenue CAGR 验证

        Returns:
            (is_winner, cagr)
        """
        # 获取年度利润表 (尽可能多年)
        income_annual = self.fmp.get_income_statement(ticker, period='annual', limit=years + 1)

        if not income_annual or len(income_annual) < 3:
            # 数据不足，无法验证
            return True, None  # 给予通过，后续阶段再验证

        try:
            latest_rev = income_annual[0].get('revenue', 0)
            oldest_rev = income_annual[-1].get('revenue', 0)
            actual_years = len(income_annual) - 1

            if oldest_rev <= 0:
                return True, None

            cagr = self._calculate_cagr(oldest_rev, latest_rev, actual_years)

            # V3.7: 对于大市值股票，只要有正 CAGR 就认为是赢家
            # (因为能维持 $50B+ 市值本身就证明了竞争力)
            is_winner = cagr > 0

            return is_winner, cagr
        except Exception:
            return True, None

    def _determine_macro_mode(self, us10y: Optional[float]) -> MacroMode:
        """
        根据 10 年期美债收益率确定宏观模式

        < 3.0%  -> Loose (宽松)
        3.0-4.5% -> Neutral (中性)
        > 4.5%  -> Tight (紧缩)
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

    def analyze(self, ticker: str) -> GatekeeperData:
        """
        执行 V3.7 血统验证 (Pedigree Check)

        Args:
            ticker: 股票代码

        Returns:
            GatekeeperData: 包含血统验证结果和宏观状态
        """
        print(f"  [Phase 0] Pedigree Check for {ticker}...")

        # 初始化 Pedigree 数据
        pedigree = PedigreeData()

        # ========== 1. 获取公司档案 ==========
        print("    - Fetching company profile...")
        profile = self.fmp.get_profile(ticker)

        # ========== 2. 市值门槛检查 ==========
        print("    - Checking market cap threshold...")
        market_cap_passed, market_cap = self._check_market_cap(ticker, profile)
        pedigree.market_cap = market_cap
        pedigree.market_cap_passed = market_cap_passed

        market_cap_b = market_cap / 1_000_000_000 if market_cap else 0
        print(f"      Market Cap: ${market_cap_b:.1f}B (Threshold: $50B) -> {'PASS' if market_cap_passed else 'FAIL'}")

        if not market_cap_passed:
            pedigree.passed = False
            pedigree.fail_reason = f"Market cap ${market_cap_b:.1f}B < $50B threshold"
            return GatekeeperData(
                pedigree=pedigree,
                sector_check_passed=False,
                passed=False,
                fail_reason=pedigree.fail_reason
            )

        # ========== 3. 行业白/黑名单检查 ==========
        print("    - Checking sector whitelist/blacklist...")
        sector_passed, sector, industry = self._check_sector(profile)
        pedigree.sector = sector
        pedigree.industry = industry
        pedigree.sector_passed = sector_passed

        print(f"      Sector: {sector}, Industry: {industry} -> {'PASS' if sector_passed else 'BLACKLISTED'}")

        if not sector_passed:
            pedigree.passed = False
            pedigree.fail_reason = f"Blacklisted sector/industry: {sector} / {industry}"
            return GatekeeperData(
                pedigree=pedigree,
                sector_check_passed=False,
                passed=False,
                fail_reason=pedigree.fail_reason
            )

        # ========== 4. 赢家历史检查 ==========
        print("    - Checking winner history (10yr CAGR)...")
        is_winner, cagr_10y = self._check_winner_history(ticker)
        pedigree.revenue_cagr_10y = cagr_10y
        pedigree.is_industry_winner = is_winner

        if cagr_10y is not None:
            print(f"      10yr Revenue CAGR: {cagr_10y:.1%} -> {'WINNER' if is_winner else 'DECLINING'}")
        else:
            print("      10yr Revenue CAGR: N/A (insufficient data)")

        # ========== 5. 宏观数据 ==========
        print("    - Fetching macro data...")

        # 10Y 美债收益率 (通过 Tavily 搜索)
        us10y = None
        if self.search:
            us10y = self.search.get_treasury_yield()
        print(f"      US 10Y Treasury Yield: {us10y:.2f}%" if us10y else "      US 10Y Treasury Yield: N/A")

        # VIX 恐慌指数 (通过 FMP)
        vix = self.fmp.get_vix()
        print(f"      VIX: {vix:.2f}" if vix else "      VIX: N/A")

        # 判断宏观模式
        macro_mode = self._determine_macro_mode(us10y)
        print(f"      Macro Mode: {macro_mode.value}")

        # VIX 恐慌检查 (警告，不直接拒绝)
        vix_panic = vix is not None and vix > self.VIX_PANIC_THRESHOLD
        if vix_panic:
            print(f"      ⚠️ VIX PANIC MODE: VIX {vix:.2f} > {self.VIX_PANIC_THRESHOLD}")
            print("      禁止左侧买入，需等待股价站上 20 日均线")

        # ========== 6. 综合判断 ==========
        pedigree.passed = market_cap_passed and sector_passed

        if pedigree.passed:
            print(f"    - Pedigree Check PASSED for {ticker}")
        else:
            print(f"    - Pedigree Check FAILED: {pedigree.fail_reason}")

        return GatekeeperData(
            pedigree=pedigree,
            sector_check_passed=sector_passed,
            macro_mode=macro_mode,
            us10y_yield=us10y,
            vix_value=vix,
            passed=pedigree.passed,
            fail_reason=pedigree.fail_reason
        )
