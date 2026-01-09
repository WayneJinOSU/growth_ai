import requests
from typing import Dict, List, Optional, Any
import config

class FMPClient:
    def __init__(self):
        self.api_key = config.FMP_API_KEY
        # 切换到更稳定的 stable 路径
        self.base_url = "https://financialmodelingprep.com/stable"

    def _get(self, endpoint: str, params: Optional[Dict] = None) -> Any:
        if not self.api_key:
            raise ValueError("FMP_API_KEY is not set")
        
        # 修复可变默认参数问题
        if params is None:
            params = {}
        else:
            # 拷贝一份，避免修改外部传入的字典
            params = params.copy()
            
        url = f"{self.base_url}/{endpoint}"
        params['apikey'] = self.api_key
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            if isinstance(data, list) and len(data) == 0:
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
