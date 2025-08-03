from typing import TypedDict, Annotated

from langgraph.graph import add_messages


class State(TypedDict):
    query:  str
    research_plan: str
    draft: str
    last_all_q: list
    retrieved_content: str

    messages: Annotated[list, add_messages]