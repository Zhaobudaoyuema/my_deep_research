from dataclasses import dataclass, asdict
from typing import Any

from web_search_agent.learn_multi_step_agent.llm.openai_llm import ChatMessage, MessageRole, ChatMessageToolCall, \
    ChatMessageToolCallFunction
from web_search_agent.learn_multi_step_agent.utils.smolagents_utils import make_json_serializable, AgentError


@dataclass
class ToolCall:
    name: str
    arguments: Any
    id: str

    def dict(self):
        return {
            "id": self.id,
            "type": "function",
            "function": {
                "name": self.name,
                "arguments": make_json_serializable(self.arguments),
            },
        }

    def dict_chat(self):
        return {
            "id": self.id,
            "type": "function",
            "function": {
                "name": self.name,
                "arguments": self.arguments,
            },
        }


@dataclass
class MemoryStep:
    def dict(self):
        return asdict(self)

    def to_messages(self, summary_mode: bool = False) -> list[ChatMessage]:
        raise NotImplementedError


@dataclass
class ActionStep(MemoryStep):
    step_number: int
    model_input_messages: list[ChatMessage] | None = None  # 当前步骤输出给模型的全部数据
    tool_calls: list[ToolCall] | None = None
    error: AgentError | None = None
    model_output_message: ChatMessage | None = None  # 当前步骤模型的完整输出
    model_output: str | None = None  # 模型输出的文本内容
    observations: str | None = None  # 观察到的工具结果

    def dict(self):
        # We overwrite the method to parse the tool_calls and action_output manually
        return {
            "step_number": self.step_number,
            "model_input_messages": self.model_input_messages,
            "tool_calls": [tc.dict() for tc in self.tool_calls] if self.tool_calls else [],
            "error": self.error.dict() if self.error else None,
            "model_output_message": self.model_output_message.dict() if self.model_output_message else None,
            "model_output": self.model_output,
            "observations": self.observations,
        }

    def to_messages(self, summary_mode: bool = False) -> list[ChatMessage]:
        messages = []
        if self.model_output is not None and not summary_mode:
            messages.append({'role': MessageRole.ASSISTANT, 'content': self.model_output.strip()})

        if self.tool_calls is not None:
            messages.append({'role': MessageRole.ASSISTANT,
                             'content': f"Calling tools:\n {str([tc.dict() for tc in self.tool_calls])}",
                             'tool_calls': [tc.dict_chat() for tc in self.tool_calls]})

        if self.observations is not None:
            messages.append({'role': MessageRole.TOOL_RESPONSE,
                             'content': f"Observation:\n{self.observations}",
                             'tool_call_id': self.tool_calls[0].id})

        if self.error is not None:
            error_message = (
                    "Error:\n"
                    + str(self.error)
                    + "\nNow let's retry: take care not to repeat previous errors! If you have retried several times, try a completely different approach.\n"
            )
            message_content = f"Call id: {self.tool_calls[0].id}\n" if self.tool_calls else ""
            message_content += error_message
            messages.append({'role': MessageRole.TOOL_RESPONSE,
                                 'content': f"Observation:\n{message_content}",
                                 'tool_call_id': self.tool_calls[0].id}
            )

        return messages


@dataclass
class PlanningStep(MemoryStep):
    model_input_messages: list[ChatMessage]
    model_output_message: ChatMessage
    plan: str

    def to_messages(self, summary_mode: bool = False) -> list:
        if summary_mode:
            return []
        return [
            {'role': MessageRole.ASSISTANT, 'content': self.plan.strip()},
            {'role': MessageRole.USER, 'content': 'Now proceed and carry out this plan.'},
            # This second message creates a role change to prevent models models from simply continuing the plan message
        ]


@dataclass
class TaskStep(MemoryStep):
    task: str

    def to_messages(self, summary_mode: bool = False) -> list:

        return [{'role': MessageRole.USER, 'content': f"New task:\n{self.task}"}]


@dataclass
class SystemPromptStep(MemoryStep):
    system_prompt: str

    def to_messages(self, summary_mode: bool = False) -> list:
        if summary_mode:
            return []
        return [{'role': MessageRole.SYSTEM, 'content': self.system_prompt if self.system_prompt else ''}]


@dataclass
class FinalAnswerStep(MemoryStep):
    output: Any


class AgentMemory:
    def __init__(self, system_prompt: str):
        self.system_prompt: SystemPromptStep = SystemPromptStep(system_prompt=system_prompt)
        self.steps: list[TaskStep | ActionStep | PlanningStep] = []

    def reset(self):
        """Reset the agent's memory, clearing all steps and keeping the system prompt."""
        self.steps = []

    def get_succinct_steps(self) -> list[dict]:
        """Return a succinct representation of the agent's steps, excluding model input messages."""
        return [
            {key: value for key, value in step.dict().items() if key != "model_input_messages"} for step in
            self.steps
        ]

    def get_full_steps(self) -> list[dict]:
        """Return a full representation of the agent's steps, including model input messages."""
        if len(self.steps) == 0:
            return []
        return [step.dict() for step in self.steps]


__all__ = ["AgentMemory"]
