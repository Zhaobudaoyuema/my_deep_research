import os
from pathlib import Path

import aiohttp
from dotenv import load_dotenv

from web_search_agent.tools.base import BaseTool

project_root = Path(__file__).resolve().parent.parent
env_path = project_root / 'config' / '.env'

load_dotenv(dotenv_path=env_path)

class GoogleSearchTool(BaseTool):
    name: str = "web_search"
    description: str = """Performs a google web search for your query then returns a string of the top search results."""
    parameters: dict = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query to perform.",
            },
            'filter_year': {
            "type": "integer",
            "description": "Optionally restrict results to a certain year",
            "nullable": True,
        }
        },
        "required": ["query"],
    }

    organic_key: str = ''
    api_key: str = ''
    provider: str = ''

    def __init__(self, provider = ''):
        super().__init__(provider=provider)
        self.provider = provider
        if provider == "serpapi":
            self.organic_key = "organic_results"
            self.api_key = os.getenv("serpapi")
        else:
            self.organic_key = "organic"
            self.api_key = os.getenv("organic")

    async def execute(self, query: str, filter_year: int | None = None) -> str:
        if self.provider == "serpapi":
            params = {
                "q": query,
                "api_key": self.api_key,
                "engine": "google",
                "google_domain": "google.com",
            }
            base_url = "https://serpapi.com/search.json"
        else:
            params = {
                "q": query,
                "api_key": self.api_key,
            }
            base_url = "https://google.serper.dev/search"

        if filter_year is not None:
            params["tbs"] = f"cdr:1,cd_min:01/01/{filter_year},cd_max:12/31/{filter_year}"

        async with aiohttp.ClientSession() as session:
            async with session.get(base_url, params=params) as response:
                if response.status != 200:
                    raise ValueError(await response.text())
                results = await response.json()

        if self.organic_key not in results:
            if filter_year is not None:
                raise Exception(
                    f"No results found for query: '{query}' with filtering on year={filter_year}. Use a less restrictive query or do not filter on year."
                )
            else:
                raise Exception(f"No results found for query: '{query}'. Use a less restrictive query.")

        if not results[self.organic_key]:
            year_filter_message = f" with filter year={filter_year}" if filter_year is not None else ""
            return f"No results found for '{query}'{year_filter_message}. Try with a more general query, or remove the year filter."

        web_snippets = []
        for idx, page in enumerate(results[self.organic_key]):
            date_published = f"\nDate published: {page['date']}" if "date" in page else ""
            source = f"\nSource: {page['source']}" if "source" in page else ""
            snippet = f"\n{page['snippet']}" if "snippet" in page else ""

            redacted_version = f"{idx}. [{page['title']}]({page['link']}){date_published}{source}\n{snippet}"
            web_snippets.append(redacted_version)

        return "## Search Results\n" + "\n\n".join(web_snippets)
