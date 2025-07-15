import asyncio
import json
import os
from pathlib import Path
from typing import List

import datasets
import pandas as pd
from datasets import load_dataset
from huggingface_hub import login, snapshot_download

from web_search_agent.learn_multi_step_agent.agents.reformulator import prepare_response
from web_search_agent.learn_multi_step_agent.agents.tool_call_agent import ToolCallingAgent

# login('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')

def load_gaia_dataset(args):
    split = args['split']
    cache_dir = os.path.join("data", "gaia", split)
    os.makedirs(cache_dir, exist_ok=True)

    cached_file = os.path.join(cache_dir, "cached_dataset.parquet")
    if os.path.exists(cached_file):
        eval_df = pd.read_parquet(cached_file)
        return eval_df

    # 下载并重命名列
    eval_ds = load_dataset("gaia-benchmark/GAIA", "2023_all", trust_remote_code=True, split=split)
    eval_ds = eval_ds.rename_columns({"Question": "question", "Final answer": "true_answer", "Level": "task"})

    # 路径处理
    def preprocess_file_paths(row):
        if len(row.get("file_name", "")) > 0:
            row["file_name"] = os.path.join("data", "gaia", split, row["file_name"])
        return row

    eval_ds = eval_ds.map(preprocess_file_paths)
    eval_df = pd.DataFrame(eval_ds)

    # 缓存数据
    eval_df.to_parquet(cached_file, index=False)
    return eval_df


def get_examples_to_answer(answers_file, eval_df, selected_tasks=None, level='all', debug=False) -> List[dict]:
    print(f"Loading answers from {answers_file}...")
    try:
        answer_df = pd.read_json(answers_file, lines=True)
        done_questions = answer_df.get("task_id", []).tolist()
        print(f"Found {len(done_questions)} previous results!")
    except Exception as e:
        print("Error when loading records: ", e)
        print("No usable records! ▶️ Starting new.")
        done_questions = []

    if level == 'all':
        filtered_df = eval_df
    else:
        filtered_df = eval_df[eval_df['task'] == level]

    if selected_tasks:
        if isinstance(selected_tasks[0], int):
            filtered_df = eval_df.iloc[selected_tasks]
        else:
            filtered_df = eval_df[eval_df['task_id'].isin(selected_tasks)]

    if debug:
        done_questions = []
    return [row.to_dict() for idx, row in filtered_df.iterrows() if row["task_id"] not in done_questions]

async def answer_single_question(example, answers_file):
    augmented_question = """You have one question to answer. It is paramount that you provide a correct answer.
    Give it all you can: I know for a fact that you have access to all the relevant tools to solve it and find the correct answer (the answer does exist). 
    Failure or 'I cannot answer' or 'None found' will not be tolerated, success will be rewarded.
    Run verification steps if that's needed, you must make sure you find the correct answer!
    Here is the task:
    """ + example["question"]

    agent = ToolCallingAgent()
    await agent.run(augmented_question)
    agent_memory = agent.write_memory_to_messages(summary_mode=True)
    final_result = await prepare_response(augmented_question, agent_memory)
    tool_message = [me for me in agent_memory if me['role'] == 'tool']
    annotated_example = {
        "task_id": example["task_id"],
        "question": example["question"],
        "true_answer": example["true_answer"],
        "answer": final_result,
        "task": example["task"],
        "file_name": example["file_name"],
        'len_steps': len(tool_message),
        'tool': tool_message

    }
    print(f"question: {example['question']} final_result:{final_result} ture_answer:{example["true_answer"]}")
    append_answer(annotated_example, answers_file)

def append_answer(entry: dict, jsonl_file: str) -> None:
    jsonl_path = Path(jsonl_file)
    jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    with open(jsonl_file, "a", encoding="utf-8") as fp:
        fp.write(json.dumps(entry) + "\n")
    assert jsonl_path.exists(), "File not found!"
    print("Answer exported to file:", jsonl_path.resolve())

if __name__ == "__main__":
    args = {
        "split": "validation",
        "level": "1",
        'run_name': "init_run"
    }
    eval_df = load_gaia_dataset(args)
    answers_file = f"D:\\python\\my_deep_research\\web_search_agent\\learn_multi_step_agent\\results\\output\\{args['split']}\\{args['run_name']}.jsonl"

    tasks_to_run = get_examples_to_answer(answers_file, eval_df, level=args['level'])
    for example in tasks_to_run[0:1]:
        print(f"【GAIA】执行任务: {example['question']}")
        asyncio.run(answer_single_question(example, answers_file))
