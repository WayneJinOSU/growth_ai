import requests
from typing import Dict, List, Optional, Any
import config


class FMPClient:
    def __init__(self):
        self.api_key = config.FMP_API_KEY
        # 切换到更稳定的 stable 路径
        self.base_url = "https://financialmodelingprep.com/stable"
        # Historical price sometimes needs v3
        self.v3_url = "https://financialmodelingprep.com/api/v3"

    def _get(self, endpoint: str, params: Optional[Dict] = None, use_v3: bool = False) -> Any:
        if not self.api_key:
            raise ValueError("FMP_API_KEY is not set")

        # 修复可变默认参数问题
        if params is None:
            params = {}
        else:
            # 拷贝一份，避免修改外部传入的字典
            params = params.copy()

        base = self.v3_url if use_v3 else self.base_url
        url = f"{base}/{endpoint}"
        params['apikey'] = self.api_key

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            if isinstance(data, list) and len(data) == 0:
                return None
            
            # Handle FMP error responses in dict
            if isinstance(data, dict) and "Error Message" in data:
                print(f"FMP API Error for {endpoint}: {data['Error Message']}")
                return None
                
            return data
        except Exception as e:
            print(f"Error fetching {endpoint}: {e}")
            return None

    def get_quote(self, ticker: str) -> Optional[Dict]:
        # 统一使用 ?symbol= 格式
        data = self._get("quote", params={'symbol': ticker})
        if data:
            return data[0]
        return None

    def get_income_statement(self, ticker: str, period: str = 'annual', limit: int = 5) -> List[Dict]:
        # 匹配用户提供的 URL: /stable/income-statement?symbol=AAPL
        params = {
            'symbol': ticker,
            'limit': limit
        }
        if period == 'quarter':
            params['period'] = 'quarter'
        return self._get("income-statement", params=params) or []

    def get_balance_sheet(self, ticker: str, period: str = 'annual', limit: int = 5) -> List[Dict]:
        """
        V3.5: Added for Inventory checks
        """
        params = {
            'symbol': ticker,
            'limit': limit
        }
        if period == 'quarter':
            params['period'] = 'quarter'
        return self._get("balance-sheet-statement", params=params) or []

    def get_cash_flow_statement(self, ticker: str, period: str = 'annual', limit: int = 5) -> List[Dict]:
        params = {
            'symbol': ticker,
            'limit': limit
        }
        if period == 'quarter':
            params['period'] = 'quarter'
        return self._get("cash-flow-statement", params=params) or []

    def get_key_metrics(self, ticker: str, period: str = 'annual', limit: int = 1) -> List[Dict]:
        params = {
            'symbol': ticker,
            'limit': limit
        }
        if period == 'quarter':
            params['period'] = 'quarter'
        return self._get("key-metrics", params=params) or []

    def get_ratios_ttm(self, ticker: str) -> Optional[Dict]:
        data = self._get("ratios-ttm", params={'symbol': ticker})
        if data:
            return data[0]
        return None

    def get_financial_growth(self, ticker: str, limit: int = 5) -> List[Dict]:
        return self._get("financial-growth", params={'symbol': ticker, 'limit': limit}) or []

    def get_profile(self, ticker: str) -> Optional[Dict]:
        data = self._get("profile", params={'symbol': ticker})
        if data:
            return data[0]
        return None

    def get_historical_price_daily(self, ticker: str, days: int = 365) -> List[Dict]:
        """
        V3.5: Get raw OHLCV for Physics/VPA calculation.
        Using v3 endpoint for historical-price-full
        """
        # Endpoint: /api/v3/historical-price-full/AAPL
        # This usually returns 5 years on free tier, or recently limited.
        # But 'historical-price-full' is the standard one.
        
        # We need roughly 1 year for good SMA/Volume analysis context
        # Params 'from' and 'to' can be used, or 'timeseries' count
        
        data = self._get(f"historical-price-full/{ticker}", use_v3=True)
        if data and 'historical' in data:
            return data['historical'][:days] # Return last N days
        return []

    # ========== V3.4 New Methods ==========

    def get_vix(self) -> Optional[float]:
        """
        获取 VIX 恐慌指数
        """
        # FMP 使用 ^VIX 作为恐慌指数符号
        data = self._get("quote", params={'symbol': '^VIX'})
        if data and len(data) > 0:
            return data[0].get('price')
        return None

    def get_stock_news(self, ticker: str, limit: int = 20, from_date: Optional[str] = None, to_date: Optional[str] = None) -> List[Dict]:
        """
        获取个股相关新闻
        """
        params = {
            'symbols': ticker,
            'limit': limit
        }
        if from_date:
            params['from'] = from_date
        if to_date:
            params['to'] = to_date
        return self._get("news/stock", params=params) or []

    def get_forex_news(self, symbol: str = "EURUSD", limit: int = 10) -> List[Dict]:
        """
        获取外汇新闻
        """
        params = {
            'symbols': symbol,
            'limit': limit
        }
        return self._get("news/forex", params=params) or []

if __name__ == "__main__":
    fMPClient = FMPClient()
    print(fMPClient.get_quote('^TNX'))
