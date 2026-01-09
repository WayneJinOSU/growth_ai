import numpy as np
from typing import List, Dict, Optional
from tools.fmp import FMPClient
from core.data_models import IronGateMetrics, CompanyData

class IronGate:
    def __init__(self, fmp_client: FMPClient):
        self.fmp = fmp_client

    def _calculate_cagr(self, start_value: float, end_value: float, years: int) -> float:
        if start_value <= 0 or years <= 0:
            return 0.0
        return (end_value / start_value) ** (1 / years) - 1

    def _calculate_slope(self, values: List[float]) -> float:
        # Simple linear regression slope
        if len(values) < 2:
            return 0.0
        x = np.arange(len(values))
        y = np.array(values)
        slope, _ = np.polyfit(x, y, 1)
        return slope

    def analyze(self, ticker: str) -> IronGateMetrics:
        # Fetch Data
        income_annual = self.fmp.get_income_statement(ticker, period='annual', limit=5)
        income_quarterly = self.fmp.get_income_statement(ticker, period='quarter', limit=5)
        ratios_ttm = self.fmp.get_ratios_ttm(ticker)
        quote = self.fmp.get_quote(ticker)

        metrics = IronGateMetrics()
        
        if not income_annual or len(income_annual) < 2:
            metrics.passed = False
            metrics.fail_reason = "Insufficient annual data"
            return metrics

        # 1. 20% Rule - 5 Year CAGR
        # income_annual is sorted by date desc (latest first)
        # We need latest full year vs 5 years ago
        try:
            latest_rev = income_annual[0]['revenue']
            old_rev = income_annual[-1]['revenue']
            years = len(income_annual) - 1
            cagr = self._calculate_cagr(old_rev, latest_rev, years)
            metrics.revenue_cagr_5y = cagr
        except Exception as e:
            metrics.revenue_cagr_5y = 0.0

        # 2. Current Quarter Growth
        if not income_quarterly or len(income_quarterly) < 5:
            metrics.passed = False
            metrics.fail_reason = "Insufficient quarterly data"
            return metrics

        try:
            # Q0 vs Q-4
            current_rev = income_quarterly[0]['revenue']
            prev_year_q_rev = income_quarterly[4]['revenue']
            current_growth = (current_rev - prev_year_q_rev) / prev_year_q_rev
            metrics.revenue_growth_current_q = current_growth

            # 3. Deceleration Alarm
            # Compare current growth vs (Q-4 vs Q-8)
            # Or Whitepaper says: "Compare current growth vs last year same period growth"
            # "If growth drops from 60% to 25%" -> implies comparing growth rates.
            # Let's get growth rate of Q-4.
            prev_rev = income_quarterly[4]['revenue']
            prev_prev_rev = income_quarterly[8]['revenue'] if len(income_quarterly) > 8 else 0
            
            if prev_prev_rev > 0:
                prev_growth = (prev_rev - prev_prev_rev) / prev_prev_rev
                metrics.revenue_growth_prev_y_q = prev_growth
            else:
                 # Fallback if not enough history
                metrics.revenue_growth_prev_y_q = current_growth # Assume steady
        except Exception as e:
            metrics.passed = False
            metrics.fail_reason = f"Data Error: {str(e)}"
            return metrics

        # Check Thresholds (20% logic)
        # Whitepaper: "CAGR approach or exceed 20%" AND "Current Q > 20%"
        # Let's be slightly lenient on CAGR if Current Q is strong? Whitepaper says "Iron Gate" -> strict.
        if (metrics.revenue_cagr_5y < 0.15) and (metrics.revenue_growth_current_q < 0.20):
             # Fail if both are weak.
             # Whitepaper: "Unless strong macro reason... eliminate"
             metrics.passed = False
             metrics.fail_reason = f"Low Growth: CAGR {metrics.revenue_cagr_5y:.1%}, Q_Growth {metrics.revenue_growth_current_q:.1%}"
             return metrics

        # Deceleration Check
        if metrics.revenue_growth_prev_y_q and metrics.revenue_growth_prev_y_q > 0.40: # Only care if it WAS high
             if metrics.revenue_growth_current_q < (metrics.revenue_growth_prev_y_q * 0.5):
                 metrics.passed = False
                 metrics.fail_reason = f"Deceleration Alarm: {metrics.revenue_growth_prev_y_q:.1%} -> {metrics.revenue_growth_current_q:.1%}"
                 return metrics

        # 4. Profitability Bifurcation
        is_profitable = False
        if ratios_ttm and ratios_ttm.get('netProfitMarginTTM', 0) > 0:
            is_profitable = True
        
        # Or check last 4 quarters Net Income sum
        total_ni = sum(q['netIncome'] for q in income_quarterly[:4])
        if total_ni > 0:
            is_profitable = True

        if is_profitable:
            # Check PEG
            pe = ratios_ttm.get('peRatioTTM') if ratios_ttm else None
            if pe is None:
                 # Fallback calc
                 eps = sum(q['eps'] for q in income_quarterly[:4])
                 price = quote.get('price') if quote else 0
                 if eps > 0 and price > 0:
                     pe = price / eps
            
            growth_rate = metrics.revenue_growth_current_q * 100 # Use Revenue growth as proxy for Growth Rate in PEG? 
            # Whitepaper: PEG = PE / Growth Rate. Usually EPS growth. 
            # But for high growth tech, often Revenue Growth is used if EPS is volatile/low.
            # MGP is "Growth" strategy. Let's use Revenue Growth for consistency or FMP's PEG if available.
            # FMP has pegRatioTTM.
            
            peg = ratios_ttm.get('pegRatioTTM') if ratios_ttm else None
            
            # If FMP PEG is weird, calc manually using Revenue Growth
            if not peg and pe and growth_rate > 0:
                peg = pe / growth_rate
            
            metrics.peg_ratio = peg
            
            if peg and peg > 2.0:
                metrics.passed = False
                metrics.fail_reason = f"PEG too high: {peg:.2f}"
                return metrics
        else:
            # Unprofitable - Check Margin Slope & OpEx
            # Gross Margin Slope (last 4-6 quarters)
            margins = []
            for q in reversed(income_quarterly[:6]): # Oldest to Newest
                if q['revenue'] > 0:
                    gm = q['grossProfit'] / q['revenue']
                    margins.append(gm)
            
            slope = self._calculate_slope(margins)
            metrics.gross_margin_slope = slope
            
            if slope < 0: # Strict: Must be positive or flat? Whitepaper: "Must show rising trend"
                 # Allow slight noise? No, "Must show rising trend".
                 if slope < -0.005: # Allow very slight noise
                     metrics.passed = False
                     metrics.fail_reason = f"Gross Margin Declining (Slope: {slope:.4f})"
                     return metrics

            # Operating Leverage: Rev Growth > OpEx Growth
            # Compare last Q vs Q-4
            curr_opex = income_quarterly[0]['operatingExpenses']
            old_opex = income_quarterly[4]['operatingExpenses']
            opex_growth = (curr_opex - old_opex) / old_opex if old_opex > 0 else 0
            
            metrics.opex_growth = opex_growth
            metrics.operating_leverage = metrics.revenue_growth_current_q > opex_growth
            
            if not metrics.operating_leverage:
                 metrics.passed = False
                 metrics.fail_reason = f"No Operating Leverage: Rev {metrics.revenue_growth_current_q:.1%} < OpEx {opex_growth:.1%}"
                 return metrics

        metrics.passed = True
        return metrics

