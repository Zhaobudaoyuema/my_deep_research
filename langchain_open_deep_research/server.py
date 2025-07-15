import asyncio
import uuid

from IPython.display import Image, display
from IPython.display import Markdown
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from graph import builder


async def main():
    from dotenv import load_dotenv
    load_dotenv()
    memory = MemorySaver()
    graph = builder.compile(checkpointer=memory)
    thread = {"configurable": {"thread_id": str(uuid.uuid4()),
                               "search_api": "tavily",
                               "planner_provider": "openai",
                               "planner_model": "gpt-4o",
                               "writer_provider": "openai",
                               "writer_model": "gpt-4o",
                               "max_search_depth": 1,
                               }}

    topic = "北京小米汽车最近汽车事故舆情分析"
    async for event in graph.astream({"topic": topic, }, thread, stream_mode="updates"):
        print(event)
        if '__interrupt__' in event:
            interrupt_value = event['__interrupt__'][0].value
            Markdown(interrupt_value)

    # async for event in graph.astream(
    #         Command(resume="Include individuals sections for Together.ai, Groq, and Fireworks with revenue estimates (ARR)"),
    #         thread, stream_mode="updates"):
    #     if '__interrupt__' in event:
    #         interrupt_value = event['__interrupt__'][0].value
    #         display(Markdown(interrupt_value))

    async for event in graph.astream(Command(resume=True), thread, stream_mode="updates"):
        print(event)
        print("\n")
    print(f"final_report: ")
    final_state = graph.get_state(thread)
    report = final_state.values.get('final_report')
    Markdown(report)
if __name__ == "__main__":
    asyncio.run(main())