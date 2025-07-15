from typing import List
import asyncio

from baidusearch.baidusearch import search
from web_search_agent.tools.search.base import WebSearchEngine, SearchItem


class BaiduSearchEngine(WebSearchEngine):
    async def perform_search(
            self, query: list, num_results: int = 10, *args, **kwargs
    ) -> List[SearchItem]:
        """
        Baidu search engine (async wrapper for sync search using run_in_executor).

        Returns results formatted according to SearchItem model.
        """
        loop = asyncio.get_event_loop()
        # 把同步的 search 封装为后台线程异步执行
        raw_results = await loop.run_in_executor(None, search, query[0], num_results)

        results = []
        for i, item in enumerate(raw_results):
            if isinstance(item, str):
                results.append(
                    SearchItem(title=f"Baidu Result {i + 1}", url=item, description=None)
                )
            elif isinstance(item, dict):
                results.append(
                    SearchItem(
                        title=item.get("title", f"Baidu Result {i + 1}"),
                        url=item.get("url", ""),
                        description=item.get("abstract", None),
                    )
                )
            else:
                try:
                    results.append(
                        SearchItem(
                            title=getattr(item, "title", f"Baidu Result {i + 1}"),
                            url=getattr(item, "url", ""),
                            description=getattr(item, "abstract", None),
                        )
                    )
                except Exception:
                    results.append(
                        SearchItem(
                            title=f"Baidu Result {i + 1}", url=str(item), description=None
                        )
                    )

        return results
