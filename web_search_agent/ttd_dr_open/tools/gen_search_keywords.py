import asyncio

from web_search_agent.learn_multi_step_agent.tools.google_search_serpapi import GoogleSearchTool
from web_search_agent.learn_multi_step_agent.tools.search_360 import Search360Tool
from web_search_agent.tools.base import BaseTool


class GapsQuerySaverTool(BaseTool):
    name: str = "do_gaps_search"
    description:str = """接收由模型根据上下文自动生成的 gaps_query 列表。
这些查询用于识别当前研究草稿中的潜在问题或信息缺口，依据的上下文包括：research_plan、current_draft 和 previous_query。
要求模型生成的 gaps_query 精准、具体，能帮助后续任务发现事实不足、数据陈旧或缺乏证据的段落。
列表长度限制为恰好 4 项。"""

    parameters: dict = {
        "type": "object",
        "properties": {
            "gaps_query": {
                "type": "array",
                "items": {
                    "type": "string"
                },
                "minItems": 4,
                "maxItems": 4,
                "description": "基于当前上下文生成的 4 条草稿改进分析查询，用于后续检索补全。"
            }
        },
        "required": ["gaps_query"]
    }

    async def execute(self, gaps_query: list[str]) -> str:
        search = Search360Tool()
        tasks = [search.execute(q) for q in gaps_query]
        results = await asyncio.gather(*tasks)
        return "\n".join(results)


