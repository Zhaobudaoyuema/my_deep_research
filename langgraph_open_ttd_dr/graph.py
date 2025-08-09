import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from langchain.chat_models import init_chat_model
from langgraph.constants import START, END
from langgraph.graph import StateGraph

from langgraph_open_ttd_dr.llm import llm_request
from langgraph_open_ttd_dr.prompts import plan_prompt, draft_generation_prompt, gap_analysis_prompt, denoising_prompt, \
    need_draft_denoising_prompt, final_answer_prompt
from langgraph_open_ttd_dr.schema import Queries, EvaluationSummary
from langgraph_open_ttd_dr.state import State
from web_search_agent.learn_multi_step_agent.tools.search_360 import Search360Tool
from web_search_agent.learn_multi_step_agent.utils.time import get_china_time
from langgraph.types import interrupt, Command

async def generate_report_plan(state: State):
    """
    生成研究计划
    :param state:
    :return:
    """
    query = state['query']
    prompt = plan_prompt.format(query=query, time=get_china_time())
    messages = [{"role": "user", "content": prompt}]
    _, result = await llm_request(messages=messages)
    return {"research_plan": result}

async def generate_draft_content(state: State):
    """
    生成草稿内容
    :param state:
    :return:
    """
    query = state['query']
    research_plan = state['research_plan']
    prompt = draft_generation_prompt.format(query=query, research_plan=research_plan, time=get_china_time())
    messages = [{"role": "user", "content": prompt}]
    _, result = await llm_request(messages=messages)
    return {'draft': result}

async def generate_sub_gaps_query(state: State):
    """
    生成子问题
    :param state:
    :return:
    """
    last_all_q = state.get('last_all_q', [])
    if last_all_q is None:
        last_all_q = []
    if not state.get('sub_queries'):
        draft = state['draft']
        query = state['query']
        plan = state['research_plan']
        prompt = gap_analysis_prompt.format(query=query, research_plan=plan, draft=draft)
        messages = [{"role": "user", "content": prompt}]
        _, result = await llm_request(messages=messages, schema=Queries)

        sub_search = [q.search_query for q in result.queries]
    else:
        sub_search = state.get('sub_queries', [])
    print(f"搜索query:{sub_search}")
    search_results = await web_search(sub_search)

    return {"retrieved_content": search_results, "last_all_q": last_all_q.extend(sub_search)}

async def web_search(result):
    search = Search360Tool()
    tasks = [search.execute(q) for q in result]
    results = await asyncio.gather(*tasks)
    re_list = []
    for result in results:
        re_list.extend(result)
    print(f"搜索结果数量:{len(re_list)}")
    return "## Search Results\n" + "\n\n".join(re_list)

async def draft_denoising(state: State):
    """
    草稿去噪
    :param state:
    :return:
    """
    draft = state['draft']
    query = state['retrieved_content']
    retrieved_content = state['research_plan']
    overall_evaluation = state.get('overall_evaluation')
    prompt = denoising_prompt.format(query=query, draft=draft, retrieved_content=retrieved_content,
                                     overall_evaluation=overall_evaluation)
    messages = [{"role": "user", "content": prompt}]
    _, result = await llm_request(messages=messages)

    return {"previous_draft": draft, "draft": result, "cur_search_depth": state.get('cur_search_depth', 1) + 1}

async def need_draft_denoising(state: State):
    """
    判断草稿是否需要去噪
    :param state:
    :return:
    """
    draft = state['draft']
    previous_draft = state['previous_draft']
    query = state['query']
    prompt = need_draft_denoising_prompt.format(query=query, current_draft=draft, previous_draft=previous_draft)
    messages = [{"role": "user", "content": prompt}]
    _, result = await llm_request(messages, schema=EvaluationSummary)
    print(f"评估去噪后草稿: {result}")
    search_queries = [re.search_query for re in result.queries]
    if not search_queries or state['cur_search_depth'] > state['max_search_depth']:
        return Command(
            update={"draft": draft},
            goto="final_answer"
        )
    else:
        return Command(
            update={"sub_queries": search_queries, "overall_evaluation": result.overall_evaluation},
            goto="generate_sub_gaps_query"
        )

async def final_answer(state: State):
    """
    生成最终答案
    :param state:
    :return:
    """
    draft = state['draft']
    query = state['query']
    research_plan = state['research_plan']
    prompt = final_answer_prompt.format(topic=query, draft=draft, research_plan=research_plan, time=get_china_time())
    messages = [{"role": "user", "content": prompt}]
    _, result = await llm_request(messages)
    return {"final_report": result}

builder = StateGraph(State)
builder.add_node("generate_report_plan", generate_report_plan)
builder.add_node("generate_draft_content", generate_draft_content)
builder.add_node("generate_sub_gaps_query", generate_sub_gaps_query)
builder.add_node("draft_denoising", draft_denoising)
builder.add_node("need_draft_denoising", need_draft_denoising)
builder.add_node("final_answer", final_answer)

builder.add_edge(START, "generate_report_plan")
builder.add_edge("generate_report_plan", "generate_draft_content")
builder.add_edge("generate_draft_content", "generate_sub_gaps_query")
builder.add_edge("generate_sub_gaps_query", "draft_denoising")
builder.add_edge("draft_denoising", "need_draft_denoising")
