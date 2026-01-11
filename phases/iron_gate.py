import numpy as np
from typing import List, Dict, Optional
from tools.fmp import FMPClient
from core.data_models import IronGateMetrics, CompanyData
import config


class IronGate:
    def __init__(self, fmp_client: FMPClient):
        self.fmp = fmp_client

    def _calculate_cagr(self, start_value: float, end_value: float, years: int) -> float:
        if start_value <= 0 or years <= 0:
            return 0.0
        return (end_value / start_value) ** (1 / years) - 1

    def _calculate_slope(self, values: List[float]) -> float:
        if len(values) < 2:
            return 0.0
        x = np.arange(len(values))
        y = np.array(values)
        slope, _ = np.polyfit(x, y, 1)
        return slope

    def analyze(self, ticker: str) -> IronGateMetrics:
        # 使用配置中的参数
        cagr_years = config.CAGR_YEARS
        quarters_for_decel = config.QUARTERS_FOR_DECEL_CHECK
        quarters_for_yoy = config.QUARTERS_FOR_YOY
        quarters_for_margin = config.QUARTERS_FOR_MARGIN_SLOPE
        quarters_for_ni = config.QUARTERS_FOR_NI_SUM

        # Fetch Data - 根据配置动态调整 limit
        income_annual = self.fmp.get_income_statement(ticker, period='annual', limit=cagr_years + 1)
        income_quarterly = self.fmp.get_income_statement(ticker, period='quarter', limit=quarters_for_decel)
        ratios_ttm = self.fmp.get_ratios_ttm(ticker)
        quote = self.fmp.get_quote(ticker)

        metrics = IronGateMetrics()

        if not income_annual or len(income_annual) < 2:
            metrics.passed = False
            metrics.fail_reason = "Insufficient annual data"
            return metrics

        # 1. CAGR 计算 (使用配置的年限)
        try:
            latest_rev = income_annual[0]['revenue']
            old_rev = income_annual[-1]['revenue']
            years = len(income_annual) - 1
            cagr = self._calculate_cagr(old_rev, latest_rev, years)
            metrics.revenue_cagr_5y = cagr  # 字段名保留兼容性
        except Exception as e:
            metrics.revenue_cagr_5y = 0.0

        # 2. Current Quarter Growth
        if not income_quarterly or len(income_quarterly) < quarters_for_yoy:
            metrics.passed = False
            metrics.fail_reason = f"Insufficient quarterly data (need {quarters_for_yoy})"
            return metrics

        try:
            # Q0 vs Q-4 (同比)
            current_rev = income_quarterly[0]['revenue']
            prev_year_q_rev = income_quarterly[quarters_for_yoy - 1]['revenue']
            current_growth = (current_rev - prev_year_q_rev) / prev_year_q_rev
            metrics.revenue_growth_current_q = current_growth

            # 3. Deceleration Alarm - Q-4 vs Q-8
            decel_index = quarters_for_decel - 1  # Q-8 的索引
            prev_rev = income_quarterly[quarters_for_yoy - 1]['revenue']
            prev_prev_rev = income_quarterly[decel_index]['revenue'] if len(income_quarterly) > decel_index else 0

            if prev_prev_rev > 0:
                prev_growth = (prev_rev - prev_prev_rev) / prev_prev_rev
                metrics.revenue_growth_prev_y_q = prev_growth
            else:
                metrics.revenue_growth_prev_y_q = current_growth
        except Exception as e:
            metrics.passed = False
            metrics.fail_reason = f"Data Error: {str(e)}"
            return metrics

        # 使用配置的阈值检查
        if (metrics.revenue_cagr_5y < config.GROWTH_THRESHOLD_CAGR) and \
                (metrics.revenue_growth_current_q < config.GROWTH_THRESHOLD_QUARTER):
            metrics.passed = False
            metrics.fail_reason = f"Low Growth: CAGR {metrics.revenue_cagr_5y:.1%}, Q_Growth {metrics.revenue_growth_current_q:.1%}"
            return metrics

        # Deceleration Check - 使用配置的阈值
        if metrics.revenue_growth_prev_y_q and metrics.revenue_growth_prev_y_q > config.DECEL_PREV_GROWTH_THRESHOLD:
            if metrics.revenue_growth_current_q < (metrics.revenue_growth_prev_y_q * config.DECEL_DROP_RATIO):
                metrics.passed = False
                metrics.fail_reason = f"Deceleration Alarm: {metrics.revenue_growth_prev_y_q:.1%} -> {metrics.revenue_growth_current_q:.1%}"
                return metrics

        # 4. Profitability Bifurcation
        is_profitable = False
        if ratios_ttm and ratios_ttm.get('netProfitMarginTTM', 0) > 0:
            is_profitable = True

        # 使用配置的季度数计算 TTM 净利润
        total_ni = sum(q['netIncome'] for q in income_quarterly[:quarters_for_ni])
        if total_ni > 0:
            is_profitable = True

        if is_profitable:
            pe = ratios_ttm.get('peRatioTTM') if ratios_ttm else None
            if pe is None:
                eps = sum(q['eps'] for q in income_quarterly[:quarters_for_ni])
                price = quote.get('price') if quote else 0
                if eps > 0 and price > 0:
                    pe = price / eps

            growth_rate = metrics.revenue_growth_current_q * 100
            peg = ratios_ttm.get('pegRatioTTM') if ratios_ttm else None

            if not peg and pe and growth_rate > 0:
                peg = pe / growth_rate

            metrics.peg_ratio = peg

            # 使用配置的 PEG 阈值
            if peg and peg > config.PEG_THRESHOLD_BUBBLE:
                metrics.passed = False
                metrics.fail_reason = f"PEG too high: {peg:.2f} (threshold: {config.PEG_THRESHOLD_BUBBLE})"
                return metrics
        else:
            # 毛利斜率 - 使用配置的季度数
            margins = []
            for q in reversed(income_quarterly[:quarters_for_margin]):
                if q['revenue'] > 0:
                    gm = q['grossProfit'] / q['revenue']
                    margins.append(gm)

            slope = self._calculate_slope(margins)
            metrics.gross_margin_slope = slope

            # 使用配置的毛利斜率容忍度
            if slope < config.GROSS_MARGIN_SLOPE_TOLERANCE:
                metrics.passed = False
                metrics.fail_reason = f"Gross Margin Declining (Slope: {slope:.4f})"
                return metrics

            # Operating Leverage - Q0 vs Q-4
            curr_opex = income_quarterly[0]['operatingExpenses']
            old_opex = income_quarterly[quarters_for_yoy - 1]['operatingExpenses']
            opex_growth = (curr_opex - old_opex) / old_opex if old_opex > 0 else 0

            metrics.opex_growth = opex_growth
            metrics.operating_leverage = metrics.revenue_growth_current_q > opex_growth

            if not metrics.operating_leverage:
                metrics.passed = False
                metrics.fail_reason = f"No Operating Leverage: Rev {metrics.revenue_growth_current_q:.1%} < OpEx {opex_growth:.1%}"
                return metrics

        metrics.passed = True
        return metrics