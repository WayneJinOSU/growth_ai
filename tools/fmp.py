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

    # ========== V3.4 New Methods ==========
    # Note: get_treasury_yield() 移至 SearchClient，使用 Tavily 搜索获取
    # 因为 FMP ^TNX 数据需要更高权限

    def get_vix(self) -> Optional[float]:
        """
        获取 VIX 恐慌指数
        用于 V3.4 波动率熔断机制
        
        Returns:
            float: VIX 值，获取失败返回 None
        """
        # FMP 使用 ^VIX 作为恐慌指数符号
        data = self._get("quote", params={'symbol': '^VIX'})
        if data and len(data) > 0:
            return data[0].get('price')
        return None

    def get_stock_news(self, ticker: str, limit: int = 20, from_date: Optional[str] = None, to_date: Optional[str] = None) -> List[Dict]:
        """
        获取个股相关新闻
        用于 V3.4 紧急弹射信号检测 (高管离职、客户流失等)
        
        Args:
            ticker: 股票代码
            limit: 返回数量上限 (默认 20)
            from_date: 起始日期 (格式: YYYY-MM-DD)
            to_date: 结束日期 (格式: YYYY-MM-DD)
        
        Returns:
            List[Dict]: 新闻列表，包含 title, text, publishedDate 等字段
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

    # NOTE: get_press_releases() 已移至 SearchClient.get_press_releases()
    # 使用 Tavily 定向搜索 businesswire.com/prnewswire.com 替代
    # 因为 FMP news/press-releases 接口需要更高级别会员权限

    def get_forex_news(self, symbol: str = "EURUSD", limit: int = 10) -> List[Dict]:
        """
        获取外汇新闻
        用于 V3.4 估值桥 Layer B 微调 (美元强弱影响跨国公司业绩)
        
        Args:
            symbol: 货币对 (默认 EURUSD)
            limit: 返回数量上限 (默认 10)
        
        Returns:
            List[Dict]: 外汇新闻列表
        """
        params = {
            'symbols': symbol,
            'limit': limit
        }
        return self._get("news/forex", params=params) or []

    # ========== V3.7 New Methods ==========

    def get_balance_sheet(self, ticker: str, period: str = 'annual', limit: int = 5) -> List[Dict]:
        """
        获取资产负债表
        用于 V3.7 Financial Forensics (库存周转、债务分析)
        
        Args:
            ticker: 股票代码
            period: 'annual' 或 'quarter'
            limit: 返回数量上限
        
        Returns:
            List[Dict]: 资产负债表数据列表
        """
        params = {
            'symbol': ticker,
            'limit': limit
        }
        if period == 'quarter':
            params['period'] = 'quarter'
        return self._get("balance-sheet-statement", params=params) or []

    def get_ratios(self, ticker: str, period: str = 'annual', limit: int = 5) -> List[Dict]:
        """
        获取历史财务比率
        用于 V3.7 Historical PE Z-Score 计算
        
        Args:
            ticker: 股票代码
            period: 'annual' 或 'quarter'
            limit: 返回数量上限
        
        Returns:
            List[Dict]: 财务比率数据列表 (含 PE, PB, etc.)
        """
        params = {
            'symbol': ticker,
            'limit': limit
        }
        if period == 'quarter':
            params['period'] = 'quarter'
        return self._get("ratios", params=params) or []

    def get_enterprise_values(self, ticker: str, period: str = 'annual', limit: int = 5) -> List[Dict]:
        """
        获取企业价值数据
        用于 V3.7 Net Debt / EBITDA 计算
        
        Args:
            ticker: 股票代码
            period: 'annual' 或 'quarter'
            limit: 返回数量上限
        
        Returns:
            List[Dict]: 企业价值数据列表 (含 enterpriseValue, netDebt 等)
        """
        params = {
            'symbol': ticker,
            'limit': limit
        }
        if period == 'quarter':
            params['period'] = 'quarter'
        return self._get("enterprise-values", params=params) or []


if __name__ == "__main__":
    fMPClient = FMPClient()
    print(fMPClient.get_quote('^TNX'))
