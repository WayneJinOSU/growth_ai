import requests
import trafilatura
from typing import Dict, List, Optional, Any
import config
from tools.llm import LLMClient

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

        base = self.base_url
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

    def get_historical_price_daily(self, ticker: str, from_date: str, to_date: str) -> List[Dict]:
        """
        V3.5: Get raw OHLCV for Physics/VPA calculation.
        Updated to use stable endpoint with date range.
        Endpoint: https://financialmodelingprep.com/stable/historical-price-eod/full?symbol=AAPL&from=...&to=...
        """
        params = {
            'symbol': ticker,
            'from': from_date,
            'to': to_date
        }
        # 注意：endpoint 不需要末尾的 /
        data = self._get("historical-price-eod/full", params=params)
        if not data or not isinstance(data, list):
            return []
        data = sorted(data, key=lambda x: x['date'])
        return data

    def get_vix(self) -> Optional[float]:
        """
        获取 VIX 恐慌指数
        """
        # FMP 使用 ^VIX 作为恐慌指数符号
        data = self._get("quote", params={'symbol': '^VIX'})
        if data and len(data) > 0:
            return data[0].get('price')
        return None

    def get_stock_news(self, ticker: str, limit: int = 5, from_date: Optional[str] = None, to_date: Optional[str] = None,
                       summarize: bool = True, llm: Optional[Any] = None) -> List[Dict]:
        """
        获取个股相关新闻
        V3.5: 新增 Trafilatura 提取 & LLM 总结功能
        """
        params = {
            'symbols': ticker,
            'limit': limit
        }
        if from_date:
            params['from'] = from_date
        if to_date:
            params['to'] = to_date
            
        news_list = self._get("news/stock", params=params) or []
        
        if summarize and llm and news_list:
            print(f"      [FMP] Summarizing {len(news_list)} news items for {ticker}...")
            for item in news_list:
                url = item.get('url')
                if not url:
                    continue
                
                try:
                    # 使用 Trafilatura 提取网页内容
                    downloaded = trafilatura.fetch_url(url)
                    content = trafilatura.extract(downloaded)
                    print(url)
                    if content:
                        # 使用 LLM 总结
                        system_prompt = f"""
                        Role:
                        You are a Senior Equity Research Analyst with expertise in capital markets, corporate finance, and SEC filings. Your task is to dissect financial press releases and news articles to provide concise, data-driven summaries for institutional investors.
                        Instructions:
                        Analyze the provided news text from the FMP (Financial Modeling Prep) API. Process the information through the following multi-step framework:
                        Step 1: News Categorization
                        Identify the primary nature of the news:
                        Capital Markets: (IPO, Secondary Offering, Private Placement, Debt Issuance, Share Buyback)
                        M&A & Strategic: (Mergers, Acquisitions, Divestitures, Joint Ventures)
                        Earnings & Financials: (Quarterly/Annual Results, Revenue Guidance, Dividend changes)
                        Operational/Business: (New Contracts, Product Launches, Partnerships)
                        Governance & Legal: (Management/Board changes, Lawsuits, SEC Investigations)
                        Step 2: Structured 5-Pillar Summary
                        Extract the following dimensions. If a specific detail is not mentioned, mark it as "N/A":
                        Headline Event (The "What"):
                        Sentiment: [Bullish / Bearish / Neutral]
                        Summary: A 1-sentence description of the core action and the parties involved.
                        The Numbers (Key Financial Metrics):
                        If Capital Markets/M&A: Price per share, total gross proceeds, discount/premium to market price, valuation multiples.
                        If Earnings: Revenue, EPS, Gross Margin (actual vs. consensus if available), YoY and QoQ growth rates.
                        If Operational: Contract value, duration, or estimated market size.
                        Rationale & Strategy (The "Why"):
                        What is the stated purpose of this move? (e.g., debt repayment, R&D, inorganic growth, increasing public float).
                        Ownership & Market Impact:
                        Dilution/Ownership: Changes in major shareholder percentages or potential share dilution.
                        Market Dynamics: Impact on "Free Float," liquidity, or complex financial instruments (e.g., Capped Calls, Hedging) that might cause price volatility.
                        Risks & Forward-Looking Outlook:
                        Timeline: Key dates (Closing date, Expiry date, Earnings call).
                        Guidance: Future financial targets or project milestones.
                        Risk Factors: Macro, regulatory, or technical risks mentioned in the text.
                        Constraints:
                        Exclude boilerplate legal disclaimers and standard "About the Company" sections.
                        Use professional financial terminology.
                        Be concise; use bullet points for clarity.
                        """
                        summary = llm.analyze_text(content, system_prompt=system_prompt , model="google/gemini-2.5-flash-lite")
                        if summary:
                            item['text'] = summary.strip()
                            item['is_summarized'] = True
                            print(summary)
                except Exception as e:
                    print(f"      [Error] Failed to summarize news from {url}: {e}")
                    
        return news_list

    def get_stock_screener(self, market_cap_more_than: Optional[int] = None, market_cap_lower_than: Optional[int] = None, sector: Optional[str] = None, exchange: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """
        股票筛选器
        """
        params = {
            'limit': limit,
            'isEtf': 'false',
            'isFund': 'false',
            'isActivelyTrading': 'true'
        }
        if market_cap_more_than is not None:
            params['marketCapMoreThan'] = market_cap_more_than
        if market_cap_lower_than is not None:
            params['marketCapLowerThan'] = market_cap_lower_than
        if sector:
            params['sector'] = sector
        if exchange:
            params['exchange'] = exchange
            
        return self._get("company-screener", params=params ) or []

    def get_forex_news(self, symbol: str = "EURUSD", limit: int = 10) -> List[Dict]:
        """
        获取外汇新闻
        """
        params = {
            'symbols': symbol,
            'limit': limit
        }
        return self._get("news/forex", params=params) or []

fmpClient = FMPClient()

if __name__ == "__main__":
    fMPClient = FMPClient()
    llmClient = LLMClient()
    # print(fMPClient.get_stock_news('AXON', llm=llmClient))
    print(fMPClient.get_historical_price_daily('AXON', from_date='2025-12-01', to_date='2026-01-28'))
    print(fMPClient.get_ratios_ttm('AXON'))
