from tavily import TavilyClient
import config
import re
from typing import List, Dict, Optional

class SearchClient:
    def __init__(self):
        self.client = TavilyClient(api_key=config.TAVILY_API_KEY)

    def search(self, query: str, max_results: int = 5) -> List[Dict]:
        try:
            response = self.client.search(query, max_results=max_results, search_depth="advanced")
            return response.get('results', [])
        except Exception as e:
            print(f"Search Error: {e}")
            return []

    # ========== V3.4 New Methods ==========

    def get_treasury_yield(self) -> Optional[float]:
        """
        通过 Tavily 搜索获取 10 年期美债收益率 (US10Y)
        用于 V3.4 宏观压力阀判断
        
        Returns:
            float: 收益率百分比 (如 4.5 表示 4.5%)，获取失败返回 None
        """
        try:
            # 搜索实时美债收益率
            results = self.search("10 year US treasury yield current rate today", max_results=3)
            
            if not results:
                return None
            
            # 从搜索结果中提取数字 (格式如 4.5%, 4.50, etc.)
            for result in results:
                content = result.get('content', '') + ' ' + result.get('title', '')
                # 匹配类似 "4.5%", "4.50%", "4.5 percent" 的模式
                matches = re.findall(r'(\d+\.\d+)\s*%?', content)
                for match in matches:
                    value = float(match)
                    # 美债收益率通常在 0-10% 范围内
                    if 0 < value < 10:
                        return value
            
            return None
        except Exception as e:
            print(f"Treasury Yield Search Error: {e}")
            return None

    def get_press_releases(self, ticker: str, company_name: str = None, limit: int = 5) -> List[Dict]:
        """
        通过 Tavily 定向搜索获取公司官方新闻稿
        使用 site: 语法锁定 businesswire.com, prnewswire.com 等官方公告源
        
        用于 V3.4 沙袋指数检测 (管理层指引 vs 实际表现)
        
        Args:
            ticker: 股票代码
            company_name: 公司名称 (可选，用于更精准搜索)
            limit: 返回数量上限 (默认 5)
        
        Returns:
            List[Dict]: 新闻稿列表，包含 title, content, url 等字段
        """
        try:
            # 构建定向搜索 query - 锁定官方公告源
            search_term = company_name if company_name else ticker
            
            # 使用 site: 语法定向搜索官方 PR 渠道
            query = f'"{search_term}" OR "{ticker}" earnings guidance announcement site:businesswire.com OR site:prnewswire.com OR site:globenewswire.com'
            
            print(f"      [Tavily PR] Searching: {query[:80]}...")
            results = self.search(query, max_results=limit)
            
            if not results:
                # 备用搜索 - 更宽泛但仍聚焦官方源
                fallback_query = f'{ticker} press release quarterly results 2024 2025 site:businesswire.com OR site:prnewswire.com'
                print("      [Tavily PR] Fallback search...")
                results = self.search(fallback_query, max_results=limit)
            
            # 转换为与 FMP 接口兼容的格式
            formatted_results = []
            for r in results:
                formatted_results.append({
                    'title': r.get('title', ''),
                    'text': r.get('content', ''),
                    'url': r.get('url', ''),
                    'publishedDate': r.get('published_date', 'N/A'),
                    'source': 'Tavily Search'
                })
            
            print(f"      [Tavily PR] Found {len(formatted_results)} press releases")
            return formatted_results
            
        except Exception as e:
            print(f"Press Release Search Error: {e}")
            return []
