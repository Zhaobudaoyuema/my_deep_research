from typing import List, Optional, Tuple

import aiohttp
import requests
from bs4 import BeautifulSoup


from web_search_agent.tools.search.base import WebSearchEngine, SearchItem


ABSTRACT_MAX_LENGTH = 300

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36",
    "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/49.0.2623.108 Chrome/49.0.2623.108 Safari/537.36",
    "Mozilla/5.0 (Windows; U; Windows NT 5.1; pt-BR) AppleWebKit/533.3 (KHTML, like Gecko) QtWeb Internet Browser/3.7 http://www.QtWeb.net",
    "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36",
    "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/532.2 (KHTML, like Gecko) ChromePlus/4.0.222.3 Chrome/4.0.222.3 Safari/532.2",
    "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1.4pre) Gecko/20070404 K-Ninja/2.1.3",
    "Mozilla/5.0 (Future Star Technologies Corp.; Star-Blade OS; x86_64; U; en-US) iNet Browser 4.7",
    "Mozilla/5.0 (Windows; U; Windows NT 6.1; rv:2.2) Gecko/20110201",
    "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1.13) Gecko/20080414 Firefox/2.0.0.13 Pogo/2.0.0.13.6866",
]

HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "Content-Type": "application/x-www-form-urlencoded",
    "User-Agent": USER_AGENTS[0],
    "Referer": "https://www.bing.com/",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "zh-CN,zh;q=0.9",
}

BING_HOST_URL = "https://www.bing.com"
BING_SEARCH_URL = "https://www.bing.com/search?q="


class BingSearchEngine(WebSearchEngine):
    def __init__(self, **data):
        super().__init__(**data)

    async def _fetch_html(self, session: aiohttp.ClientSession, url: str) -> Optional[str]:
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.text()
                return None
        except Exception as e:
            print(f"Fetch error: {e}")
            return None

    async def _parse_html(
        self, session: aiohttp.ClientSession, url: str, rank_start: int = 0
    ) -> Tuple[List[SearchItem], Optional[str]]:
        html_text = await self._fetch_html(session, url)
        if not html_text:
            return [], None

        try:
            root = BeautifulSoup(html_text, "lxml")
            list_data = []
            ol_results = root.find("ol", id="b_results")
            if not ol_results:
                return [], None

            for li in ol_results.find_all("li", class_="b_algo"):
                try:
                    h2 = li.find("h2")
                    title = h2.text.strip() if h2 else ""
                    url = h2.a["href"].strip() if h2 and h2.a else ""

                    p = li.find("p")
                    abstract = p.text.strip() if p else ""
                    if ABSTRACT_MAX_LENGTH and len(abstract) > ABSTRACT_MAX_LENGTH:
                        abstract = abstract[:ABSTRACT_MAX_LENGTH]

                    rank_start += 1

                    list_data.append(
                        SearchItem(
                            title=title or f"Bing Result {rank_start}",
                            url=url,
                            description=abstract,
                        )
                    )
                except Exception:
                    continue

            next_btn = root.find("a", title="Next page")
            next_url = BING_HOST_URL + next_btn["href"] if next_btn else None
            return list_data, next_url

        except Exception as e:
            print(f"Error parsing HTML: {e}")
            return [], None

    async def _search(self, query: str, num_results: int = 10) -> List[SearchItem]:
        if not query:
            return []

        list_result = []
        next_url = BING_SEARCH_URL + query
        rank_start = 0

        async with aiohttp.ClientSession(headers=HEADERS) as session:
            while len(list_result) < num_results and next_url:
                data, next_url = await self._parse_html(session, next_url, rank_start)
                if data:
                    list_result.extend(data)
                if not next_url:
                    break
                rank_start = len(list_result)

        return list_result[:num_results]

    async def perform_search(
        self, query: list, num_results: int = 10, *args, **kwargs
    ) -> List[SearchItem]:
        return await self._search(query[0], num_results=num_results)