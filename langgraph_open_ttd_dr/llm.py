from openai import OpenAI, AsyncOpenAI
from dotenv import load_dotenv
from typing import Any, Union, Optional, Dict, Tuple, Type
from pydantic import BaseModel
import json

from langchain_core.utils.function_calling import convert_to_openai_tool

load_dotenv()
client = AsyncOpenAI()


async def llm_request(
    messages: list,
    schema: Optional[Union[Dict, Type[BaseModel]]] = None,
    include_raw: bool = False,
    stream: bool = True,
    model: str = "volcengine/doubao-seed-1-6-250615-disable-thinking"
):
    """
    通用 LLM 请求逻辑：
    - 支持结构化 tool-calling 输出（schema）
    - 支持流式推理过程与回答输出（stream=True）
    - 支持 include_raw 显示原始内容
    """

    if schema:
        # 判断 schema 类型
        if isinstance(schema, type) and issubclass(schema, BaseModel):
            tool = convert_to_openai_tool(schema)
            is_pydantic = True
        elif isinstance(schema, dict):
            tool = schema
            is_pydantic = False
        else:
            raise ValueError("Schema 必须是 Pydantic 类或 dict 格式")

        completion = await client.chat.completions.create(
            model=model,
            messages=messages,
            tools=[tool],
            tool_choice={"type": "function", "function": {"name": tool["function"]["name"]}},
            extra_body={"enable_thinking": True, "thinking_budget": 50},
            stream=stream,
            timeout=3600
        )
        parsed_args = {}
        if not stream:
            message = completion.choices[0].message
            if message.tool_calls:
                arguments_str = message.tool_calls[0].function.arguments
                parsed_args = json.loads(arguments_str)
        else:
            try:
                tool_args_buffer: str = ""
                async for chunk in completion:
                    for choice in chunk.choices:
                        if choice.delta.tool_calls:
                            for tc in choice.delta.tool_calls:
                                if tc.index == 0:  # 只处理第一条 tool 调用
                                    tool_args_buffer += tc.function.arguments or ""

                parsed_args = json.loads(tool_args_buffer)
            except Exception as e:
                pass

        if include_raw:
            return "", parsed_args
        if is_pydantic:
            return "", schema(**parsed_args)
        return "", parsed_args

    completion = await client.chat.completions.create(
        model=model,
        messages=messages,
        extra_body={"enable_thinking": True, "thinking_budget": 50},
        stream=stream,
    )

    if stream:
        reasoning_content = ""
        answer_content = ""
        is_answering = False

        print("\n" + "=" * 20 + "思考过程" + "=" * 20 + "\n")
        async for chunk in completion:
            if not chunk.choices:
                print("\nUsage:")
                print(chunk.usage)
                continue

            delta = chunk.choices[0].delta

            if hasattr(delta, "reasoning_content") and delta.reasoning_content is not None:
                if not is_answering:
                    print(delta.reasoning_content, end="", flush=True)
                reasoning_content += delta.reasoning_content

            if hasattr(delta, "content") and delta.content:
                if not is_answering:
                    print("\n" + "=" * 20 + "完整回复" + "=" * 20 + "\n")
                    is_answering = True
                print(delta.content, end="", flush=True)
                answer_content += delta.content

        return reasoning_content, answer_content

    else:
        content = completion.choices[0].message.content
        return "", content


async def main():
    from pydantic import BaseModel

    class AnswerWithJustification(BaseModel):
        answer: str
        justification: str

    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What weighs more, a pound of bricks or a pound of feathers?"},
    ]

    # ✅ 示例 1：结构化输出（非流式）
    _, result = await llm_request(messages, schema=AnswerWithJustification, stream=False)
    print("\n" + "=" * 20 + "结构化输出" + "=" * 20)
    print(result)

    # ✅ 示例 2：原始思考过程+回答输出（流式）
    # reasoning, answer = await llm_request(messages, stream=True, model="360/aliyun-qwen3-235b-a22b-250729")
    # print("\n\n[完整思考过程]", reasoning)
    # print("\n[最终回复]", answer)

    # ✅ 示例 3：普通非流式输出（无 schema）
    # _, plain_answer = await llm_request(messages, stream=False)
    # print("\n[非结构化回复]", plain_answer)


if __name__ == "__main__":
    main()
