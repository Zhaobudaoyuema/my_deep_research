from abc import ABC, abstractmethod

from pydantic import Field

from web_search_agent.learn_multi_step_agent.agents.multi_step_agent import MultiStepAgent
from web_search_agent.learn_multi_step_agent.memory.memory import ActionStep


class ReactAgent(MultiStepAgent, ABC):

    @abstractmethod
    async def think(self, memory_step: ActionStep):
        ...

    @abstractmethod
    async def act(self, memory_step: ActionStep):
        ...

    async def step(self, memory_step: ActionStep):
        is_act = await self.think(memory_step)
        if is_act:
            await self.act(memory_step)
        else:
            print(f"步骤：{self.step_number} 模型没有生成工具调用，结束执行")
            self.is_finsh = True