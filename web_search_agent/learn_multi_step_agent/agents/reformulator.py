# Shamelessly stolen from Microsoft Autogen team: thanks to them for this great resource!
# https://github.com/microsoft/autogen/blob/gaia_multiagent_v01_march_1st/autogen/browser_utils.py
import copy

from web_search_agent.learn_multi_step_agent.llm.openai_llm import MessageRole, OpenAILLM


async def prepare_response(original_task: str, inner_messages) -> str:
    messages = [
        {
            "role": MessageRole.SYSTEM,
            "content": f"""Earlier you were asked the following:{original_task}
            Your team then worked diligently to address that request. Read below a transcript of that conversation:"""
            ,
        }
    ]

    for message in inner_messages:
        if not message.get("content"):
            continue

        messages.append({
            'role': MessageRole.USER,
            'content': message["content"],
        })

    # ask for the final answer
    messages.append(
        {
            "role": MessageRole.USER,
            "content": [
                {
                    "type": "text",
                    "text": f"""
                Read the above conversation and output a FINAL ANSWER to the question. The question is repeated here for convenience:

                {original_task}

                FINAL ANSWER FORMAT: Your response must strictly follow these formatting rules:
                - For NUMBERS: Use digits only (not words), omit commas and units (no $, USD, %, etc.) unless specifically requested
                - For TEXT: Omit articles and abbreviations unless specified, exclude final punctuation (.!?)
                - For LISTS: Provide comma-separated values following the above number/text rules
                - Follow ALL formatting instructions in the original question (alphabetization, sequencing, decimal places, etc.)
                - Please carefully understand the requirements of the original task and ensure that the final output meets the specific units given in the question (/Angstrom,/thousand hours, etc.)
                - If you cannot determine an answer, respond only with: "Unable to determine"
                - Your entire response should consist of ONLY the requested information in the EXACT format specified - nothing more, nothing less.
                """,
                }
            ],
        }
    )
    llm = OpenAILLM()
    response = await llm.generate(messages, tool_choice=None)

    final_answer = response.content.split("FINAL ANSWER: ")[-1].strip()
    print("> Reformulated answer: ", final_answer)

    return final_answer
