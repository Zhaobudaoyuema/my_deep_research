from abc import ABC, abstractmethod

from openai import BaseModel
from pydantic import Field

from web_search_agent.learn_multi_step_agent.llm.openai_llm import ChatMessage, OpenAILLM
from web_search_agent.learn_multi_step_agent.memory.memory import ActionStep, AgentMemory, TaskStep


class MultiStepAgent(ABC):

    def __init__(self):
        self.max_steps: int = 10

        self.step_number: int = 1

        self.memory = AgentMemory(self.format_system_prompt)

        self.model = OpenAILLM()

        self.is_finsh: bool = False

    @property
    def format_system_prompt(self) -> str:
        return self.initialize_system_prompt()

    @abstractmethod
    def initialize_system_prompt(self):
        ...

    @abstractmethod
    async def step(self, memory_step: ActionStep):
        ...

    async def run(self, task):
        try:
            self.memory.steps.append(TaskStep(task=task))
            while self.step_number <= self.max_steps and not self.is_finsh:
                action_step = ActionStep(
                    step_number=self.step_number,
                )
                await self.step(action_step)

                self.step_number += 1
                self.memory.steps.append(action_step)
        except Exception as e:
            print(e)

    def write_memory_to_messages(
        self,
        summary_mode: bool = False,
    ) -> list:
        """
        Reads past llm_outputs, actions, and observations or errors from the memory into a series of messages
        that can be used as input to the LLM. Adds a number of keywords (such as PLAN, error, etc) to help
        the LLM.
        """
        messages = self.memory.system_prompt.to_messages(summary_mode=summary_mode)
        for memory_step in self.memory.steps:
            messages.extend(memory_step.to_messages(summary_mode=summary_mode))
        return messages