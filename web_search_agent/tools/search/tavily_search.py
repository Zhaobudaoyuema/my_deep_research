import asyncio
from typing import List, Optional, Tuple

import requests
from bs4 import BeautifulSoup
from charset_normalizer import from_bytes
from tavily import AsyncTavilyClient

from web_search_agent.tools.search.base import WebSearchEngine, SearchItem


class TavilySearchEngine(WebSearchEngine):

    async def _search_sync(self, search_queries: List[str], num_results: int = 10):
        if not search_queries:
            return []

        tavily_async_client = AsyncTavilyClient(api_key="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")
        search_tasks = []
        for query in search_queries:
            search_tasks.append(
                tavily_async_client.search(
                    query,
                    max_results=num_results,
                    include_raw_content=True,
                    topic="general"
                )
            )

        # Execute all searches concurrently
        search_docs = await asyncio.gather(*search_tasks)
        results = []
        for search in search_docs:
            temp = []
            result = search['results']
            for re in result:
                temp.append(
                    SearchItem(
                        title=re['title'], url=re['url'], description=self.fix_misdecoded_string(re['content'])
                    )
                )
            results.append(temp)


        print(f"tavily_search query: {search_queries}, results: {results}")

        return results

    def fix_misdecoded_string(self, raw: str) -> str:
        """
        修正被错误解码成 str 的乱码字符串，尝试多种编码还原并自动检测编码重新解码。
        使用 charset_normalizer 自动检测编码。
        """
        possible_encodings = ['latin1', 'windows-1252', 'gbk', 'big5', 'cp936']

        def contains_reasonable_text(text: str) -> bool:
            return any('\u4e00' <= c <= '\u9fff' for c in text) or any(c.isalpha() for c in text)

        for enc in possible_encodings:
            try:
                raw_bytes = raw.encode(enc)
                # charset_normalizer 返回结果列表，best() 是最优
                best_guess = from_bytes(raw_bytes).best()
                if best_guess is None:
                    continue
                fixed = best_guess.text
                if contains_reasonable_text(fixed):
                    return fixed
            except Exception:
                pass

        return raw
    async def perform_search(
        self, query: list, num_results: int = 10, *args, **kwargs
    ) -> List[SearchItem]:
        """
        Bing search engine.

        Returns results formatted according to SearchItem model.
        """
        result = await self._search_sync(query, num_results=num_results)
        return result[0]

    async def multi_perform_search(
            self, query_list: list, num_results: int = 10, *args, **kwargs
    ) -> List[SearchItem]:
        """
        Bing search engine.

        Returns results formatted according to SearchItem model.
        """
        result = await self._search_sync(query_list, num_results=num_results)
        return result
