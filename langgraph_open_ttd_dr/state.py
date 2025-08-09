from typing import TypedDict, Annotated

from langgraph.graph import add_messages


class State(TypedDict):
    query:  str
    research_plan: str
    draft: str
    last_all_q: list
    retrieved_content: str
    previous_draft: str
    messages: Annotated[list, add_messages]
    max_search_depth:int
    cur_search_depth:int
    sub_queries: list
    overall_evaluation: str
    final_report:str