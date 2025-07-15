from langchain.chat_models import init_chat_model


class LangchainLLM:
    llm = init_chat_model("gpt-4o", model_provider="openai", temperature=0)

    async def run(self):
        await self.llm.ainvoke()