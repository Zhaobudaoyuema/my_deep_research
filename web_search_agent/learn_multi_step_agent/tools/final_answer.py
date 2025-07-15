from typing import Any

from web_search_agent.tools.base import BaseTool


class FinalAnswerTool(BaseTool):
    name: str = "final_answer"
    description: str = "Provides a final answer to the given problem."
    parameters: dict = {
        "type": "object",
        "properties": {
            "answer": {
                "type": "string",
                "description": "The final answer to the problem",
            }
        },
        "required": ["answer"],
    }

    async def execute(self, answer: Any) -> Any:
        return answer
