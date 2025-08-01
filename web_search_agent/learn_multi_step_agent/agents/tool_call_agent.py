import json
from abc import abstractmethod

from web_search_agent.learn_multi_step_agent.agents.react_agent import ReactAgent
from web_search_agent.learn_multi_step_agent.llm.openai_llm import ChatMessage
from web_search_agent.learn_multi_step_agent.memory.memory import ActionStep, ToolCall
from web_search_agent.learn_multi_step_agent.prompts.prompt import TOOLCALLPROMPT, TOOLCALLPROMPT_EN
from web_search_agent.learn_multi_step_agent.tools.final_answer import FinalAnswerTool
from web_search_agent.learn_multi_step_agent.tools.google_search_serpapi import GoogleSearchTool
from web_search_agent.learn_multi_step_agent.tools.search_360 import Search360Tool
from web_search_agent.learn_multi_step_agent.tools.tool_collection import ToolCollection
from web_search_agent.tools.create_chat_completion import CreateChatCompletion
from web_search_agent.tools.terminate import Terminate
from web_search_agent.tools.web_search import WebSearch


class ToolCallingAgent(ReactAgent):

    def __init__(self):
        # self.system_prompt = TOOLCALLPROMPT
        self.system_prompt = TOOLCALLPROMPT_EN
        self.available_tools: ToolCollection = ToolCollection(
            Search360Tool(), Terminate(), FinalAnswerTool()
        )
        super().__init__()

    def initialize_system_prompt(self):
        self.system_prompt.format(
            tools = self.available_tools.to_model_context()
        )
        return self.system_prompt

    async def think(self, memory_step: ActionStep):
        # 加载之前轮记忆
        memory_messages = self.write_memory_to_messages()

        input_messages = memory_messages.copy()

        memory_step.model_input_messages = input_messages

        chat_message: ChatMessage = await self.model.generate(
            input_messages,
            tools=self.available_tools.to_params(),
            tool_choice='required'
        )
        print(
            f"tool_call 步骤：{memory_step.step_number}, 结果：{chat_message.content}")

        if not chat_message.tool_calls:
            return False

        memory_step.model_output_message = chat_message
        tools = []
        for tool_call in chat_message.tool_calls[:1]:
            tool_name = tool_call.function.name
            tool_arguments = tool_call.function.arguments
            tools.append(ToolCall(name=tool_name, arguments=tool_arguments, id=tool_call.id))
        memory_step.tool_calls = tools

        return True

    @abstractmethod
    async def merge_args(self, command):
        pass

    async def act(self, memory_step: ActionStep):
        if not memory_step.tool_calls:
            # Return last message content if no tool calls
            return self.memory.get_full_steps()[-1].content or "No content or commands to execute"

        results = []
        for command in memory_step.tool_calls:
            name = command.name
            if name not in self.available_tools.tool_map:
                return f"Error: Unknown tool '{name}'"



            args = json.loads(command.arguments or "{}")
            print(f"🔧 Activating tool: '{name}'... args: {args}")
            result = await self.available_tools.execute(name=name, tool_input=args)

            if name in ['terminate', 'final_answer']:
                self.is_finsh = True
            observation = (
                f"Observed output of cmd `{name}` executed:\n{str(result)}"
                if result
                else f"Cmd `{name}` completed with no output"
            )
            print(observation)
            results.append(observation)

        memory_step.observations = "\n\n".join(results)

        return "\n\n".join(results)
