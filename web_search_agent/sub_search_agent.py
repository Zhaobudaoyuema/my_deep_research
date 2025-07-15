import asyncio
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain.chat_models import ChatOpenAI, init_chat_model
from gemini_backend_deep_research.prompts import get_current_date, query_writer_instructions, reflection_instructions, \
    answer_instructions
from gemini_backend_deep_research.tools_and_schemas import SearchQueryList, Reflection

from web_search_agent.tools.search.tavily_search import TavilySearchEngine

load_dotenv()

class SubSearchAgent(BaseModel):
    name: str = Field(default="SubSearchAgent", description="Unique name of the agent")

    max_research_loops: int = 3

    research_loop_count: int = 0

    all_web_search: list = []


    async def generate_query(self, topic):
        llm = init_chat_model(model='gpt-4o', model_provider='openai')
        structured_llm = llm.with_structured_output(SearchQueryList)
        current_date = get_current_date()
        formatted_prompt = query_writer_instructions.format(
            current_date=current_date,
            research_topic=topic,
            number_queries=3,
        )
        # Generate the search queries
        result = structured_llm.invoke(formatted_prompt)
        print(f"初始查询生成：{result.query}")
        return result.query

    async def search_web(self, search_queries):
        search_engine = TavilySearchEngine()
        result = await search_engine.multi_perform_search(search_queries, 5)
        search_result = []
        for search in result:
            for item in search:
                search_result.append(str(item.to_dict()))
        self.all_web_search.extend(search_result)
        return search_result

    async def reflection(self,web_research_result, topic):
        try:
            llm = init_chat_model(model='gpt-4o', model_provider='openai')
            current_date = get_current_date()
            formatted_prompt = reflection_instructions.format(
                current_date=current_date,
                research_topic=topic,
                summaries="\n\n---\n\n".join(web_research_result),
            )

            for attempt in range(3):
                try:
                    result = llm.with_structured_output(Reflection).invoke(formatted_prompt)
                    print(f"当前轮数：{self.research_loop_count} 反思结果：{result}")
                    return {
                        "is_sufficient": result.is_sufficient,
                        "knowledge_gap": result.knowledge_gap,
                        "follow_up_queries": result.follow_up_queries,
                    }
                except Exception as e:
                    print(f"reflection 第 {attempt + 1} 次调用失败：{e}")
                    if attempt < 2:
                        await asyncio.sleep(1)
                    else:
                        raise

        except Exception as e:
            print(f"反思阶段失败：{e}")
            return {
                "is_sufficient": False,
                "knowledge_gap": "反思失败，未能获取信息差。",
                "follow_up_queries": [],
            }

    async def final_answer(self, topic):
        current_date = get_current_date()
        formatted_prompt = answer_instructions.format(
            current_date=current_date,
            research_topic=topic,
            summaries="\n---\n\n".join(self.all_web_search),
        )
        llm = init_chat_model(model='gpt-4o', model_provider='openai')
        result = llm.invoke(formatted_prompt)
        print(f"最终输出结果：{result.content}")
        return result.content

    async def run(self, topic):
        search_queries = await self.generate_query(topic)
        while self.research_loop_count < self.max_research_loops:
            web_result = await self.search_web(search_queries)
            reflect_result = await self.reflection(web_result, topic)
            if reflect_result['is_sufficient']:
                break
            else:
                search_queries = reflect_result['follow_up_queries']
            self.research_loop_count += 1
        await self.final_answer(topic)




