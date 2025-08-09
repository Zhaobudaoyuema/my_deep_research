import asyncio
import os
from pathlib import Path

import aiohttp
from dotenv import load_dotenv

from web_search_agent.tools.base import BaseTool

project_root = Path(__file__).resolve().parent.parent
env_path = project_root / 'config' / '.env'

load_dotenv(dotenv_path=env_path)


class Search360Tool(BaseTool):
    name: str = "web_search"
    description: str = """Performs a 360 web search for your query then returns a string of the top search results."""
    parameters: dict = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query to perform.",
            }
        },
        "required": ["query"],
    }

    async def execute(self, query: str) -> str:
        params = {
            "model": 'allso-n',
            "count": 20,
            "sub_query": query,
            "query": "query",
            "request_id": "1"
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(os.getenv("360_search_base_url"), headers={"Authorization": os.getenv("360_search_api_key")},params=params) as response:
                if response.status != 200:
                    raise ValueError(await response.text())
                results = await response.json()
        res = results.get("data", {}).get("output_results")
        res_sorted = sorted(res, key=lambda x: x['rank'], reverse=True)
        res_list = []
        for i in res_sorted:
            if i.get('rank') < 10:
                continue
            res_list.append(f"标题：{i.get("title")}\n发布时间：{i.get('date')}\n正文：{i.get("summary_large")}")
        return res_list

if __name__ == "__main__":
    tool = Search360Tool()
    print(asyncio.run(tool.execute("日本的天气")))
