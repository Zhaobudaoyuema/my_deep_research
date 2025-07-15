import asyncio

from web_search_agent.react_agent import ReActAgent
from web_search_agent.sub_search_agent import SubSearchAgent


async def sub_search(topic):
    """
    Perform sub-search using the agent.

    Args:
        agent (ReActAgent): The agent to perform the sub-search.
        topic (str): The topic for the sub-search.

    Returns:
        str: The result of the sub-search.
    """
    agent = SubSearchAgent()
    return await agent.run(topic)

async def main():
    # Create and initialize Manus agent
    agent = ReActAgent()
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
    asyncio.run(sub_search("What is the publication date of the collection from Psychology Top 100 of 2023?"))
