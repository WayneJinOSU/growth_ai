from tavily import TavilyClient
import config
from typing import List, Dict

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

