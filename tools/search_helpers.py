"""
SearchHelper: 跨 Phase 共用的搜索 + 引用收集工具
=================================================
所有 Phase 通过组合 (composition) 使用本类，消除重复实现。

Usage:
    sh = SearchHelper(search_client, deep_client)
    results = sh.unified_search(query, deep_search=True)
    context = sh.collect_refs(results, references)
"""

from core.data_models import SearchReference


class SearchHelper:
    """
    统一搜索分派 + 引用去重收集器。
    各 Phase 在 __init__ 中组合本类即可，无需各自重复实现。
    """

    def __init__(self, search_client, deep_client=None):
        self.search = search_client
        self.deep = deep_client

    def collect_refs(self, results: list, references: list) -> str:
        """
        去重搜索结果并构建带 [ID] 引用的上下文字符串。
        同一 URL 不会重复入库，已存在的 ref 会被复用。

        Args:
            results: 搜索结果列表 (每项包含 url, title, content)
            references: 全局引用列表 (会被就地修改)

        Returns:
            带 [ID] 标记的上下文文本
        """
        new_refs = []
        for r in results:
            if r.get('url'):
                if not any(ref.url == r['url'] for ref in references):
                    new_id = len(references) + 1
                    ref = SearchReference(
                        id=new_id,
                        title=r.get('title', 'No Title'),
                        url=r['url'],
                        snippet=r.get('content', '')[:100] + '...'
                    )
                    references.append(ref)
                    new_refs.append(ref)
                else:
                    existing = next(ref for ref in references if ref.url == r['url'])
                    new_refs.append(existing)

        context_parts = []
        for r, ref in zip(results, new_refs):
            content = r.get('content', '')
            context_parts.append(f"[{ref.id}] {ref.title}: {content}")
        return "\n\n".join(context_parts)

    def unified_search(self, query: str, max_results: int = 5,
                       days: int = 180, deep_search: bool = False) -> list:
        """
        统一搜索分派：deep_search=True 时优先使用 Tavily advanced search，
        无结果或异常时 fallback 到标准搜索。

        Args:
            query: 搜索关键词
            max_results: 最大结果数
            days: 标准搜索的时间窗口（天）
            deep_search: 是否启用深度搜索

        Returns:
            搜索结果列表
        """
        if deep_search and self.deep:
            try:
                raw = self.deep.search.client.search(
                    query, search_depth="advanced", max_results=max_results
                ).get('results', [])
                if raw:
                    print(f"        [Deep] {len(raw)} results via advanced search")
                    return raw
                print("        [Deep] No results, falling back to standard search")
            except Exception as e:
                print(f"        [Deep] Error ({e}), falling back to standard search")
        return self.search.search(query, max_results=max_results, days=days)
