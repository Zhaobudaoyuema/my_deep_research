from web_search_agent.tools.base import BaseTool


class ResearchPlanSaverTool(BaseTool):
    name: str = "generates_research_plan"
    description: str = """生成模型输出的研究计划。该计划概述了关键研究领域，作为后续智能体操作的框架。"""
    parameters: dict = {
        "type": "object",
        "properties": {
            "user_query": {
                "type": "string",
                "description": "触发此次研究的用户原始查询。",
            },
            "research_plan": {
                "type": "string",
                "description": "结构化的研究计划，包含关键研究领域和目标，采用 Markdown 格式。",
            }
        },
        "required": ["user_query", "research_plan"],
    }


    async def execute(self, user_query: str, research_plan: str) -> str:
        # 假设我们将计划保存到某个数据库或内存中用于后续阶段
        # 这里只是示例：打印或简单返回以确认保存成功
        # 可以根据实际需求替换为写入文件、缓存或数据库逻辑
        print("✅ 已保存研究计划：")
        print(f"🔍 查询：{user_query}")
        print(f"📋 计划内容：\n{research_plan}")

        return f"当前的研究计划: 这个很重要，每次生成gaps问题的时候 都需要带着。{research_plan}"
