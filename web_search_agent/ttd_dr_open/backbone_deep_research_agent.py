import json

from web_search_agent.learn_multi_step_agent.agents.react_agent import ReactAgent
from web_search_agent.learn_multi_step_agent.agents.tool_call_agent import ToolCallingAgent
from web_search_agent.learn_multi_step_agent.llm.openai_llm import ChatMessage
from web_search_agent.learn_multi_step_agent.memory.memory import ActionStep, ToolCall
from web_search_agent.learn_multi_step_agent.prompts.prompt import TOOLCALLPROMPT, TOOLCALLPROMPT_EN, BackbonePROMPT_EN
from web_search_agent.learn_multi_step_agent.tools.final_answer import FinalAnswerTool
from web_search_agent.learn_multi_step_agent.tools.google_search_serpapi import GoogleSearchTool
from web_search_agent.learn_multi_step_agent.tools.search_360 import Search360Tool
from web_search_agent.learn_multi_step_agent.tools.tool_collection import ToolCollection
from web_search_agent.learn_multi_step_agent.utils.time import get_china_time
from web_search_agent.ttd_dr_open.tools.denoising_draft_tool import DenoiseAndReviseDraftTool
from web_search_agent.ttd_dr_open.tools.draft_generation_tool import ResearchDraftGeneratorTool
from web_search_agent.ttd_dr_open.tools.gen_search_keywords import GapsQuerySaverTool
from web_search_agent.ttd_dr_open.tools.research_plan_tool import ResearchPlanSaverTool


class BackboneDeepResearchAgent(ToolCallingAgent):

    def __init__(self):
        super().__init__()
        self.system_prompt = BackbonePROMPT_EN
        self.available_tools: ToolCollection = ToolCollection(
            ResearchPlanSaverTool(), FinalAnswerTool(), DenoiseAndReviseDraftTool(),
            GapsQuerySaverTool(), ResearchDraftGeneratorTool()
        )



    def initialize_system_prompt(self):
        prompt = BackbonePROMPT_EN
        prompt = prompt.format(
            tools=self.available_tools.to_model_context(),
            time=get_china_time()
        )
        print(f'当前系统提示词: {prompt}')
        return prompt

    async def merge_args(self, command: ToolCall):
        pass

