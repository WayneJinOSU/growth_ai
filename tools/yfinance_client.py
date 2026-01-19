"""
YFinance Client for MGP V3.7
============================
用于获取 Forward PE、PEG Ratio 等前瞻性估值数据。
这些数据在 FMP Starter 权限下不可用，但 yfinance 免费提供。
"""

import yfinance as yf
from typing import Optional, Dict, Any


class YFinanceClient:
    """
    YFinance 数据客户端

    主要用途:
    - 获取 Forward PE (前瞻性市盈率)
    - 获取 PEG Ratio (市盈增长比)
    - 获取财报日历 (Earnings Date)
    """

    def get_forward_pe(self, ticker: str) -> Optional[float]:
        """
        获取 Forward PE (前瞻性市盈率)

        V3.7 规则: Forward PE < 20x 触发买入信号

        Args:
            ticker: 股票代码

        Returns:
            float: Forward PE 值，获取失败返回 None
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            return info.get('forwardPE')
        except Exception as e:
            print(f"      [Warning] Failed to fetch Forward PE for {ticker}: {e}")
            return None

    def get_peg_ratio(self, ticker: str) -> Optional[float]:
        """
        获取 PEG Ratio (市盈增长比)

        V3.7 规则: PEG < 0.6 为加分项

        Args:
            ticker: 股票代码

        Returns:
            float: PEG Ratio 值，获取失败返回 None
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            return info.get('pegRatio')
        except Exception as e:
            print(f"      [Warning] Failed to fetch PEG Ratio for {ticker}: {e}")
            return None

    def get_trailing_pe(self, ticker: str) -> Optional[float]:
        """
        获取 Trailing PE (TTM 市盈率)

        用于 Historical PE Z-Score 备选方案

        Args:
            ticker: 股票代码

        Returns:
            float: Trailing PE 值，获取失败返回 None
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            return info.get('trailingPE')
        except Exception as e:
            print(f"      [Warning] Failed to fetch Trailing PE for {ticker}: {e}")
            return None

    def get_valuation_data(self, ticker: str) -> Dict[str, Any]:
        """
        一次性获取所有估值相关数据

        Returns:
            Dict: {
                'forward_pe': float | None,
                'trailing_pe': float | None,
                'peg_ratio': float | None,
                'price_to_book': float | None,
                'enterprise_to_ebitda': float | None,
            }
        """
        result = {
            'forward_pe': None,
            'trailing_pe': None,
            'peg_ratio': None,
            'price_to_book': None,
            'enterprise_to_ebitda': None,
        }

        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            result['forward_pe'] = info.get('forwardPE')
            result['trailing_pe'] = info.get('trailingPE')
            result['peg_ratio'] = info.get('pegRatio')
            result['price_to_book'] = info.get('priceToBook')
            result['enterprise_to_ebitda'] = info.get('enterpriseToEbitda')

        except Exception as e:
            print(f"      [Warning] Failed to fetch valuation data for {ticker}: {e}")

        return result

    def get_earnings_dates(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        获取财报日期信息

        用于 V3.7 "Kitchen Sink" 买点检测

        Args:
            ticker: 股票代码

        Returns:
            Dict: 包含最近财报日期信息
        """
        try:
            stock = yf.Ticker(ticker)
            # 获取财报日历
            calendar = stock.calendar
            if calendar is not None and not calendar.empty:
                return calendar.to_dict()
            return None
        except Exception as e:
            print(f"      [Warning] Failed to fetch earnings dates for {ticker}: {e}")
            return None

    def get_market_cap(self, ticker: str) -> Optional[float]:
        """
        获取市值

        V3.7 规则: 市值 > $50B

        Args:
            ticker: 股票代码

        Returns:
            float: 市值 (美元)，获取失败返回 None
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            return info.get('marketCap')
        except Exception as e:
            print(f"      [Warning] Failed to fetch Market Cap for {ticker}: {e}")
            return None


if __name__ == "__main__":
    client = YFinanceClient()

    # Test with NVO (Novo Nordisk)
    ticker = "NVO"
    print(f"Testing YFinance Client with {ticker}:")
    print(f"  Forward PE: {client.get_forward_pe(ticker)}")
    print(f"  PEG Ratio: {client.get_peg_ratio(ticker)}")
    print(f"  Market Cap: {client.get_market_cap(ticker)}")
    print(f"  Valuation Data: {client.get_valuation_data(ticker)}")
