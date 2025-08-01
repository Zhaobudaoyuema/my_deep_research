import asyncio

from web_search_agent.learn_multi_step_agent.agents.tool_call_agent import ToolCallingAgent
from web_search_agent.ttd_dr_open.backbone_deep_research_agent import BackboneDeepResearchAgent


async def main():
    agent = BackboneDeepResearchAgent()
    try:
        prompt = input("Enter your prompt: ")
        if not prompt.strip():
            print("Empty prompt provided.")
            return

        print("Processing your request...")
        await agent.run(prompt)
        print("Request processing completed.")
    except KeyboardInterrupt:
        print("Operation interrupted.")

if __name__ == "__main__":
    # asyncio.run(main())
    asyncio.run(main())
