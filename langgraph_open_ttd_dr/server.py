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
                               }}

    topic = "北京小米汽车最近汽车事故舆情分析"
    async for event in graph.astream({"query": topic, "max_search_depth": 5}, thread):
        print("\n-------------- 执行完一个节点 -------------\n")
        # if '__interrupt__' in event:
        #     interrupt_value = event['__interrupt__'][0].value
        #     Markdown(interrupt_value)

    final_state = graph.get_state(thread)
    report = final_state.values.get('final_report')
    Markdown(report)
if __name__ == "__main__":
    asyncio.run(main())