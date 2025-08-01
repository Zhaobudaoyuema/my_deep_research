from web_search_agent.tools.base import BaseTool


class DenoiseAndReviseDraftTool(BaseTool):
    name: str = "denoise_and_revise_draft"
    description:str = """执行草稿的“去噪与修订”步骤，利用前一阶段 gap 搜索返回的信息进行内容补全和优化。
模型需结合上下文中的 research_plan、query、current_draft 和 gaps_search 检索结果，补充具体细节、完善事实、删除占位符，提升草稿质量。
需用 [1]、[2] 等方式插入引用，保留草稿原有结构，并标注尚未补全的地方 [NEEDS RESEARCH]。"""

    parameters: dict = {
        "type": "object",
        "properties": {
            "improved_draft": {
                "type": "string",
                "description": "修订优化后的草稿版本，已融合 gap 检索补全信息，完成结构、准确性与表达层面的增强。"
            }
        },
        "required": ["improved_draft"]
    }

    async def execute(self, improved_draft: str) -> str:
        print("✅ 草稿已完成去噪与修订：\n")
        print(improved_draft)
        return f"新的草稿: {improved_draft}"
