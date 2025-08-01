from web_search_agent.learn_multi_step_agent.llm.openai_llm import OpenAILLM, MessageRole
from web_search_agent.tools.base import BaseTool

class ResearchDraftGeneratorTool(BaseTool):
    name: str = "generate_research_draft"
    description: str = """根据用户查询和研究计划自动生成结构化、学术风格的研究草稿，用于支撑进一步研究或撰写报告。当前只是草稿，不需要很长的输出，只需要
    200字以内的就足够了"""
    parameters: dict = {
        "type": "object",
        "properties": {
            "user_query": {
                "type": "string",
                "description": "用户最初提出的研究问题或查询。",
            },
            "research_plan": {
                "type": "string",
                "description": "研究计划的内容，包含研究维度、目标和关键问题，使用 markdown 格式。",
            },
            "draft_context": {
                "type": "string",
                "description": "可选的研究上下文或背景信息，如已有资料、研究方向提示等。",
            }
        },
        "required": ["user_query", "research_plan"],
    }

    async def execute(self, user_query: str, research_plan: str, draft_context: str = "") -> str:
        draft_prompt = f"""请为以下查询创建一份全面的研究草稿：

查询：  
{user_query}

研究计划：  
{research_plan}

{draft_context if draft_context else ""}

请生成一份详细的研究草稿，要求如下：

1. 全面覆盖
- 涵盖研究背景中提到的所有方面  
- 各研究维度的内容分布应均衡  
- 融合多种观点，形成有机整体  

2. 结构与组织
- 引言需清晰列出将要讨论的所有内容要点  
- 主体部分应按研究维度分节组织良好  
- 不同维度之间逻辑衔接顺畅  
- 结论部分应整合各观点，形成统一认识  

3. 内容要求
- 包含最新的信息和近期发展动态  
- 回应研究计划中提出的关键问题  
- 明确指出仍需进一步研究的领域  
- 提供基于证据的分析和论证  

4. 整合策略
- 展示各研究维度之间的关联性  
- 突出互补性与对立性发现  
- 在多维度之间提炼综合性见解  
- 回应研究中可能存在的空白或冲突点  

该草稿应具有扎实的深度与广度，能为后续研究与细化工作打下坚实基础。重点在于深入探讨所有指定研究维度，同时保持内容的一致性与连贯性。

文风要求：  
请使用清晰、专业、具有学术报告风格的表达方式撰写。

当前只是草稿，不需要很多，仅需200字以内。
"""
        llm = OpenAILLM()
        messages = [{'role': MessageRole.USER, 'content': f"/no_think {draft_prompt}"}]
        response = await llm.generate(messages)
        return f"当前生成的草稿：你需要后续一直通过调用gaps优化补充他。{response.content}"
