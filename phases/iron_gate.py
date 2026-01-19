"""
Phase 2: Financial Armor (财务装甲) - V3.7 Armored Sniper
=========================================================
确保在黎明到来前，公司不会死于失血。

V3.7 铁律:
1. 毛利率熔断 - 同比下降 < 300bps (3%)
2. 债务窒息线 - Net Debt / EBITDA < 3.0x (或现金跑道 > 24个月)
3. 稀释墙 - SBC 年稀释率 < 3%

数据源: FMP Financial Statements
"""

import numpy as np
from typing import List, Optional
from tools.fmp import FMPClient
from tools.yfinance_client import YFinanceClient
from core.data_models import IronGateMetrics


class IronGate:
    """
    V3.7 财务装甲：MGP 策略的第二道关卡
    
    职责：
    - 毛利率安全检查
    - 债务健康检查
    - 股权稀释检查
    """
    
    # V3.7 铁律阈值
    GROSS_MARGIN_MAX_DROP_BPS = 300  # 300 基点 = 3%
    NET_DEBT_EBITDA_MAX = 3.0
    CASH_RUNWAY_MIN_MONTHS = 24
    SBC_DILUTION_MAX = 0.03  # 3%

    def __init__(self, fmp_client: FMPClient, yf_client: YFinanceClient = None):
        self.fmp = fmp_client
        self.yf = yf_client or YFinanceClient()

    def _calculate_cagr(self, start_value: float, end_value: float, years: int) -> float:
        """计算复合年均增长率"""
        if start_value <= 0 or years <= 0:
            return 0.0
        return (end_value / start_value) ** (1 / years) - 1

    def _calculate_slope(self, values: List[float]) -> float:
        """计算数据序列的线性回归斜率"""
        if len(values) < 2:
            return 0.0
        x = np.arange(len(values))
        y = np.array(values)
        slope, _ = np.polyfit(x, y, 1)
        return slope

    def _check_gross_margin_safety(self, income_annual: List[dict]) -> tuple[bool, Optional[float], Optional[float], Optional[float]]:
        """
        毛利率熔断检查
        
        V3.7 铁律: 同比下降 < 300bps (3%)
        
        Returns:
            (is_safe, current_gm, prev_gm, change_bps)
        """
        if not income_annual or len(income_annual) < 2:
            return True, None, None, None
        
        try:
            # 当前年度
            rev_current = income_annual[0].get('revenue', 0)
            gp_current = income_annual[0].get('grossProfit', 0)
            gm_current = gp_current / rev_current if rev_current > 0 else None
            
            # 去年
            rev_prev = income_annual[1].get('revenue', 0)
            gp_prev = income_annual[1].get('grossProfit', 0)
            gm_prev = gp_prev / rev_prev if rev_prev > 0 else None
            
            if gm_current is None or gm_prev is None:
                return True, gm_current, gm_prev, None
            
            # 变化 (基点)
            change_bps = (gm_current - gm_prev) * 10000
            is_safe = change_bps >= -self.GROSS_MARGIN_MAX_DROP_BPS
            
            return is_safe, gm_current, gm_prev, change_bps
        except Exception as e:
            print(f"      [Warning] Gross margin check failed: {e}")
            return True, None, None, None

    def _check_debt_safety(self, ticker: str, balance_sheet: List[dict], cashflow: List[dict]) -> tuple[bool, Optional[float], Optional[float], Optional[float], Optional[float]]:
        """
        债务窒息线检查
        
        V3.7 铁律:
        - 主要: Net Debt / EBITDA < 3.0x
        - 备选: 现金跑道 > 24 个月
        
        Returns:
            (is_safe, net_debt, ebitda, net_debt_to_ebitda, cash_runway_months)
        """
        if not balance_sheet:
            return True, None, None, None, None
        
        try:
            # 获取最新资产负债表数据
            bs = balance_sheet[0]
            
            # 计算 Net Debt = Total Debt - Cash
            total_debt = bs.get('totalDebt', 0) or 0
            cash = bs.get('cashAndCashEquivalents', 0) or bs.get('cashAndShortTermInvestments', 0) or 0
            net_debt = total_debt - cash
            
            # 获取 EBITDA (从 Enterprise Values 或计算)
            # 备选: 从 Key Metrics 获取
            key_metrics = self.fmp.get_key_metrics(ticker, period='annual', limit=1)
            ebitda = None
            if key_metrics:
                ebitda = key_metrics[0].get('ebitda')
            
            # 如果没有 EBITDA，尝试计算
            if not ebitda and cashflow:
                # EBITDA ≈ Operating Cash Flow + Interest + Taxes - CapEx changes
                # 简化计算: 使用 Operating Income + D&A
                income = self.fmp.get_income_statement(ticker, period='annual', limit=1)
                if income:
                    operating_income = income[0].get('operatingIncome', 0) or 0
                    # D&A 从现金流量表获取
                    da = cashflow[0].get('depreciationAndAmortization', 0) or 0
                    ebitda = operating_income + da
            
            # 计算 Net Debt / EBITDA
            net_debt_to_ebitda = None
            if ebitda and ebitda > 0:
                net_debt_to_ebitda = net_debt / ebitda
            
            # 计算现金跑道 (备选)
            cash_runway_months = None
            if cashflow and cash > 0:
                # 使用最近的自由现金流
                fcf = cashflow[0].get('freeCashFlow', 0) or 0
                if fcf < 0:  # 烧钱状态
                    monthly_burn = abs(fcf) / 12
                    cash_runway_months = cash / monthly_burn if monthly_burn > 0 else float('inf')
                else:
                    cash_runway_months = float('inf')  # 不烧钱
            
            # 判断是否安全
            is_safe = True
            
            # 主要检查: Net Debt / EBITDA
            if net_debt_to_ebitda is not None:
                if net_debt_to_ebitda > self.NET_DEBT_EBITDA_MAX:
                    # 检查备选: 现金跑道
                    if cash_runway_months is not None and cash_runway_months >= self.CASH_RUNWAY_MIN_MONTHS:
                        is_safe = True  # 备选通过
                    else:
                        is_safe = False
            
            return is_safe, net_debt, ebitda, net_debt_to_ebitda, cash_runway_months
        except Exception as e:
            print(f"      [Warning] Debt safety check failed: {e}")
            return True, None, None, None, None

    def _check_dilution_safety(self, ticker: str, cashflow: List[dict], market_cap: Optional[float]) -> tuple[bool, Optional[float], Optional[float], Optional[float]]:
        """
        稀释墙检查
        
        V3.7 铁律: SBC 年稀释率 < 3%
        
        Returns:
            (is_safe, sbc_annual, market_cap, dilution_rate)
        """
        if not cashflow:
            return True, None, market_cap, None
        
        try:
            # 获取年度 SBC
            sbc_annual = cashflow[0].get('stockBasedCompensation', 0) or 0
            
            # 获取市值 (如果未提供)
            if not market_cap:
                market_cap = self.yf.get_market_cap(ticker)
            
            if not market_cap or market_cap <= 0:
                return True, sbc_annual, market_cap, None
            
            # 计算稀释率
            dilution_rate = sbc_annual / market_cap
            is_safe = dilution_rate <= self.SBC_DILUTION_MAX
            
            return is_safe, sbc_annual, market_cap, dilution_rate
        except Exception as e:
            print(f"      [Warning] Dilution safety check failed: {e}")
            return True, None, market_cap, None

    def analyze(self, ticker: str, market_cap: Optional[float] = None) -> IronGateMetrics:
        """
        执行 V3.7 财务装甲分析
        
        Args:
            ticker: 股票代码
            market_cap: 市值 (可选，来自 Gatekeeper)
            
        Returns:
            IronGateMetrics: 包含所有财务装甲指标
        """
        print(f"  [Phase 2] Financial Armor Analysis for {ticker}...")
        
        metrics = IronGateMetrics()
        
        # ========== 获取财务数据 ==========
        print("    - Fetching financial data...")
        income_annual = self.fmp.get_income_statement(ticker, period='annual', limit=5)
        income_quarterly = self.fmp.get_income_statement(ticker, period='quarter', limit=9)
        balance_annual = self.fmp.get_balance_sheet(ticker, period='annual', limit=3)
        cashflow_annual = self.fmp.get_cash_flow_statement(ticker, period='annual', limit=3)
        cashflow_quarterly = self.fmp.get_cash_flow_statement(ticker, period='quarter', limit=4)
        
        # ========== 1. 毛利率熔断 ==========
        print("    - Iron Rule #1: Gross Margin Safety...")
        gm_safe, gm_current, gm_prev, gm_change_bps = self._check_gross_margin_safety(income_annual)
        
        metrics.gross_margin_current = gm_current
        metrics.gross_margin_prev_year = gm_prev
        metrics.gross_margin_yoy_change_bps = gm_change_bps
        metrics.gross_margin_safe = gm_safe
        
        if gm_change_bps is not None:
            print(f"      Current GM: {gm_current:.1%} | Prev Year: {gm_prev:.1%} | Change: {gm_change_bps:+.0f} bps")
            print(f"      Result: {'SAFE' if gm_safe else 'FAILED (>300bps drop)'}")
        else:
            print("      N/A (insufficient data)")
        
        # ========== 2. 债务窒息线 ==========
        print("    - Iron Rule #2: Debt Safety...")
        debt_safe, net_debt, ebitda, nd_ebitda, runway = self._check_debt_safety(ticker, balance_annual, cashflow_annual)
        
        metrics.net_debt = net_debt
        metrics.ebitda = ebitda
        metrics.net_debt_to_ebitda = nd_ebitda
        metrics.cash_runway_months = runway
        metrics.debt_safe = debt_safe
        
        if nd_ebitda is not None:
            print(f"      Net Debt: ${net_debt/1e9:.1f}B | EBITDA: ${ebitda/1e9:.1f}B | Ratio: {nd_ebitda:.2f}x")
        if runway is not None and runway != float('inf'):
            print(f"      Cash Runway: {runway:.0f} months")
        print(f"      Result: {'SAFE' if debt_safe else 'FAILED (debt too high)'}")
        
        # ========== 3. 稀释墙 ==========
        print("    - Iron Rule #3: Dilution Safety...")
        dilution_safe, sbc, mkt_cap, dilution_rate = self._check_dilution_safety(ticker, cashflow_annual, market_cap)
        
        metrics.sbc_annual = sbc
        metrics.market_cap = mkt_cap
        metrics.sbc_dilution_rate = dilution_rate
        metrics.dilution_safe = dilution_safe
        
        if dilution_rate is not None:
            print(f"      Annual SBC: ${sbc/1e6:.0f}M | Market Cap: ${mkt_cap/1e9:.1f}B | Dilution: {dilution_rate:.2%}")
            print(f"      Result: {'SAFE' if dilution_safe else 'FAILED (>3% dilution)'}")
        else:
            print("      N/A (insufficient data)")
        
        # ========== Legacy Metrics (保留兼容性) ==========
        print("    - Computing legacy metrics...")
        self._compute_legacy_metrics(ticker, metrics, income_annual, income_quarterly, cashflow_quarterly)
        
        # ========== 综合判断 ==========
        all_safe = metrics.gross_margin_safe and metrics.debt_safe and metrics.dilution_safe
        
        if not all_safe:
            fail_reasons = []
            if not metrics.gross_margin_safe:
                fail_reasons.append(f"Gross margin dropped {abs(gm_change_bps):.0f}bps (>300bps)")
            if not metrics.debt_safe:
                fail_reasons.append(f"Net Debt/EBITDA {nd_ebitda:.1f}x (>3.0x)")
            if not metrics.dilution_safe:
                fail_reasons.append(f"SBC dilution {dilution_rate:.1%} (>3%)")
            metrics.fail_reason = "; ".join(fail_reasons)
            metrics.passed = False
            print(f"    - Financial Armor FAILED: {metrics.fail_reason}")
        else:
            metrics.passed = True
            print(f"    - Financial Armor PASSED for {ticker}")
        
        return metrics

    def _compute_legacy_metrics(self, ticker: str, metrics: IronGateMetrics, 
                                 income_annual: List[dict], income_quarterly: List[dict],
                                 cashflow_quarterly: List[dict]):
        """计算 V3.4 兼容的 legacy metrics"""
        
        # CAGR
        if income_annual and len(income_annual) >= 3:
            try:
                latest_rev = income_annual[0].get('revenue', 0)
                old_rev = income_annual[-1].get('revenue', 0)
                years = len(income_annual) - 1
                if old_rev > 0:
                    metrics.revenue_cagr_ny = self._calculate_cagr(old_rev, latest_rev, years)
                    print(f"      Revenue CAGR ({years}y): {metrics.revenue_cagr_ny:.1%}")
            except Exception:
                pass
        
        # 季度同比增速
        if income_quarterly and len(income_quarterly) >= 5:
            try:
                current_rev = income_quarterly[0].get('revenue', 0)
                prev_year_q_rev = income_quarterly[4].get('revenue', 0)
                if prev_year_q_rev > 0:
                    metrics.revenue_growth_current_q = (current_rev - prev_year_q_rev) / prev_year_q_rev
                    print(f"      Current Q YoY Growth: {metrics.revenue_growth_current_q:.1%}")
            except Exception:
                pass
        
        # SBC/Revenue Ratio
        if cashflow_quarterly and income_quarterly and len(cashflow_quarterly) >= 4 and len(income_quarterly) >= 4:
            try:
                sbc_sum = sum(q.get('stockBasedCompensation', 0) or 0 for q in cashflow_quarterly[:4])
                rev_sum = sum(q.get('revenue', 0) or 0 for q in income_quarterly[:4])
                if rev_sum > 0:
                    metrics.sbc_revenue_ratio = sbc_sum / rev_sum
                    print(f"      SBC/Revenue Ratio (TTM): {metrics.sbc_revenue_ratio:.1%}")
            except Exception:
                pass
        
        # Dilution Shield 设为 V3.7 的 dilution_safe
        metrics.dilution_shield_passed = metrics.dilution_safe
