import os
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI

from typing import Dict, List, Optional, Union

from openai.types.chat import ChatCompletionMessage, ChatCompletion
from pydantic import BaseModel

from web_search_agent.schema import (
    ROLE_VALUES,
    TOOL_CHOICE_TYPE,
    TOOL_CHOICE_VALUES,
    Message,
    ToolChoice,
)

project_root = Path(__file__).resolve().parent.parent
env_path = project_root / 'config' / '.env'

load_dotenv(dotenv_path=env_path)

class LLM(BaseModel):

    client: AsyncOpenAI
    model: str

    model_config = {
        "arbitrary_types_allowed": True
    }

    def __init__(self):
        client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"),base_url=os.getenv("OPENAI_API_BASE"))
        super().__init__(client=client, model="360/aliyun-qwen3-235b-a22b")

    async def ask(self, messages: List[Union[dict, Message]]):

        messages = self.format_messages(messages, False)

        params = {
            "model": self.model,
            "messages": messages,
        }

        response = await self.client.chat.completions.create(
            **params, stream=False
        )

        if not response.choices or not response.choices[0].message.content:
            raise ValueError("Empty or invalid response from LLM")

        return response.choices[0].message.content

    async def ask_tool(
            self,
            messages: List[Union[dict, Message]],
            system_msgs: Optional[List[Union[dict, Message]]] = None,
            timeout: int = 300,
            tools: Optional[List[dict]] = None,
            tool_choice: TOOL_CHOICE_TYPE = ToolChoice.AUTO,  # type: ignore
            temperature: Optional[float] = None,
            **kwargs,
    ) -> ChatCompletionMessage | None:

        if system_msgs:
            system_msgs = self.format_messages(system_msgs, False)
            messages = system_msgs + self.format_messages(messages, False)
        else:
            messages = self.format_messages(messages, False)

        params = {
            "model": self.model,
            "messages": messages,
            "tools": tools,
            "tool_choice": tool_choice,
            "timeout": timeout,
            **kwargs,
        }
        response: ChatCompletion = await self.client.chat.completions.create(
            **params
        )

        # Check if response is valid
        if not response.choices or not response.choices[0].message:
            print(response)
            # raise ValueError("Invalid or empty response from LLM")
            return None
        return response.choices[0].message

    @staticmethod
    def format_messages(
            messages: List[Union[dict, Message]], supports_images: bool = False
    ) -> List[dict]:
        """
        Format messages for LLM by converting them to OpenAI message format.

        Args:
            messages: List of messages that can be either dict or Message objects
            supports_images: Flag indicating if the target model supports image inputs

        Returns:
            List[dict]: List of formatted messages in OpenAI format

        Raises:
            ValueError: If messages are invalid or missing required fields
            TypeError: If unsupported message types are provided

        Examples:
            >>> msgs = [
            ...     Message.system_message("You are a helpful assistant"),
            ...     {"role": "user", "content": "Hello"},
            ...     Message.user_message("How are you?")
            ... ]
            >>> formatted = LLM.format_messages(msgs)
        """
        formatted_messages = []

        for message in messages:
            # Convert Message objects to dictionaries
            if isinstance(message, Message):
                message = message.to_dict()

            if isinstance(message, dict):
                # If message is a dict, ensure it has required fields
                if "role" not in message:
                    raise ValueError("Message dict must contain 'role' field")

                # Process base64 images if present and model supports images
                if supports_images and message.get("base64_image"):
                    # Initialize or convert content to appropriate format
                    if not message.get("content"):
                        message["content"] = []
                    elif isinstance(message["content"], str):
                        message["content"] = [
                            {"type": "text", "text": message["content"]}
                        ]
                    elif isinstance(message["content"], list):
                        # Convert string items to proper text objects
                        message["content"] = [
                            (
                                {"type": "text", "text": item}
                                if isinstance(item, str)
                                else item
                            )
                            for item in message["content"]
                        ]

                    # Add the image to content
                    message["content"].append(
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{message['base64_image']}"
                            },
                        }
                    )

                    # Remove the base64_image field
                    del message["base64_image"]
                # If model doesn't support images but message has base64_image, handle gracefully
                elif not supports_images and message.get("base64_image"):
                    # Just remove the base64_image field and keep the text content
                    del message["base64_image"]

                if "content" in message or "tool_calls" in message:
                    formatted_messages.append(message)
                # else: do not include the message
            else:
                raise TypeError(f"Unsupported message type: {type(message)}")

        # Validate all messages have required fields
        for msg in formatted_messages:
            if msg["role"] not in ROLE_VALUES:
                raise ValueError(f"Invalid role: {msg['role']}")

        return formatted_messages