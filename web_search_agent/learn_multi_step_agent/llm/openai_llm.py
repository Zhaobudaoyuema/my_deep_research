import json
import os
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI

from typing import Dict, List, Optional, Union, Any

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL_CALL = "tool"
    TOOL_RESPONSE = "tool"

    @classmethod
    def roles(cls):
        return [r.value for r in cls]

@dataclass
class ChatMessageToolCallFunction:
    arguments: Any
    name: str
    description: str | None = None


@dataclass
class ChatMessageToolCall:
    function: ChatMessageToolCallFunction
    id: str
    type: str

    def __str__(self) -> str:
        return f"Call: {self.id}: Calling {str(self.function.name)} with arguments: {str(self.function.arguments)}"


def get_dict_from_nested_dataclasses(obj, ignore_key=None):
    def convert(obj):
        if hasattr(obj, "__dataclass_fields__"):
            return {k: convert(v) for k, v in asdict(obj).items() if k != ignore_key}
        return obj

    return convert(obj)


@dataclass
class ChatMessage:
    role: str
    content: str | list[dict[str, Any]] | None = None
    tool_calls: Optional[List[ChatMessageToolCall]] | list[dict] = None
    raw: Any | None = None

    def model_dump_json(self):
        return json.dumps(get_dict_from_nested_dataclasses(self, ignore_key="raw"))

    @classmethod
    def from_dict(cls, data: dict, raw: Any | None = None) -> "ChatMessage":
        if data.get("tool_calls"):
            tool_calls = [
                ChatMessageToolCall(
                    function=ChatMessageToolCallFunction(**tc["function"]), id=tc["id"], type=tc["type"]
                )
                for tc in data["tool_calls"]
            ]
            data["tool_calls"] = tool_calls
        return cls(
            role=data["role"],
            content=data.get("content"),
            tool_calls=data.get("tool_calls"),
            raw=raw,
        )

    def to_model_dict(self):
        return get_dict_from_nested_dataclasses(self, ignore_key="raw")

    def render_as_markdown(self) -> str:
        rendered = str(self.content) or ""
        if self.tool_calls:
            rendered += "\n".join(
                [
                    json.dumps({"tool": tool.function.name, "arguments": tool.function.arguments})
                    for tool in self.tool_calls
                ]
            )
        return rendered
project_root = Path(__file__).resolve().parent.parent
env_path = project_root / 'config' / '.env'

load_dotenv(dotenv_path=env_path)

class OpenAILLM:
    client: AsyncOpenAI
    model: str

    def __init__(self, model_name: str = '360/aliyun-qwen3-235b-a22b'):
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"),
                                  base_url=os.getenv("OPENAI_API_BASE"))
        self.model = model_name

    async def generate(self,
                       messages: list,
                       tools: Optional[List[dict]] = None,
                       tool_choice: str | dict | None = "required", ):
        params = {
            "model": self.model,
            "messages": messages,
            "tools": tools,
            "tool_choice": tool_choice,
        }

        response = await self.client.chat.completions.create(**params)

        return ChatMessage.from_dict(
            response.choices[0].message.model_dump(include={"role", "content", "tool_calls"}),
            raw=response,
        )
